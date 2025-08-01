from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import os


def user_avatar_path(instance, filename):
    """Generuje ścieżkę dla avatarów użytkowników"""
    ext = filename.split('.')[-1]
    filename = f'avatar_{instance.user.id}.{ext}'
    return f'avatars/{filename}'


class UserProfile(models.Model):
    """Profil użytkownika z dodatkowymi informacjami"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Użytkownik")
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True, verbose_name="Avatar")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    department = models.CharField(max_length=100, blank=True, verbose_name="Dział")
    position = models.CharField(max_length=100, blank=True, verbose_name="Stanowisko")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    
    class Meta:
        verbose_name = "Profil użytkownika"
        verbose_name_plural = "Profile użytkowników"
    
    def __str__(self):
        return f"Profil {self.user.username}"
    
    @property
    def full_name(self):
        """Zwraca pełne imię i nazwisko"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username
    
    @property
    def display_name(self):
        """Zwraca nazwę do wyświetlenia (imię i nazwisko lub username)"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username


class ProductGroup(models.Model):
    """Grupa produktów"""
    name = models.CharField(max_length=100, verbose_name="Nazwa grupy")
    code = models.CharField(max_length=20, unique=True, verbose_name="Kod grupy")
    description = models.TextField(blank=True, verbose_name="Opis")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Kolor")
    is_active = models.BooleanField(default=True, verbose_name="Aktywna")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    
    class Meta:
        verbose_name = "Grupa produktów"
        verbose_name_plural = "Grupy produktów"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def products_count(self):
        """Liczba produktów w grupie"""
        return self.products.count()


class Product(models.Model):
    """Produkt w magazynie"""
    code = models.CharField(max_length=50, unique=True, verbose_name="Kod produktu")
    name = models.CharField(max_length=200, verbose_name="Nazwa produktu")
    description = models.TextField(blank=True, verbose_name="Opis")
    barcode = models.CharField(max_length=100, unique=True, verbose_name="Kod kreskowy")
    unit = models.CharField(max_length=20, default="szt", verbose_name="Jednostka")
    
    # Grupa produktów (opcjonalna)
    groups = models.ManyToManyField(ProductGroup, blank=True,related_name='products', verbose_name="Grupy produktów")
    
    # Pola synchronizacji z Subiektem
    subiekt_id = models.IntegerField(null=True, blank=True, verbose_name="ID w Subiekcie/PLU")
    subiekt_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Stan w Subiekcie")
    subiekt_stock_reserved = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Stan zarezerwowany w Subiekcie")

    last_sync_date = models.DateTimeField(null=True, blank=True, verbose_name="Ostatnia synchronizacja")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def total_stock(self):
        """Łączny stan magazynowy we wszystkich lokalizacjach"""
        return Stock.objects.filter(product=self).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def stock_difference(self):
        """Różnica między stanem WMS a Subiektem"""
        return self.total_stock - self.subiekt_stock
    
    @property
    def needs_sync(self):
        """Czy produkt wymaga synchronizacji"""
        return abs(self.stock_difference) > 0.01  # Tolerancja 0.01


class Location(models.Model):
    """Lokalizacja w magazynie"""
    LOCATION_TYPES = [
        ('shelf', 'Półka'),
        ('rack', 'Regał'),
        ('zone', 'Strefa'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Kod lokalizacji")
    name = models.CharField(max_length=200, verbose_name="Nazwa lokalizacji")
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES, default='shelf')
    barcode = models.CharField(max_length=100, unique=True, verbose_name="Kod kreskowy lokalizacji")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Lokalizacja nadrzędna")
    description = models.TextField(blank=True, verbose_name="Opis")
    is_active = models.BooleanField(default=True, verbose_name="Aktywna")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lokalizacja"
        verbose_name_plural = "Lokalizacje"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Stock(models.Model):
    """Stan magazynowy produktu w lokalizacji"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produkt")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Lokalizacja")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ilość")
    reserved_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ilość zarezerwowana")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'location']
        verbose_name = "Stan magazynowy"
        verbose_name_plural = "Stany magazynowe"

    def __str__(self):
        return f"{self.product.name} w {self.location.name}: {self.quantity}"


