from django.core.management.base import BaseCommand
from django.db import transaction
from wms.models import Product, ProductCode
import random
import string


class Command(BaseCommand):
    help = 'Dodaje przykładowe kody kreskowe i QR do produktów'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Pokazuje co zostanie zrobione bez wprowadzania zmian',
        )

    def generate_barcode(self):
        """Generuje przykładowy kod kreskowy EAN-13"""
        # EAN-13 ma 13 cyfr
        digits = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        # Prosty algorytm sprawdzający dla EAN-13
        checksum = sum(int(digits[i]) * (1 if i % 2 == 0 else 3) for i in range(12)) % 10
        checksum = (10 - checksum) % 10
        return digits + str(checksum)

    def generate_qr_code(self):
        """Generuje przykładowy kod QR"""
        # Prosty kod QR zawierający informacje o produkcie
        return f"QR{random.randint(100000, 999999)}"

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('Dodawanie przykładowych kodów do produktów...')
        
        products = Product.objects.all()
        
        if not products.exists():
            self.stdout.write('Nie znaleziono produktów do dodania kodów')
            return
        
        codes_added = 0
        
        if not dry_run:
            with transaction.atomic():
                for product in products:
                    # Dodaj kod kreskowy EAN-13
                    barcode = self.generate_barcode()
                    ProductCode.objects.get_or_create(
                        product=product,
                        code=barcode,
                        defaults={
                            'code_type': 'ean13',
                            'description': 'Przykładowy kod EAN-13'
                        }
                    )
                    
                    # Dodaj kod QR
                    qr_code = self.generate_qr_code()
                    ProductCode.objects.get_or_create(
                        product=product,
                        code=qr_code,
                        defaults={
                            'code_type': 'qr',
                            'description': 'Przykładowy kod QR'
                        }
                    )
                    
                    # Dodaj dodatkowy kod kreskowy Code 128
                    code128 = f"128{random.randint(100000, 999999)}"
                    ProductCode.objects.get_or_create(
                        product=product,
                        code=code128,
                        defaults={
                            'code_type': 'code128',
                            'description': 'Przykładowy kod Code 128'
                        }
                    )
                    
                    codes_added += 3
                    self.stdout.write(f'Dodano kody dla produktu: {product.name}')
        else:
            for product in products:
                self.stdout.write(f'Dodano kody dla produktu: {product.name}')
                codes_added += 3
        
        self.stdout.write(self.style.SUCCESS(f'Dodano {codes_added} kodów do {products.count()} produktów')) 