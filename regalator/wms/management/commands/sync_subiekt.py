from django.core.management.base import BaseCommand
from django.utils import timezone
from wms.models import Product, ProductGroup, ProductCode
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
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Uruchom interaktywne menu',
        )

    def handle(self, *args, **options):
        # If specific arguments are provided, run the original logic
        if any([options['drop_unused'], options['product_id'], options['force']]):
            self.handle_legacy_mode(options)
            return
        
        # Interactive mode is now default - show interactive menu
        self.show_interactive_menu(options)
        return
    
    def handle_legacy_mode(self, options):
        """Handles the original command logic for backward compatibility"""
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
    
    def show_interactive_menu(self, options):
        """Shows interactive menu for sync operations"""
        while True:
            self.display_menu()
            choice = input('\nWybierz opcję (1-7): ').strip()
            
            if choice == '1':
                self.sync_all_products()
            elif choice == '2':
                self.sync_single_product()
            elif choice == '3':
                self.show_unused_products(options.get('dry_run', False))
            elif choice == '4':
                self.show_sync_status()
            elif choice == '5':
                self.show_product_info()
            elif choice == '6':
                self.sync_barcodes_from_subiekt()
            elif choice == '7':
                self.stdout.write(self.style.SUCCESS('Do widzenia!'))
                break
            else:
                self.stdout.write(self.style.ERROR('Nieprawidłowy wybór. Spróbuj ponownie.'))
            
            if choice in ['1', '2', '3', '4', '5', '6']:
                input('\nNaciśnij Enter, aby kontynuować...')
    
    def display_menu(self):
        """Displays the main menu"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('MENU SYNCHRONIZACJI Z SUBIEKTEM'))
        self.stdout.write('='*60)
        self.stdout.write('1. Synchronizuj wszystkie produkty z Subiektu')
        self.stdout.write('2. Synchronizuj pojedynczy produkt')
        self.stdout.write('3. Zarządzaj nieużywanymi produktami')
        self.stdout.write('4. Pokaż status synchronizacji')
        self.stdout.write('5. Informacje o produktach')
        self.stdout.write('6. Synchronizuj kody kreskowe z Subiektu')
        self.stdout.write('7. Wyjdź')
        self.stdout.write('='*60)
    
    def sync_all_products(self):
        """Synchronizes all products from Subiekt"""
        self.stdout.write('\nRozpoczynam synchronizację wszystkich produktów z Subiektu...')
        
        try:
            subiekt_products = tw_Towar.subiekt_objects.get_products_with_stock(limit=0)
            
            if not subiekt_products:
                self.stdout.write(self.style.WARNING('Nie znaleziono produktów w Subiekcie.'))
                return
            
            self.stdout.write(f'Znaleziono {len(subiekt_products)} produktów do synchronizacji.')
            confirm = input('Czy chcesz kontynuować? (y/N): ')
            
            if confirm.lower() not in ['y', 'yes', 'tak']:
                self.stdout.write('Synchronizacja anulowana.')
                return
            
            synced_count = 0
            for i, subiekt_product in enumerate(subiekt_products, 1):
                self.sync_product_from_subiekt(subiekt_product)
                synced_count += 1
                self.stdout.write(f'[{i}/{len(subiekt_products)}] {subiekt_product.tw_Nazwa}')
            
            self.stdout.write(
                self.style.SUCCESS(f'\nPomyślnie zsynchronizowano {synced_count} produktów z Subiektu')
            )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas synchronizacji: {str(e)}')
            )
    
    def sync_single_product(self):
        """Synchronizes a single product from Subiekt"""
        self.stdout.write('\nSynchronizacja pojedynczego produktu')
        self.stdout.write('='*40)
        
        try:
            product_id = input('Podaj ID produktu z Subiektu (tw_Id): ').strip()
            
            if not product_id:
                self.stdout.write('Nie podano ID produktu.')
                return
            
            try:
                product_id = int(product_id)
            except ValueError:
                self.stdout.write('Nieprawidłowy format ID produktu.')
                return
            
            subiekt_product = tw_Towar.subiekt_objects.get_product_by_id(product_id)
            
            if not subiekt_product:
                self.stdout.write(
                    self.style.ERROR(f'Produkt o ID {product_id} nie istnieje w Subiekcie')
                )
                return
            
            # Wyświetl informacje o produkcie
            self.display_product_info(subiekt_product)
            
            # Pytaj o potwierdzenie
            confirm = input('\nCzy chcesz kontynuować synchronizację? (y/N): ')
            if confirm.lower() in ['y', 'yes', 'tak']:
                self.sync_product_from_subiekt(subiekt_product)
                self.stdout.write(
                    self.style.SUCCESS(f'Zsynchronizowano produkt: {subiekt_product.tw_Nazwa}')
                )
            else:
                self.stdout.write('Synchronizacja anulowana.')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas synchronizacji: {str(e)}')
            )
    
    def show_unused_products(self, dry_run=False):
        """Shows unused products management menu"""
        while True:
            self.stdout.write('\nZARZĄDZANIE NIEUŻYWANYMI PRODUKTAMI')
            self.stdout.write('='*50)
            self.stdout.write('1. Pokaż nieużywane produkty (podgląd)')
            self.stdout.write('2. Usuń nieużywane produkty')
            self.stdout.write('3. Powrót do głównego menu')
            
            choice = input('\nWybierz opcję (1-3): ').strip()
            
            if choice == '1':
                self.drop_unused_products(dry_run=True)
            elif choice == '2':
                self.drop_unused_products(dry_run=False)
            elif choice == '3':
                break
            else:
                self.stdout.write(self.style.ERROR('Nieprawidłowy wybór.'))
    
    def show_sync_status(self):
        """Shows synchronization status"""
        self.stdout.write('\n📊 STATUS SYNCHRONIZACJI')
        self.stdout.write('='*40)
        
        total_products = Product.objects.count()
        synced_products = Product.objects.filter(last_sync_date__isnull=False).count()
        unsynced_products = total_products - synced_products
        
        self.stdout.write(f'📦 Łączna liczba produktów w WMS: {total_products}')
        self.stdout.write(f'✅ Zsynchronizowane produkty: {synced_products}')
        self.stdout.write(f'❌ Niesynchronizowane produkty: {unsynced_products}')
        
        if synced_products > 0:
            latest_sync = Product.objects.filter(last_sync_date__isnull=False).order_by('-last_sync_date').first()
            if latest_sync:
                self.stdout.write(f'🕒 Ostatnia synchronizacja: {latest_sync.last_sync_date.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Show products with Subiekt IDs
        subiekt_products = Product.objects.filter(subiekt_id__isnull=False).count()
        self.stdout.write(f'🔗 Produkty z ID Subiekt: {subiekt_products}')
    
    def show_product_info(self):
        """Shows detailed product information"""
        self.stdout.write('\n🔍 INFORMACJE O PRODUKTACH')
        self.stdout.write('='*40)
        
        total_products = Product.objects.count()
        self.stdout.write(f'📦 Łączna liczba produktów: {total_products}')
        
        if total_products == 0:
            self.stdout.write('ℹ️  Brak produktów w systemie.')
            return
        
        # Show recent products
        recent_products = Product.objects.order_by('-created_at')[:5]
        self.stdout.write('\n📋 Ostatnio dodane produkty:')
        for product in recent_products:
            sync_status = '✅' if product.last_sync_date else '❌'
            self.stdout.write(f'  {sync_status} {product.code} - {product.name}')
            if product.subiekt_id:
                self.stdout.write(f'     Subiekt ID: {product.subiekt_id}')
        
        # Show products with stock
        products_with_stock = Product.objects.filter(subiekt_stock__gt=0).count()
        self.stdout.write(f'\n📦 Produkty ze stanem magazynowym: {products_with_stock}')
        
        # Show product groups
        from wms.models import ProductGroup
        groups_count = ProductGroup.objects.count()
        self.stdout.write(f'🏷️  Liczba grup produktów: {groups_count}')
    
    def sync_product_from_subiekt(self, subiekt_product):
        """Synchronizuje produkt z Subiektu do WMS"""
        from wms.models import ProductCode
        
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
                'unit': 'szt',  # Domyślna jednostka
            }
        )
        
        if not created:
            # Aktualizuj istniejący produkt
            wms_product.code = subiekt_product.tw_Symbol
            wms_product.name = subiekt_product.tw_Nazwa
            wms_product.description = subiekt_product.tw_Opis or ''
        
        # Aktualizuj dane z Subiektu
        wms_product.subiekt_stock = Decimal(str(getattr(subiekt_product, 'st_Stan', 0)))
        wms_product.subiekt_stock_reserved = Decimal(str(getattr(subiekt_product, 'st_StanRez', 0)))
        wms_product.last_sync_date = timezone.now()
        
        # Obsługa kodów kreskowych z Subiektu
        subiekt_barcode = str(subiekt_product.tw_Id)
        if subiekt_barcode:
            # Sprawdź czy kod już istnieje dla tego produktu
            existing_code = ProductCode.objects.filter(
                product=wms_product,
                code=subiekt_barcode,
                code_type='barcode'
            ).first()
            
            if not existing_code:
                # Utwórz nowy kod kreskowy
                ProductCode.objects.create(
                    product=wms_product,
                    code=subiekt_barcode,
                    code_type='barcode',
                    description='Kod z Subiektu (tw_Id)'
                )
                self.stdout.write(f'  Dodano kod kreskowy: {subiekt_barcode}')
            else:
        
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
            
            # Pokaż informacje o kodach kreskowych
            from wms.models import ProductCode
            product_codes = ProductCode.objects.filter(product=existing_product, is_active=True)
            if product_codes.exists():
                self.stdout.write(f'  Kody kreskowe ({product_codes.count()}):')
                for code in product_codes:
                    self.stdout.write(f'    - {code.code} ({code.get_code_type_display()})')
            else:
                self.stdout.write('  Brak kodów kreskowych')
                
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
            self.style.SUCCESS(f'\nPomyślnie usunięto {deleted_count} nieużywanych produktów.')
        )
    
    def sync_barcodes_from_subiekt(self):
        """Synchronizes barcodes from Subiekt to WMS"""
        self.stdout.write('\nSynchronizacja kodów kreskowych z Subiektu')
        self.stdout.write('='*50)
        
        try:
            # Get all products with Subiekt IDs
            wms_products = Product.objects.filter(subiekt_id__isnull=False)
            
            if not wms_products.exists():
                self.stdout.write(self.style.WARNING('Nie znaleziono produktów z ID Subiekt do synchronizacji kodów kreskowych.'))
                return
            
            self.stdout.write(f'Znaleziono {wms_products.count()} produktów z ID Subiekt.')
            confirm = input('Czy chcesz kontynuować synchronizację kodów kreskowych? (y/N): ')
            
            if confirm.lower() not in ['y', 'yes', 'tak']:
                self.stdout.write('Synchronizacja anulowana.')
                return
            
            synced_count = 0
            created_count = 0
            updated_count = 0
            
            for product in wms_products:
                subiekt_id = str(product.subiekt_id)
                
                # Check if barcode already exists for this product
                existing_code = ProductCode.objects.filter(
                    product=product,
                    code=subiekt_id,
                    code_type='barcode'
                ).first()
                
                if existing_code:
                    # Update existing barcode if needed
                    existing_code.description = 'Kod z Subiektu (tw_Id)'
                    existing_code.save()
                        updated_count += 1
                        self.stdout.write(f'  Zaktualizowano kod: {product.code} - {subiekt_id}')
                else:
                    # Create new barcode
                    ProductCode.objects.create(
                        product=product,
                        code=subiekt_id,
                        code_type='barcode',
                        description='Kod z Subiektu (tw_Id)'
                    )
                    created_count += 1
                    self.stdout.write(f'  Utworzono kod: {product.code} - {subiekt_id}')
                
                synced_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'\nSynchronizacja zakończona:')
            )
            self.stdout.write(f'  Produkty przetworzone: {synced_count}')
            self.stdout.write(f'  Nowe kody utworzone: {created_count}')
            self.stdout.write(f'  Kody zaktualizowane: {updated_count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas synchronizacji kodów kreskowych: {str(e)}')
            )