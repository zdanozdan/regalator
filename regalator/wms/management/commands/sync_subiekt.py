from django.core.management.base import BaseCommand
from django.utils import timezone
from wms.models import Product, ProductGroup
from subiekt.models import tw_Towar
from decimal import Decimal


class Command(BaseCommand):
    help = 'Synchronizuje produkty z Subiektem'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Wymuś synchronizację wszystkich produktów',
        )
        parser.add_argument(
            '--product-id',
            '--product_id',
            type=int,
            help='Synchronizuj tylko konkretny produkt z Subiektu (podaj tw_Id)',
        )
        parser.add_argument(
            '--drop-unused',
            action='store_true',
            help='Usuń nieużywane produkty (bez stanów, zamówień, itp.)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Pokaż tylko listę produktów do usunięcia bez ich usuwania',
        )

    def handle(self, *args, **options):
        if options['drop_unused']:
            self.drop_unused_products(options['dry_run'])
            return
            
        self.stdout.write('Rozpoczynam synchronizację z Subiektem...')
        
        if options['product_id']:
            # Synchronizuj tylko konkretny produkt z Subiektu
            try:
                subiekt_product = tw_Towar.subiekt_objects.get_product_by_id(options['product_id'])
                if subiekt_product:
                    # Wyświetl informacje o produkcie przed synchronizacją
                    self.display_product_info(subiekt_product)
                    
                    # Pytaj o potwierdzenie
                    confirm = input('\nCzy chcesz kontynuować synchronizację? (y/N): ')
                    if confirm.lower() in ['y', 'yes', 'tak']:
                        self.sync_product_from_subiekt(subiekt_product)
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Zsynchronizowano produkt: {subiekt_product.tw_Nazwa}')
                        )
                    else:
                        self.stdout.write('Synchronizacja anulowana.')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Produkt o ID {options["product_id"]} nie istnieje w Subiekcie')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Błąd podczas synchronizacji: {str(e)}')
                )
        else:
            # Synchronizuj wszystkie produkty z Subiektu
            try:
                subiekt_products = tw_Towar.subiekt_objects.get_products_with_stock(limit=0)  # 0 = wszystkie produkty
                
                synced_count = 0
                for subiekt_product in subiekt_products:
                    self.sync_product_from_subiekt(subiekt_product)
                    synced_count += 1
                    self.stdout.write(f'✓ {subiekt_product.tw_Nazwa}')
                
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Zsynchronizowano {synced_count} produktów z Subiektu')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Błąd podczas synchronizacji: {str(e)}')
                )
    
    def sync_product_from_subiekt(self, subiekt_product):
        """Synchronizuje produkt z Subiektu do WMS"""
        # Mapowanie pól zgodnie z wymaganiami:
        # code = tw_Symbol
        # name = tw_Nazwa  
        # description = tw_Opis
        # subiekt_id = tw_Id
        # subiekt_stock = st_Stan
        # subiekt_stock_reserved = st_StanRez
        
        # Sprawdź czy produkt już istnieje w WMS
        wms_product, created = Product.objects.get_or_create(
            subiekt_id=subiekt_product.tw_Id,
            defaults={
                'code': subiekt_product.tw_Symbol,
                'name': subiekt_product.tw_Nazwa,
                'description': subiekt_product.tw_Opis or '',
                'barcode': subiekt_product.tw_Id,  # Używamy symbolu jako kod kreskowy
                'unit': 'szt',  # Domyślna jednostka
            }
        )
        
        if not created:
            # Aktualizuj istniejący produkt
            wms_product.code = subiekt_product.tw_Symbol
            wms_product.name = subiekt_product.tw_Nazwa
            wms_product.description = subiekt_product.tw_Opis or ''
            wms_product.barcode = subiekt_product.tw_Id
        
        # Aktualizuj dane z Subiektu
        wms_product.subiekt_stock = Decimal(str(getattr(subiekt_product, 'st_Stan', 0)))
        wms_product.subiekt_stock_reserved = Decimal(str(getattr(subiekt_product, 'st_StanRez', 0)))
        wms_product.last_sync_date = timezone.now()
        
        # Obsługa grupy produktów
        subiekt_group = getattr(subiekt_product, 'grt_Nazwa', '')
        if subiekt_group:
            wms_group, group_created = ProductGroup.objects.get_or_create(
                name=subiekt_group,
                defaults={
                    'code': subiekt_group[:20],  # Używamy nazwy jako kodu (max 20 znaków)
                    'description': f'Grupa z Subiektu: {subiekt_group}',
                    'color': '#007bff',  # Domyślny kolor
                }
            )
            
            # Dodaj produkt do grupy (jeśli nie jest już w tej grupie)
            if wms_group not in wms_product.groups.all():
                wms_product.groups.add(wms_group)
                if group_created:
                    self.stdout.write(f'  → Utworzono nową grupę: {wms_group.name}')
                else:
                    self.stdout.write(f'  → Dodano do grupy: {wms_group.name}')
        
        print(f'wms_product: {wms_product.name}')
        print(f'wms_product.barcode: {wms_product.barcode}')
        barcodes = Product.objects.filter(barcode=wms_product.barcode)
        print(f'barcodes: {barcodes}')
        wms_product.save()
        
        if created:
            self.stdout.write(f'  → Utworzono nowy produkt: {wms_product.name}')
        else:
            self.stdout.write(f'  → Zaktualizowano produkt: {wms_product.name}')
    
    def display_product_info(self, subiekt_product):
        """Wyświetla informacje o produkcie z Subiektu"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('INFORMACJE O PRODUKCIE Z SUBIEKTU'))
        self.stdout.write('='*60)
        self.stdout.write(f'ID (tw_Id): {subiekt_product.tw_Id}')
        self.stdout.write(f'Symbol (tw_Symbol): {subiekt_product.tw_Symbol}')
        self.stdout.write(f'Nazwa (tw_Nazwa): {subiekt_product.tw_Nazwa}')
        self.stdout.write(f'Opis (tw_Opis): {subiekt_product.tw_Opis or "Brak opisu"}')
        self.stdout.write(f'Stan magazynowy (st_Stan): {getattr(subiekt_product, "st_Stan", 0)}')
        self.stdout.write(f'Stan zarezerwowany (st_StanRez): {getattr(subiekt_product, "st_StanRez", 0)}')
        self.stdout.write(f'Grupa (grt_Nazwa): {getattr(subiekt_product, "grt_Nazwa", "") or "Brak grupy"}')
        self.stdout.write('='*60)
        
        # Sprawdź czy produkt już istnieje w WMS
        try:
            existing_product = Product.objects.get(subiekt_id=subiekt_product.tw_Id)
            self.stdout.write(self.style.WARNING('\nPRODUKT JUŻ ISTNIEJE W WMS:'))
            self.stdout.write(f'  WMS ID: {existing_product.id}')
            self.stdout.write(f'  WMS Nazwa: {existing_product.name}')
            self.stdout.write(f'  WMS Kod: {existing_product.code}')
            self.stdout.write(f'  WMS Stan: {existing_product.subiekt_stock}')
            self.stdout.write(f'  WMS Stan zarezerwowany: {existing_product.subiekt_stock_reserved}')
            self.stdout.write(f'  Ostatnia synchronizacja: {existing_product.last_sync_date}')
        except Product.DoesNotExist:
            self.stdout.write(self.style.SUCCESS('\nPRODUKT NIE ISTNIEJE W WMS - ZOSTANIE UTWORZONY'))
        
        self.stdout.write('='*60)
    
    def drop_unused_products(self, dry_run=False):
        """Usuwa nieużywane produkty z systemu WMS"""
        from wms.models import (
            Stock, OrderItem, PickingItem, SupplierOrderItem, 
            ReceivingItem, PickingHistory, ReceivingHistory, DocumentItem
        )
        
        self.stdout.write('🔍 Analizuję nieużywane produkty...')
        
        # Znajdź wszystkie produkty
        all_products = Product.objects.all()
        unused_products = []
        
        for product in all_products:
            # Sprawdź czy produkt ma jakiekolwiek stany magazynowe
            has_stock = Stock.objects.filter(product=product).exists()
            
            # Sprawdź czy produkt jest używany w zamówieniach klientów
            has_order_items = OrderItem.objects.filter(product=product).exists()
            
            # Sprawdź czy produkt jest używany w zleceniach kompletacji
            has_picking_items = PickingItem.objects.filter(product=product).exists()
            
            # Sprawdź czy produkt jest używany w zamówieniach do dostawców
            has_supplier_order_items = SupplierOrderItem.objects.filter(product=product).exists()
            
            # Sprawdź czy produkt jest używany w przyjęciach
            has_receiving_items = ReceivingItem.objects.filter(product=product).exists()
            
            # Sprawdź czy produkt jest używany w historii kompletacji
            has_picking_history = PickingHistory.objects.filter(product_scanned=product).exists()
            
            # Sprawdź czy produkt jest używany w historii przyjęć
            has_receiving_history = ReceivingHistory.objects.filter(product=product).exists()
            
            # Sprawdź czy produkt jest używany w dokumentach magazynowych
            has_document_items = DocumentItem.objects.filter(product=product).exists()
            
            # Produkt jest nieużywany jeśli nie ma żadnych powiązań
            is_unused = not any([
                has_stock, has_order_items, has_picking_items, 
                has_supplier_order_items, has_receiving_items,
                has_picking_history, has_receiving_history, has_document_items
            ])
            
            if is_unused:
                unused_products.append(product)
        
        if not unused_products:
            self.stdout.write(
                self.style.SUCCESS('✓ Nie znaleziono nieużywanych produktów do usunięcia.')
            )
            return
        
        # Wyświetl listę nieużywanych produktów
        self.stdout.write(f'\n📋 Znaleziono {len(unused_products)} nieużywanych produktów:')
        self.stdout.write('='*60)
        
        for i, product in enumerate(unused_products, 1):
            self.stdout.write(f'{i:3d}. {product.code} - {product.name}')
            if product.subiekt_id:
                self.stdout.write(f'     Subiekt ID: {product.subiekt_id}')
            self.stdout.write(f'     Utworzono: {product.created_at.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 Tryb podglądu - produkty nie zostały usunięte.')
            )
            return
        
        # Pytaj o potwierdzenie usunięcia
        confirm = input(f'\n❓ Czy chcesz usunąć {len(unused_products)} nieużywanych produktów? (y/N): ')
        if confirm.lower() not in ['y', 'yes', 'tak']:
            self.stdout.write('❌ Usuwanie anulowane.')
            return
        
        # Usuń nieużywane produkty
        deleted_count = 0
        for product in unused_products:
            try:
                product_name = f"{product.code} - {product.name}"
                product.delete()
                deleted_count += 1
                self.stdout.write(f'🗑️  Usunięto: {product_name}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Błąd podczas usuwania {product.code}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Pomyślnie usunięto {deleted_count} nieużywanych produktów.')
        )