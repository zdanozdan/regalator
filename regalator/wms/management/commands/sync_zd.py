from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q, Count
from wms.models import SupplierOrder, SupplierOrderItem, Product
from subiekt.models import dok_Dokument
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Synchronizuje zamówienia do dostawców (ZD) z Subiektem'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Wymuś synchronizację wszystkich zamówień',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Liczba najnowszych zamówień do synchronizacji (domyślnie 20)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Pokaż tylko listę zamówień do synchronizacji bez ich tworzenia',
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Uruchom interaktywne menu',
        )

    def handle(self, *args, **options):
        if options['interactive']:
            self.show_interactive_menu(options)
            return
        
        if options['dry_run']:
            self.dry_run_sync(options)
            return
        
        self.sync_zd_from_subiekt(options)

    def show_interactive_menu(self, options):
        """Shows interactive menu for ZD sync operations"""
        while True:
            self.display_menu()
            choice = input('\nWybierz opcję (1-7): ').strip()
            
            if choice == '1':
                self.sync_zd_from_subiekt(options)
            elif choice == '2':
                self.dry_run_sync(options)
            elif choice == '3':
                self.show_sync_status()
            elif choice == '4':
                self.sync_single_zd()
            elif choice == '5':
                self.show_zd_details()
            elif choice == '6':
                self.manage_zd_orders()
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
        self.stdout.write(self.style.SUCCESS('MENU SYNCHRONIZACJI ZD Z SUBIEKTEM'))
        self.stdout.write('='*60)
        self.stdout.write('1. Synchronizuj ZD z Subiektu')
        self.stdout.write('2. Podgląd synchronizacji (dry-run)')
        self.stdout.write('3. Pokaż status synchronizacji')
        self.stdout.write('4. Synchronizuj pojedynczy ZD')
        self.stdout.write('5. Szczegóły ZD z Subiektu')
        self.stdout.write('6. Zarządzaj zamówieniami ZD')
        self.stdout.write('7. Wyjdź')
        self.stdout.write('='*60)

    def sync_zd_from_subiekt(self, options):
        """Synchronizes ZD orders from Subiekt to WMS"""
        self.stdout.write('\nRozpoczynam synchronizację ZD z Subiektu...')
        
        try:
            # Get ZD documents from Subiekt
            subiekt_zd_documents = dok_Dokument.dokument_objects.get_zd(limit=options['limit'])
            
            if not subiekt_zd_documents:
                self.stdout.write(self.style.WARNING('⚠️  Nie znaleziono dokumentów ZD w Subiekcie.'))
                return
            
            self.stdout.write(f'Znaleziono {len(subiekt_zd_documents)} dokumentów ZD do synchronizacji.')
            
            if not options['force']:
                confirm = input('Czy chcesz kontynuować? (y/N): ')
                if confirm.lower() not in ['y', 'yes', 'tak']:
                    self.stdout.write('Synchronizacja anulowana.')
                    return
            
            synced_count = 0
            for i, zd_doc in enumerate(subiekt_zd_documents, 1):
                try:
                    self.sync_zd_document(zd_doc)
                    synced_count += 1
                    self.stdout.write(f'✓ [{i}/{len(subiekt_zd_documents)}] ZD {zd_doc.dok_NrPelny} - {zd_doc.adr_Nazwa}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Błąd podczas synchronizacji ZD {zd_doc.dok_NrPelny}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\nPomyślnie zsynchronizowano {synced_count} zamówień ZD z Subiektu')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Błąd podczas synchronizacji: {str(e)}')
            )

    def dry_run_sync(self, options):
        """Shows what would be synchronized without actually doing it"""
        self.stdout.write('\nPODGLĄD SYNCHRONIZACJI ZD (DRY-RUN)')
        self.stdout.write('='*50)
        
        try:
            subiekt_zd_documents = dok_Dokument.dokument_objects.get_zd(limit=options['limit'])
            
            if not subiekt_zd_documents:
                self.stdout.write(self.style.WARNING('⚠️  Nie znaleziono dokumentów ZD w Subiekcie.'))
                return
            
            self.stdout.write(f'Znaleziono {len(subiekt_zd_documents)} dokumentów ZD:')
            self.stdout.write('='*50)
            
            for i, zd_doc in enumerate(subiekt_zd_documents, 1):
                self.display_zd_info(zd_doc, i)
                
                # Check if already exists in WMS
                existing_order = SupplierOrder.objects.filter(order_number=zd_doc.dok_NrPelny).first()
                if existing_order:
                    self.stdout.write(self.style.WARNING(f'  JUŻ ISTNIEJE W WMS: {existing_order.supplier_name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'  NOWY - zostanie utworzony'))
                
                self.stdout.write('')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas podglądu: {str(e)}')
            )

    def sync_zd_document(self, zd_doc):
        """Synchronizes a single ZD document from Subiekt to WMS"""
        # Check if order already exists
        existing_order = SupplierOrder.objects.filter(order_number=zd_doc.dok_NrPelny).first()
        
        if existing_order:
            # Update existing order
            existing_order.supplier_name = zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna or 'Nieznany dostawca'
            existing_order.supplier_code = ''  # No supplier code in Subiekt
            existing_order.order_date = zd_doc.dok_DataWyst or timezone.now().date()
            existing_order.expected_delivery_date = zd_doc.dok_PlatTermin or zd_doc.dok_DataMag or zd_doc.dok_DataWyst or timezone.now().date()
            existing_order.actual_delivery_date = zd_doc.dok_DataOtrzym
            existing_order.notes = f'ZD z Subiektu: {zd_doc.dok_NrPelny}'
            existing_order.updated_at = timezone.now()
            existing_order.save()
            
            self.stdout.write(f'  → Zaktualizowano zamówienie: {existing_order.supplier_name}')
            
            # Sync order items for existing order
            try:
                self.sync_zd_items(existing_order, zd_doc.dok_Id)
            except Exception as e:
                self.stdout.write(f'  Błąd podczas synchronizacji pozycji: {str(e)}')
        else:
            # Create new order
            supplier_order = SupplierOrder.objects.create(
                order_number=zd_doc.dok_NrPelny,
                supplier_name=zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna or 'Nieznany dostawca',
                supplier_code='',  # No supplier code in Subiekt
                order_date=zd_doc.dok_DataWyst or timezone.now().date(),
                expected_delivery_date=zd_doc.dok_PlatTermin or zd_doc.dok_DataMag or zd_doc.dok_DataWyst or timezone.now().date(),
                actual_delivery_date=zd_doc.dok_DataOtrzym,
                status='pending',  # Default status
                notes=f'ZD z Subiektu: {zd_doc.dok_NrPelny}'
            )
            
            self.stdout.write(f'  → Utworzono nowe zamówienie: {supplier_order.supplier_name}')
            
            # Try to sync order items if available
            try:
                self.sync_zd_items(supplier_order, zd_doc.dok_Id)
            except Exception as e:
                self.stdout.write(f'  Błąd podczas synchronizacji pozycji: {str(e)}')

    def sync_zd_items(self, supplier_order, zd_doc_id):
        """Synchronizes ZD order items from Subiekt"""
        self.stdout.write(f'Synchronizacja pozycji ZD {supplier_order.order_number} (ID: {zd_doc_id})')
        try:
            # Get document positions from Subiekt
            zd_positions = dok_Dokument.dokument_objects.get_zd_pozycje(zd_doc_id)
            
            if not zd_positions:
                self.stdout.write(f'  Brak pozycji w ZD {supplier_order.order_number}')
                return
            
            self.stdout.write(f'  Znaleziono {len(zd_positions)} pozycji w Subiekcie')
            
            for i, position in enumerate(zd_positions, 1):
                self.stdout.write(f'  Pozycja {i}: {position}')
                
                # Try to find corresponding product in WMS
                product = Product.objects.filter(subiekt_id=position['tw_Id']).first()
                
                if product:
                    # Create or update order item
                    order_item, created = SupplierOrderItem.objects.get_or_create(
                        supplier_order=supplier_order,
                        product=product,
                        defaults={
                            'quantity_ordered': Decimal(str(position.get('ob_Znak', 0))),
                            'quantity_received': 0,
                            'notes': f'Pozycja z Subiektu: {position.get("ob_Id", "")}'
                        }
                    )
                    
                    if not created:
                        # Update existing item
                        order_item.quantity_ordered = Decimal(str(position.get('ob_Znak', 0)))
                        order_item.notes = f'Pozycja z Subiektu: {position.get("ob_Id", "")}'
                        order_item.save()
                    
                    self.stdout.write(f'    ✓ {product.name} - {order_item.quantity_ordered}')
                else:
                    self.stdout.write(f'    Produkt nie znaleziony w WMS (Subiekt ID: {position["tw_Id"]})')
                    
        except Exception as e:
            self.stdout.write(f'  Błąd podczas pobierania pozycji ZD: {str(e)}')
            import traceback
            self.stdout.write(f'  Szczegóły błędu: {traceback.format_exc()}')

    def display_zd_info(self, zd_doc, index):
        """Displays information about a ZD document"""
        self.stdout.write(f'{index:2d}. ZD {zd_doc.dok_NrPelny}')
        self.stdout.write(f'     Dostawca: {zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna or "Nieznany"}')
        self.stdout.write(f'     Data wystawienia: {zd_doc.dok_DataWyst or "Brak"}')
        self.stdout.write(f'     Data magazynowa: {zd_doc.dok_DataMag or "Brak"}')
        self.stdout.write(f'     Data otrzymania (przewidywana): {zd_doc.dok_PlatTermin or "Brak"}')
        
        if zd_doc.adr_Ulica:
            self.stdout.write(f'     Adres: {zd_doc.adr_Ulica}, {zd_doc.adr_Miejscowosc} {zd_doc.adr_Kod}')

    def show_sync_status(self):
        """Shows synchronization status"""
        self.stdout.write('\nSTATUS SYNCHRONIZACJI ZD')
        self.stdout.write('='*40)
        
        total_orders = SupplierOrder.objects.count()
        orders_with_notes = SupplierOrder.objects.filter(notes__icontains='ZD z Subiektu').count()
        
        self.stdout.write(f'Łączna liczba zamówień ZD w WMS: {total_orders}')
        self.stdout.write(f'Zsynchronizowane z Subiektu: {orders_with_notes}')
        self.stdout.write(f'Lokalne zamówienia: {total_orders - orders_with_notes}')
        
        if total_orders > 0:
            latest_order = SupplierOrder.objects.order_by('-created_at').first()
            if latest_order:
                self.stdout.write(f'Ostatnio dodane: {latest_order.order_number} - {latest_order.supplier_name}')
        
        # Show recent orders
        recent_orders = SupplierOrder.objects.order_by('-created_at')[:5]
        if recent_orders:
            self.stdout.write('\nOstatnie zamówienia:')
            for order in recent_orders:
                sync_status = 'SYNC' if 'ZD z Subiektu' in order.notes else 'LOCAL'
                self.stdout.write(f'  {sync_status} {order.order_number} - {order.supplier_name}')
                self.stdout.write(f'     Status: {order.get_status_display()}')
                self.stdout.write(f'     Pozycje: {order.total_items}')

    def sync_single_zd(self):
        """Synchronizes a single ZD document from Subiekt"""
        self.stdout.write('\nSYNCHRONIZACJA POJEDYNCZEGO ZD')
        self.stdout.write('='*50)
        
        try:
            # Get available ZD documents from Subiekt
            subiekt_zd_documents = dok_Dokument.dokument_objects.get_zd(limit=50)
            
            if not subiekt_zd_documents:
                self.stdout.write(self.style.WARNING('⚠️  Nie znaleziono dokumentów ZD w Subiekcie.'))
                return
            
            # Display available ZD documents
            self.stdout.write(f'Dostępne dokumenty ZD ({len(subiekt_zd_documents)}):')
            self.stdout.write('='*50)
            
            for i, zd_doc in enumerate(subiekt_zd_documents, 1):
                existing_order = SupplierOrder.objects.filter(order_number=zd_doc.dok_NrPelny).first()
                status = 'ISTNIEJE' if existing_order else 'NOWY'
                self.stdout.write(f'{i:2d}. {status} - {zd_doc.dok_NrPelny} - {zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna}')
            
            # Ask user to select
            try:
                choice = input(f'\nWybierz numer ZD (1-{len(subiekt_zd_documents)}) lub 0 aby anulować: ').strip()
                if choice == '0':
                    self.stdout.write('❌ Anulowano.')
                    return
                
                choice_num = int(choice)
                if choice_num < 1 or choice_num > len(subiekt_zd_documents):
                    self.stdout.write(self.style.ERROR('Nieprawidłowy numer.'))
                    return
                
                selected_zd = subiekt_zd_documents[choice_num - 1]
                
                # Show details and confirm
                self.display_zd_info(selected_zd, choice_num)
                confirm = input('\nCzy chcesz zsynchronizować ten ZD? (y/N): ')
                
                if confirm.lower() in ['y', 'yes', 'tak']:
                    self.sync_zd_document(selected_zd)
                    self.stdout.write(
                        self.style.SUCCESS(f'Zsynchronizowano ZD: {selected_zd.dok_NrPelny}')
                    )
                else:
                    self.stdout.write('❌ Anulowano.')
                    
            except ValueError:
                self.stdout.write(self.style.ERROR('Nieprawidłowy format numeru.'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Błąd podczas synchronizacji: {str(e)}')
            )

    def show_zd_details(self):
        """Shows detailed information about ZD documents from Subiekt"""
        self.stdout.write('\nSZCZEGÓŁY ZD Z SUBIEKTU')
        self.stdout.write('='*50)
        
        try:
            limit = input('Podaj liczbę dokumentów do wyświetlenia (domyślnie 10): ').strip()
            if not limit:
                limit = 10
            else:
                limit = int(limit)
            
            subiekt_zd_documents = dok_Dokument.dokument_objects.get_zd(limit=limit)
            
            if not subiekt_zd_documents:
                self.stdout.write(self.style.WARNING('⚠️  Nie znaleziono dokumentów ZD w Subiekcie.'))
                return
            
            self.stdout.write(f'Szczegóły {len(subiekt_zd_documents)} dokumentów ZD:')
            self.stdout.write('='*50)
            
            for i, zd_doc in enumerate(subiekt_zd_documents, 1):
                self.display_zd_detailed_info(zd_doc, i)
                self.stdout.write('')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Błąd podczas pobierania szczegółów: {str(e)}')
            )

    def display_zd_detailed_info(self, zd_doc, index):
        """Displays detailed information about a ZD document"""
        self.stdout.write(f'{index:2d}. ZD {zd_doc.dok_NrPelny}')
        self.stdout.write(f'     ID dokumentu: {zd_doc.dok_Id}')
        self.stdout.write(f'     Dostawca: {zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna or "Nieznany"}')
        self.stdout.write(f'     Data wystawienia: {zd_doc.dok_DataWyst or "Brak"}')
        self.stdout.write(f'     Data magazynowa: {zd_doc.dok_DataMag or "Brak"}')
        self.stdout.write(f'     Data otrzymania (przewidywana): {zd_doc.dok_PlatTermin or "Brak"}')
        
        if zd_doc.adr_Ulica:
            self.stdout.write(f'     Adres: {zd_doc.adr_Ulica}, {zd_doc.adr_Miejscowosc} {zd_doc.adr_Kod}')
        
        # Check if exists in WMS
        existing_order = SupplierOrder.objects.filter(order_number=zd_doc.dok_NrPelny).first()
        if existing_order:
            self.stdout.write(self.style.SUCCESS(f'     ISTNIEJE W WMS: {existing_order.supplier_name}'))
            self.stdout.write(f'     Status WMS: {existing_order.get_status_display()}')
            self.stdout.write(f'     Pozycje WMS: {existing_order.total_items}')
        else:
            self.stdout.write(self.style.WARNING(f'     NIE ISTNIEJE W WMS'))

    def manage_zd_orders(self):
        """Manages ZD orders in WMS"""
        while True:
            self.stdout.write('\nZARZĄDZANIE ZAMÓWIENIAMI ZD')
            self.stdout.write('='*50)
            self.stdout.write('1. Lista wszystkich zamówień ZD')
            self.stdout.write('2. Wyszukaj zamówienie')
            self.stdout.write('3. Statystyki zamówień')
            self.stdout.write('4. Usuń zamówienie')
            self.stdout.write('5. Powrót do głównego menu')
            
            choice = input('\nWybierz opcję (1-5): ').strip()
            
            if choice == '1':
                self.list_zd_orders()
            elif choice == '2':
                self.search_zd_orders()
            elif choice == '3':
                self.show_zd_statistics()
            elif choice == '4':
                self.delete_zd_order()
            elif choice == '5':
                break
            else:
                self.stdout.write(self.style.ERROR('Nieprawidłowy wybór.'))
            
            if choice in ['1', '2', '3', '4']:
                input('\nNaciśnij Enter, aby kontynuować...')

    def list_zd_orders(self):
        """Lists all ZD orders in WMS"""
        self.stdout.write('\nLISTA ZAMÓWIENIÓW ZD W WMS')
        self.stdout.write('='*50)
        
        orders = SupplierOrder.objects.all().order_by('-created_at')
        
        if not orders:
            self.stdout.write('Brak zamówień ZD w systemie.')
            return
        
        self.stdout.write(f'Znaleziono {orders.count()} zamówień:')
        self.stdout.write('='*50)
        
        for i, order in enumerate(orders, 1):
            sync_status = 'SYNC' if 'ZD z Subiektu' in order.notes else 'LOCAL'
            self.stdout.write(f'{i:3d}. {sync_status} {order.order_number} - {order.supplier_name}')
            self.stdout.write(f'     Status: {order.get_status_display()}')
            self.stdout.write(f'     Data: {order.order_date}')
            self.stdout.write(f'     Pozycje: {order.total_items}')
            self.stdout.write(f'     Przyjęte: {order.received_items}')
            self.stdout.write('')

    def search_zd_orders(self):
        """Searches for ZD orders"""
        self.stdout.write('\nWYSZUKIWANIE ZAMÓWIENIÓW ZD')
        self.stdout.write('='*50)
        
        search_term = input('Podaj termin wyszukiwania (numer, dostawca): ').strip()
        
        if not search_term:
            self.stdout.write('Nie podano terminu wyszukiwania.')
            return
        
        orders = SupplierOrder.objects.filter(
            Q(order_number__icontains=search_term) |
            Q(supplier_name__icontains=search_term)
        ).order_by('-created_at')
        
        if not orders:
            self.stdout.write(f'Nie znaleziono zamówień dla: "{search_term}"')
            return
        
        self.stdout.write(f'Znaleziono {orders.count()} zamówień:')
        self.stdout.write('='*50)
        
        for i, order in enumerate(orders, 1):
            sync_status = 'SYNC' if 'ZD z Subiektu' in order.notes else 'LOCAL'
            self.stdout.write(f'{i:2d}. {sync_status} {order.order_number} - {order.supplier_name}')
            self.stdout.write(f'     Status: {order.get_status_display()}')
            self.stdout.write(f'     Data: {order.order_date}')
            self.stdout.write(f'     Pozycje: {order.total_items}')
            self.stdout.write('')

    def show_zd_statistics(self):
        """Shows ZD order statistics"""
        self.stdout.write('\nSTATYSTYKI ZAMÓWIENIÓW ZD')
        self.stdout.write('='*50)
        
        total_orders = SupplierOrder.objects.count()
        synced_orders = SupplierOrder.objects.filter(notes__icontains='ZD z Subiektu').count()
        local_orders = total_orders - synced_orders
        
        self.stdout.write(f'Łączna liczba zamówień: {total_orders}')
        self.stdout.write(f'Zsynchronizowane z Subiektu: {synced_orders}')
        self.stdout.write(f'Lokalne zamówienia: {local_orders}')
        
        # Status statistics
        status_stats = SupplierOrder.objects.values('status').annotate(count=Count('status'))
        if status_stats:
            self.stdout.write('\nStatusy zamówień:')
            for stat in status_stats:
                status_name = dict(SupplierOrder.SUPPLIER_STATUS_CHOICES)[stat['status']]
                self.stdout.write(f'  {status_name}: {stat["count"]}')
        
        # Recent activity
        recent_orders = SupplierOrder.objects.order_by('-created_at')[:5]
        if recent_orders:
            self.stdout.write('\nOstatnie zamówienia:')
            for order in recent_orders:
                sync_status = 'SYNC' if 'ZD z Subiektu' in order.notes else 'LOCAL'
                self.stdout.write(f'  {sync_status} {order.order_number} - {order.created_at.strftime("%Y-%m-%d %H:%M")}')

    def delete_zd_order(self):
        """Deletes a ZD order"""
        self.stdout.write('\nUSUWANIE ZAMÓWIENIA ZD')
        self.stdout.write('='*50)
        
        order_number = input('Podaj numer zamówienia do usunięcia: ').strip()
        
        if not order_number:
            self.stdout.write('Nie podano numeru zamówienia.')
            return
        
        try:
            order = SupplierOrder.objects.get(order_number=order_number)
            
            self.stdout.write(f'Znalezione zamówienie:')
            self.stdout.write(f'  Numer: {order.order_number}')
            self.stdout.write(f'  Dostawca: {order.supplier_name}')
            self.stdout.write(f'  Status: {order.get_status_display()}')
            self.stdout.write(f'  Pozycje: {order.total_items}')
            self.stdout.write(f'  Utworzone: {order.created_at.strftime("%Y-%m-%d %H:%M")}')
            
            confirm = input(f'\nCzy na pewno chcesz usunąć zamówienie {order.order_number}? (y/N): ')
            
            if confirm.lower() in ['y', 'yes', 'tak']:
                order.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Usunięto zamówienie: {order_number}')
                )
            else:
                self.stdout.write('Anulowano usuwanie.')
                
        except SupplierOrder.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Nie znaleziono zamówienia: {order_number}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas usuwania: {str(e)}')
            ) 