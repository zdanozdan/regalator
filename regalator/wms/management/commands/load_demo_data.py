from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from wms.models import (
    Product, Location, Stock, CustomerOrder, OrderItem,
    PickingOrder, PickingItem, SupplierOrder, SupplierOrderItem,
    ReceivingOrder, ReceivingItem
)

class Command(BaseCommand):
    help = 'Ładuje dane demo do systemu WMS'

    def handle(self, *args, **options):
        self.stdout.write('Ładowanie danych demo...')
        
        # Utwórz użytkownika demo
        user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'email': 'demo@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write('✓ Utworzono użytkownika demo')
        else:
            self.stdout.write('✓ Użytkownik demo już istnieje')

        # Produkty
        products_data = [
            {'name': 'Laptop Dell Latitude 5520', 'barcode': '5901234123457', 'unit': 'szt.', 'code': 'PROD001', 'description': 'Laptop biznesowy 15.6" Intel i5, 8GB RAM, 256GB SSD'},
            {'name': 'Monitor LG 24ML600', 'barcode': '5901234123458', 'unit': 'szt.', 'code': 'PROD002', 'description': 'Monitor 24" Full HD, HDMI, VGA'},
            {'name': 'Klawiatura mechaniczna Logitech', 'barcode': '5901234123459', 'unit': 'szt.', 'code': 'PROD003', 'description': 'Klawiatura mechaniczna RGB, przełączniki Blue'},
            {'name': 'Mysz bezprzewodowa Microsoft', 'barcode': '5901234123460', 'unit': 'szt.', 'code': 'PROD004', 'description': 'Mysz bezprzewodowa Bluetooth, 6 przycisków'},
            {'name': 'Dysk SSD Samsung 500GB', 'barcode': '5901234123461', 'unit': 'szt.', 'code': 'PROD005', 'description': 'Dysk SSD 500GB, SATA III, 550MB/s'},
            {'name': 'Pamięć RAM DDR4 8GB', 'barcode': '5901234123462', 'unit': 'szt.', 'code': 'PROD006', 'description': 'Pamięć RAM DDR4 8GB 2666MHz'},
            {'name': 'Kamera internetowa Logitech C920', 'barcode': '5901234123463', 'unit': 'szt.', 'code': 'PROD007', 'description': 'Kamera internetowa Full HD 1080p'},
            {'name': 'Głośniki Creative Pebble', 'barcode': '5901234123464', 'unit': 'szt.', 'code': 'PROD008', 'description': 'Głośniki 2.0 USB, 4W'},
        ]
        
        products = []
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                barcode=product_data['barcode'],
                defaults=product_data
            )
            products.append(product)
            if created:
                self.stdout.write(f'✓ Utworzono produkt: {product.name}')

        # Lokalizacje
        locations_data = [
            {'name': 'Regał A, Rząd 1, Półka 1', 'barcode': 'LOC001'},
            {'name': 'Regał A, Rząd 1, Półka 2', 'barcode': 'LOC002'},
            {'name': 'Regał A, Rząd 2, Półka 1', 'barcode': 'LOC003'},
            {'name': 'Regał B, Rząd 1, Półka 1', 'barcode': 'LOC004'},
            {'name': 'Regał B, Rząd 1, Półka 2', 'barcode': 'LOC005'},
            {'name': 'Regał C, Rząd 1, Półka 1', 'barcode': 'LOC006'},
        ]
        
        locations = []
        for location_data in locations_data:
            location, created = Location.objects.get_or_create(
                barcode=location_data['barcode'],
                defaults=location_data
            )
            locations.append(location)
            if created:
                self.stdout.write(f'✓ Utworzono lokalizację: {location.name}')

        # Stany magazynowe
        stock_data = [
            {'product': products[0], 'location': locations[0], 'quantity': 5},
            {'product': products[0], 'location': locations[1], 'quantity': 3},
            {'product': products[1], 'location': locations[0], 'quantity': 8},
            {'product': products[1], 'location': locations[2], 'quantity': 4},
            {'product': products[2], 'location': locations[1], 'quantity': 12},
            {'product': products[3], 'location': locations[2], 'quantity': 15},
            {'product': products[4], 'location': locations[3], 'quantity': 6},
            {'product': products[5], 'location': locations[4], 'quantity': 10},
            {'product': products[6], 'location': locations[5], 'quantity': 7},
            {'product': products[7], 'location': locations[0], 'quantity': 9},
        ]
        
        for stock_data_item in stock_data:
            stock, created = Stock.objects.get_or_create(
                product=stock_data_item['product'],
                location=stock_data_item['location'],
                defaults={'quantity': stock_data_item['quantity']}
            )
            if created:
                self.stdout.write(f'✓ Utworzono stan: {stock.product.name} w {stock.location.name}')

        # Zamówienia klientów
        customers = ['Firma ABC Sp. z o.o.', 'Sklep XYZ', 'Biuro DEF', 'Warsztat GHI']
        
        for i, customer in enumerate(customers):
            order = CustomerOrder.objects.create(
                order_number=f'ZK-2024-{i+1:03d}',
                customer_name=customer,
                order_date=date.today() - timedelta(days=i*2),
                status='pending' if i < 2 else 'in_progress' if i == 2 else 'completed',
                total_value=0
            )
            
            # Dodaj pozycje do zamówienia
            for j, product in enumerate(products[i:i+3]):
                quantity = (i + 1) * (j + 1)
                unit_price = Decimal('100.00') + (j * Decimal('50.00'))  # Symulacja ceny
                total_price = unit_price * quantity
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
            
            # Oblicz wartość całkowitą
            order.total_value = sum(item.quantity * item.unit_price for item in order.items.all())
            order.save()
            
            self.stdout.write(f'✓ Utworzono zamówienie: {order.order_number}')

        # Zamówienia do dostawców (ZD)
        suppliers = [
            {'name': 'UPCERA Sp. z o.o.', 'code': 'UPCERA'},
            {'name': 'Zirconium Functional', 'code': 'ZIRCONIUM'},
            {'name': 'Tech Supplies Ltd.', 'code': 'TECHSUP'},
            {'name': 'Digital Solutions', 'code': 'DIGITAL'},
        ]
        
        supplier_orders = []
        for i, supplier in enumerate(suppliers):
            order = SupplierOrder.objects.create(
                order_number=f'ZD-2024-{i+1:03d}',
                supplier_name=supplier['name'],
                supplier_code=supplier['code'],
                order_date=date.today() - timedelta(days=i*3),
                expected_delivery_date=date.today() + timedelta(days=i*2),
                status='pending' if i < 2 else 'in_transit' if i == 2 else 'received',
                notes=f'Zamówienie testowe {i+1}'
            )
            
            # Dodaj pozycje do zamówienia
            for j, product in enumerate(products[i*2:(i+1)*2]):
                quantity = (i + 1) * 10
                unit_price = Decimal('80.00') + (j * Decimal('30.00'))  # Symulacja ceny zakupu
                SupplierOrderItem.objects.create(
                    supplier_order=order,
                    product=product,
                    quantity_ordered=quantity,
                    quantity_received=0 if i < 2 else quantity,
                    unit_price=unit_price
                )
            
            supplier_orders.append(order)
            self.stdout.write(f'✓ Utworzono ZD: {order.order_number}')

        # Rejestry przyjęć (Regalacja)
        for i, supplier_order in enumerate(supplier_orders[:2]):  # Tylko pierwsze 2 ZD
            receiving_order = ReceivingOrder.objects.create(
                order_number=f'Regalacja-{supplier_order.order_number}-{timezone.now().strftime("%Y%m%d%H%M")}',
                supplier_order=supplier_order,
                status='pending' if i == 0 else 'in_progress',
                assigned_to=user,
                started_at=timezone.now() if i == 1 else None
            )
            
            # Dodaj pozycje do Regalacji
            sequence = 1
            for supplier_item in supplier_order.items.all():
                ReceivingItem.objects.create(
                    receiving_order=receiving_order,
                    supplier_order_item=supplier_item,
                    product=supplier_item.product,
                    quantity_ordered=supplier_item.quantity_ordered,
                    quantity_received=0,
                    location=locations[i % len(locations)],
                    sequence=sequence
                )
                sequence += 1
            
            self.stdout.write(f'✓ Utworzono Regalację: {receiving_order.order_number}')

        self.stdout.write(self.style.SUCCESS('✓ Wszystkie dane demo zostały załadowane!'))
        self.stdout.write('Dane logowania: demo / demo123') 