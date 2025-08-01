from django.core.management.base import BaseCommand
from wms.models import ProductGroup, Product


class Command(BaseCommand):
    help = 'Tworzy przykładowe grupy produktów i przypisuje do nich produkty'

    def handle(self, *args, **options):
        self.stdout.write('Tworzenie przykładowych grup produktów...')
        
        # Usuń istniejące grupy
        ProductGroup.objects.all().delete()
        
        # Utwórz grupy produktów
        groups_data = [
            {
                'name': 'Elektronika',
                'code': 'ELEC',
                'description': 'Produkty elektroniczne - komputery, monitory, akcesoria',
                'color': '#6c757d'
            },
            {
                'name': 'Akcesoria komputerowe',
                'code': 'ACC',
                'description': 'Akcesoria do komputerów - klawiatury, myszy, kamery',
                'color': '#495057'
            },
            {
                'name': 'Pamięć i dyski',
                'code': 'MEM',
                'description': 'Pamięć RAM, dyski SSD, karty pamięci',
                'color': '#6c757d'
            },
            {
                'name': 'Audio/Video',
                'code': 'AV',
                'description': 'Głośniki, kamery, mikrofony',
                'color': '#495057'
            },
            {
                'name': 'Premium',
                'code': 'PREMIUM',
                'description': 'Produkty premium - wysokiej jakości',
                'color': '#6c757d'
            },
            {
                'name': 'Bestsellery',
                'code': 'BEST',
                'description': 'Najpopularniejsze produkty',
                'color': '#495057'
            }
        ]
        
        groups = {}
        for group_data in groups_data:
            group, created = ProductGroup.objects.get_or_create(
                code=group_data['code'],
                defaults=group_data
            )
            groups[group_data['code']] = group
            if created:
                self.stdout.write(f'✓ Utworzono grupę: {group.name}')
            else:
                self.stdout.write(f'✓ Grupa już istnieje: {group.name}')
        
        # Pobierz wszystkie produkty
        products = Product.objects.all()
        
        # Przypisz produkty do grup (jeden produkt może być w wielu grupach)
        product_assignments = {
            'Laptop Dell Latitude 5520': ['ELEC', 'PREMIUM', 'BEST'],
            'Monitor LG 24ML600': ['ELEC', 'AV'],
            'Klawiatura mechaniczna Logitech': ['ACC', 'PREMIUM'],
            'Mysz bezprzewodowa Microsoft': ['ACC'],
            'Dysk SSD Samsung 500GB': ['MEM', 'BEST'],
            'Pamięć RAM DDR4 8GB': ['MEM'],
            'Kamera internetowa Logitech C920': ['ACC', 'AV', 'BEST'],
            'Głośniki Creative Pebble': ['AV']
        }
        
        self.stdout.write('\nPrzypisywanie produktów do grup...')
        
        for product in products:
            if product.name in product_assignments:
                # Wyczyść istniejące grupy
                product.groups.clear()
                
                # Dodaj nowe grupy
                for group_code in product_assignments[product.name]:
                    if group_code in groups:
                        product.groups.add(groups[group_code])
                
                group_names = [groups[code].name for code in product_assignments[product.name] if code in groups]
                self.stdout.write(f'✓ {product.name} → {", ".join(group_names)}')
            else:
                # Produkty bez przypisania pozostają bez grupy
                product.groups.clear()
                self.stdout.write(f'○ {product.name} → bez grupy')
        
        # Wyświetl statystyki
        self.stdout.write('\n' + '='*50)
        self.stdout.write('STATYSTYKI GRUP:')
        self.stdout.write('='*50)
        
        for group in ProductGroup.objects.all():
            count = group.products.count()
            self.stdout.write(f'{group.name}: {count} produktów')
        
        total_products = Product.objects.count()
        products_with_groups = Product.objects.filter(groups__isnull=False).distinct().count()
        products_without_groups = total_products - products_with_groups
        
        self.stdout.write(f'\nŁącznie produktów: {total_products}')
        self.stdout.write(f'Produktów z grupami: {products_with_groups}')
        self.stdout.write(f'Produktów bez grup: {products_without_groups}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Przykładowe grupy produktów zostały utworzone pomyślnie!')
        ) 