from django.core.management.base import BaseCommand
from django.db import transaction
from wms.models import Product, ProductGroup
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Ładuje produkty Upcera z pliku Excel do bazy danych WMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='media/assets/uncategorized/Upcera_list.xlsx',
            help='Ścieżka do pliku Excel z produktami'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aktualizuj istniejące produkty zamiast pomijać je'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        update_existing = options['update']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Plik nie istnieje: {file_path}')
            )
            return
        
        self.stdout.write('Ładowanie produktów Upcera z pliku Excel...')
        
        try:
            # Wczytaj plik Excel
            df = pd.read_excel(file_path)
            self.stdout.write(f'Znaleziono {len(df)} produktów w pliku')
            
            # Statystyki
            created_count = 0
            updated_count = 0
            skipped_count = 0
            groups_created = 0
            
            for index, row in df.iterrows():
                try:
                    # Mapowanie kolumn
                    symbol = str(row['symbol']).strip() if pd.notna(row['symbol']) else ''
                    nazwa = str(row['nazwa']).strip() if pd.notna(row['nazwa']) else ''
                    opis = str(row['opis']).strip() if pd.notna(row['opis']) else ''
                    plu = str(row['plu']).strip() if pd.notna(row['plu']) else ''
                    stan = float(row['stan']) if pd.notna(row['stan']) else 0.0
                    grupa = str(row['grupa']).strip() if pd.notna(row['grupa']) else ''
                    typ_opakowania = str(row['typ_opakowania']).strip() if pd.notna(row['typ_opakowania']) else 'szt'
                    
                    # Walidacja wymaganych pól
                    if not symbol or not nazwa:
                        self.stdout.write(f'Pominięto wiersz {index + 1}: brak symbolu lub nazwy')
                        skipped_count += 1
                        continue
                    
                    # Sprawdź czy produkt już istnieje
                    existing_product = Product.objects.filter(code=symbol).first()
                    
                    if existing_product and not update_existing:
                        self.stdout.write(f'Pominięto istniejący produkt: {symbol}')
                        skipped_count += 1
                        continue
                    
                    # Generuj unikalny kod kreskowy jeśli PLU jest puste
                    barcode = plu if plu else f"UP{index+1:06d}"
                    
                    # Przygotuj dane produktu
                    product_data = {
                        'code': symbol,
                        'name': nazwa,
                        'description': opis,
                        'barcode': barcode,
                        'subiekt_id': int(plu) if plu and plu.isdigit() else None,
                        'subiekt_stock': stan,
                        'unit': typ_opakowania,
                    }
                    
                    # Utwórz lub zaktualizuj produkt
                    if existing_product and update_existing:
                        for field, value in product_data.items():
                            setattr(existing_product, field, value)
                        existing_product.save()
                        product = existing_product
                        updated_count += 1
                        self.stdout.write(f'✓ Zaktualizowano: {symbol}')
                    else:
                        product = Product.objects.create(**product_data)
                        created_count += 1
                        self.stdout.write(f'✓ Utworzono: {symbol}')
                    
                    # Obsługa grupy produktów
                    if grupa:
                        group, group_created = ProductGroup.objects.get_or_create(
                            name=grupa,
                            defaults={
                                'code': grupa.upper()[:20],  # Ogranicz do 20 znaków
                                'description': f'Grupa produktów: {grupa}',
                                'color': '#6c757d'
                            }
                        )
                        
                        if group_created:
                            groups_created += 1
                            self.stdout.write(f'  → Utworzono grupę: {grupa}')
                        
                        # Dodaj produkt do grupy
                        product.groups.add(group)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Błąd w wierszu {index + 1}: {str(e)}')
                    )
                    skipped_count += 1
                    continue
            
            # Wyświetl statystyki
            self.stdout.write('\n' + '='*50)
            self.stdout.write('STATYSTYKI ŁADOWANIA:')
            self.stdout.write('='*50)
            self.stdout.write(f'Utworzone produkty: {created_count}')
            self.stdout.write(f'Zaktualizowane produkty: {updated_count}')
            self.stdout.write(f'Pominięte produkty: {skipped_count}')
            self.stdout.write(f'Utworzone grupy: {groups_created}')
            self.stdout.write(f'Łącznie przetworzonych: {created_count + updated_count + skipped_count}')
            
            # Statystyki grup
            self.stdout.write('\nGRUPY PRODUKTÓW:')
            for group in ProductGroup.objects.all():
                count = group.products.count()
                self.stdout.write(f'{group.name}: {count} produktów')
            
            self.stdout.write(
                self.style.SUCCESS('\n✓ Produkty Upcera zostały załadowane pomyślnie!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Błąd podczas ładowania pliku: {str(e)}')
            ) 