class CustomerOrder(models.Model):
    """Zamówienie klienta (ZK) - symulacja z Subiekt GT"""
    ORDER_STATUS = [
        ('pending', 'Oczekujące'),
        ('in_progress', 'W kompletacji'),
        ('completed', 'Zrealizowane'),
        ('partially_completed', 'Częściowo zrealizowane'),
        ('cancelled', 'Anulowane'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name="Numer zamówienia")
    customer_name = models.CharField(max_length=200, verbose_name="Nazwa klienta")
    customer_address = models.TextField(verbose_name="Adres dostawy")
    order_date = models.DateTimeField(default=timezone.now, verbose_name="Data zamówienia")
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Wartość całkowita")
    notes = models.TextField(blank=True, verbose_name="Uwagi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zamówienie klienta"
        verbose_name_plural = "Zamówienia klientów"

    def __str__(self):
        return f"ZK {self.order_number} - {self.customer_name}"


class OrderItem(models.Model):
    """Pozycja w zamówieniu klienta"""
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items', verbose_name="Zamówienie")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produkt")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ilość zamówiona")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena jednostkowa")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena całkowita")
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ilość zrealizowana")

    class Meta:
        verbose_name = "Pozycja zamówienia"
        verbose_name_plural = "Pozycje zamówienia"

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class PickingOrder(models.Model):
    """Zlecenie kompletacji (RegOut)"""
    PICKING_STATUS = [
        ('created', 'Utworzone'),
        ('in_progress', 'W trakcie'),
        ('completed', 'Zakończone'),
        ('cancelled', 'Anulowane'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True, verbose_name="Numer zlecenia")
    customer_order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, verbose_name="Zamówienie klienta")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Przypisane do")
    status = models.CharField(max_length=20, choices=PICKING_STATUS, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Rozpoczęto")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Zakończono")
    notes = models.TextField(blank=True, verbose_name="Uwagi")

    class Meta:
        verbose_name = "Zlecenie kompletacji"
        verbose_name_plural = "Zlecenia kompletacji"

    def __str__(self):
        return f"RegOut {self.order_number} - {self.customer_order.customer_name}"

    @property
    def completed_items_count(self):
        """Liczba zakończonych pozycji"""
        return self.items.filter(is_completed=True).count()
    
    @property
    def total_items_count(self):
        """Całkowita liczba pozycji"""
        return self.items.count()
    
    @property
    def pending_items_count(self):
        """Liczba nieukończonych pozycji"""
        return self.items.filter(is_completed=False).count()
    
    @property
    def pending_items(self):
        """Nieukończone pozycje"""
        return self.items.filter(is_completed=False)
    
    @property
    def completed_items(self):
        """Ukończone pozycje"""
        return self.items.filter(is_completed=True)
    
    @property
    def next_item(self):
        """Następna pozycja do kompletacji"""
        return self.items.filter(is_completed=False).order_by('sequence').first()
    
    @property
    def progress_percentage(self):
        """Procent ukończenia (0-100)"""
        if self.total_items_count == 0:
            return 0
        return int((self.completed_items_count / self.total_items_count) * 100)


class PickingItem(models.Model):
    """Pozycja w zleceniu kompletacji"""
    picking_order = models.ForeignKey(PickingOrder, on_delete=models.CASCADE, related_name='items', verbose_name="Zlecenie kompletacji")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, verbose_name="Pozycja zamówienia")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produkt")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Lokalizacja")
    quantity_to_pick = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ilość do pobrania")
    quantity_picked = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ilość pobrana")
    is_completed = models.BooleanField(default=False, verbose_name="Zakończone")
    sequence = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Pozycja kompletacji"
        verbose_name_plural = "Pozycje kompletacji"

    def __str__(self):
        return f"{self.product.name} - {self.quantity_to_pick} z {self.location.name}"


