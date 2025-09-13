from django.core.management.base import BaseCommand
from django.db import transaction
from wms.models import Product, ProductCode


class Command(BaseCommand):
    help = 'Migruje istniejące kody kreskowe do nowego modelu ProductCode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Pokazuje co zostanie zrobione bez wprowadzania zmian',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Wymuś migrację nawet jeśli pole barcode nie istnieje',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write('Sprawdzanie istniejących kodów kreskowych...')
        
        # Sprawdź czy pole barcode jeszcze istnieje w modelu
        try:
            # Próbujemy sprawdzić czy pole barcode istnieje
            products_with_barcodes = Product.objects.filter(barcode__isnull=False).exclude(barcode='')
            
            if products_with_barcodes.exists():
                self.stdout.write(f'Znaleziono {products_with_barcodes.count()} produktów z kodami kreskowymi do migracji')
                
                if not dry_run:
                    with transaction.atomic():
                        for product in products_with_barcodes:
                            # Utwórz ProductCode dla każdego produktu
                            ProductCode.objects.create(
                                product=product,
                                code=product.barcode,
                                code_type='barcode',
                                description='Migrowany z pola barcode'
                            )
                            self.stdout.write(f'Utworzono kod kreskowy dla produktu: {product.name}')
                else:
                    for product in products_with_barcodes:
                        self.stdout.write(f'Utworzono kod kreskowy dla produktu: {product.name} ({product.barcode})')
            else:
                self.stdout.write('Nie znaleziono produktów z kodami kreskowymi do migracji')
                
        except Exception as e:
            if 'barcode' in str(e).lower():
                self.stdout.write(
                    self.style.WARNING('Pole barcode zostało już usunięte z modelu Product.')
                )
                self.stdout.write(
                    self.style.SUCCESS('Migracja została już wykonana lub nie jest potrzebna.')
                )
                
                # Sprawdź czy są już jakieś kody w nowym systemie
                existing_codes = ProductCode.objects.count()
                if existing_codes > 0:
                    self.stdout.write(f'Znaleziono {existing_codes} kodów w nowym systemie ProductCode.')
                else:
                    self.stdout.write('Brak kodów w nowym systemie ProductCode.')
                    
                    if force:
                        self.stdout.write('Uruchamiam migrację z Subiektu...')
                        self.migrate_from_subiekt(dry_run)
                    else:
                        self.stdout.write(
                            'Użyj --force aby uruchomić migrację z Subiektu lub --dry-run aby zobaczyć co zostanie zrobione.'
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Błąd podczas migracji: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS('Migracja zakończona'))
    
    def migrate_from_subiekt(self, dry_run=False):
        """Migruje kody z Subiektu jeśli pole barcode nie istnieje"""
        try:
            from subiekt.models import tw_Towar
            
            self.stdout.write('Pobieranie produktów z Subiektu...')
            subiekt_products = tw_Towar.subiekt_objects.get_products_with_stock(limit=0)
            
            if not subiekt_products:
                self.stdout.write('Nie znaleziono produktów w Subiekcie.')
                return
            
            self.stdout.write(f'Znaleziono {len(subiekt_products)} produktów w Subiekcie.')
            
            if not dry_run:
                with transaction.atomic():
                    for subiekt_product in subiekt_products:
                        # Znajdź lub utwórz produkt w WMS
                        wms_product, created = Product.objects.get_or_create(
                            subiekt_id=subiekt_product.tw_Id,
                            defaults={
                                'code': subiekt_product.tw_Symbol,
                                'name': subiekt_product.tw_Nazwa,
                                'description': subiekt_product.tw_Opis or '',
                                'unit': 'szt',
                            }
                        )
                        
                        # Utwórz kod kreskowy z Subiektu
                        subiekt_barcode = str(subiekt_product.tw_Id)
                        existing_code = ProductCode.objects.filter(
                            product=wms_product,
                            code=subiekt_barcode
                        ).first()
                        
                        if not existing_code:
                            ProductCode.objects.create(
                                product=wms_product,
                                code=subiekt_barcode,
                                code_type='barcode',
                                description='Kod z Subiektu (tw_Id)'
                            )
                            self.stdout.write(f'Dodano kod kreskowy dla produktu: {wms_product.name}')
                        else:
                            self.stdout.write(f'Kod kreskowy już istnieje dla produktu: {wms_product.name}')
            else:
                for subiekt_product in subiekt_products:
                    self.stdout.write(f'Dodano kod kreskowy dla produktu: {subiekt_product.tw_Nazwa} ({subiekt_product.tw_Id})')
                    
        except ImportError:
            self.stdout.write(
                self.style.ERROR('Nie można zaimportować modeli Subiekt. Upewnij się, że Subiekt jest skonfigurowany.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas migracji z Subiektu: {e}')
            ) 