class PickingHistory(models.Model):
    """Historia kompletacji - śledzenie każdego skanowania"""
    picking_item = models.ForeignKey(PickingItem, on_delete=models.CASCADE, verbose_name="Pozycja kompletacji")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Użytkownik")
    location_scanned = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="Zeskanowana lokalizacja")
    product_scanned = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Zeskanowany produkt")
    quantity_picked = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ilość pobrana")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="Czas skanowania")
    notes = models.TextField(blank=True, verbose_name="Uwagi")

    class Meta:
        verbose_name = "Historia kompletacji"
        verbose_name_plural = "Historia kompletacji"

    def __str__(self):
        return f"{self.product_scanned.name} - {self.quantity_picked} - {self.scanned_at}"


class SupplierOrder(models.Model):
    """Zamówienie do dostawcy (ZD)"""
    SUPPLIER_STATUS_CHOICES = [
        ('pending', 'Oczekujące'),
        ('confirmed', 'Potwierdzone'),
        ('in_transit', 'W transporcie'),
        ('received', 'Przyjęte'),
        ('partially_received', 'Częściowo przyjęte'),
        ('cancelled', 'Anulowane'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    supplier_name = models.CharField(max_length=200)
    supplier_code = models.CharField(max_length=50, blank=True)
    order_date = models.DateField()
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SUPPLIER_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date']
    
    def __str__(self):
        return f"ZD {self.order_number} - {self.supplier_name}"
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def received_items(self):
        return self.items.filter(quantity_received__gt=0).count()
    
    @property
    def is_fully_received(self):
        return self.received_items == self.total_items and self.total_items > 0


class SupplierOrderItem(models.Model):
    """Pozycje zamówienia do dostawcy"""
    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        unique_together = ['supplier_order', 'product']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_ordered} szt."
    
    @property
    def total_value(self):
        return self.quantity_ordered * self.unit_price


class ReceivingOrder(models.Model):
    """Rejestr przyjęć (RegIn)"""
    RECEIVING_STATUS_CHOICES = [
        ('pending', 'Oczekujące'),
        ('in_progress', 'W trakcie'),
        ('completed', 'Zakończone'),
        ('cancelled', 'Anulowane'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name='receiving_orders')
    status = models.CharField(max_length=20, choices=RECEIVING_STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"RegIn {self.order_number} - {self.supplier_order.supplier_name}"
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def received_items(self):
        return self.items.filter(quantity_received__gt=0).count()


class ReceivingItem(models.Model):
    """Pozycje rejestru przyjęć"""
    receiving_order = models.ForeignKey(ReceivingOrder, on_delete=models.CASCADE, related_name='items')
    supplier_order_item = models.ForeignKey(SupplierOrderItem, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    sequence = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['sequence']
        unique_together = ['receiving_order', 'supplier_order_item']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_received}/{self.quantity_ordered}"


class ReceivingHistory(models.Model):
    """Historia skanowań przy przyjmowaniu"""
    receiving_order = models.ForeignKey(ReceivingOrder, on_delete=models.CASCADE, related_name='history')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    scanned_by = models.ForeignKey(User, on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-scanned_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_received} w {self.location.name}"


class WarehouseDocument(models.Model):
    """Dokument magazynowy (PZ)"""
    DOCUMENT_TYPE_CHOICES = [
        ('PZ', 'Przyjęcie zewnętrzne'),
        ('WZ', 'Wydanie zewnętrzne'),
        ('MM', 'Przesunięcie międzymagazynowe'),
    ]
    
    document_number = models.CharField(max_length=50, unique=True)
    document_type = models.CharField(max_length=2, choices=DOCUMENT_TYPE_CHOICES)
    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, null=True, blank=True)
    customer_order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, null=True, blank=True)
    document_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-document_date']
    
    def __str__(self):
        return f"{self.document_type} {self.document_number}"


class DocumentItem(models.Model):
    """Pozycje dokumentu magazynowego"""
    document = models.ForeignKey(WarehouseDocument, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    class Meta:
        unique_together = ['document', 'product', 'location']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} w {self.location.name}"
