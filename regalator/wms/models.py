from django.db import models
from django.db.models import JSONField
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


def location_image_path(instance, filename):
    """Generuje ścieżkę dla zdjęć lokalizacji"""
    ext = filename.split('.')[-1]
    filename = f'location_{instance.location.barcode}_{instance.id}.{ext}'
    return f'locations/{filename}'


def product_image_path(instance, filename):
    """Generuje ścieżkę dla zdjęć produktów"""
    ext = filename.split('.')[-1]
    filename = f'product_{instance.product.code}_{instance.id}.{ext}'
    return f'products/{filename}'


class UserProfile(models.Model):
    """Profil użytkownika z dodatkowymi informacjami"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Użytkownik")
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True, verbose_name="Avatar")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    department = models.CharField(max_length=100, blank=True, verbose_name="Dział")
    position = models.CharField(max_length=100, blank=True, verbose_name="Stanowisko")
    password_changed = models.BooleanField(default=False, verbose_name="Hasło zmienione")
    gt_user_id = models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name="ID użytkownika GT")
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


class ProductCode(models.Model):
    """Kody produktów (barcodes, QR codes)"""
    CODE_TYPES = [
        ('barcode', 'Kod kreskowy'),
        ('qr', 'Kod QR'),
        ('ean13', 'EAN-13'),
        ('ean8', 'EAN-8'),
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('other', 'Inny'),
    ]
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='codes', verbose_name="Produkt")
    code = models.CharField(max_length=200, unique=True, verbose_name="Kod")
    code_type = models.CharField(max_length=20, choices=CODE_TYPES, default='barcode', verbose_name="Typ kodu")
    description = models.CharField(max_length=200, blank=True, verbose_name="Opis")
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    
    class Meta:
        verbose_name = "Kod produktu"
        verbose_name_plural = "Kody produktów"
        ordering = ['code_type', 'code']
        unique_together = ['product', 'code']
    
    def __str__(self):
        return f"{self.get_code_type_display()}: {self.code}"
    


class Product(models.Model):
    """Produkt w magazynie"""
    code = models.CharField(max_length=50, unique=True, verbose_name="Kod produktu")
    name = models.CharField(max_length=200, verbose_name="Nazwa produktu")
    description = models.TextField(blank=True, verbose_name="Opis")
    unit = models.CharField(max_length=20, default="szt", verbose_name="Jednostka")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Produkt nadrzędny")
    variants = JSONField(default={'size': '', 'color': ''}, verbose_name="Warianty produktu")
    
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
    def all_barcodes(self):
        """Wszystkie kody kreskowe produktu"""
        return self.codes.filter(code_type='barcode', is_active=True)
    
    @property
    def all_qr_codes(self):
        """Wszystkie kody QR produktu"""
        return self.codes.filter(code_type='qr', is_active=True)
    
    @property
    def primary_barcode(self):
        """Zwraca domyślny kod kreskowy (aktywny)"""
        return self.codes.filter(code_type='barcode', is_active=True).first()
    
    @property
    def total_stock(self):
        """Łączny stan magazynowy we wszystkich lokalizacjach (włącznie z produktami potomnymi)"""
        # Get all child products
        child_products = Product.objects.filter(parent=self)
        
        # Get stock for this product and all child products
        product_ids = [self.id] + list(child_products.values_list('id', flat=True))
        
        return Stock.objects.filter(product_id__in=product_ids).aggregate(
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
    
    @classmethod
    def find_by_code(cls, value):
        """
        Znajduje produkt po kodzie kreskowym / QR, kodzie systemowym
        lub nazwie (dokładne dopasowanie, ignorując wielkość liter).
        """
        if not value:
            return None

        value = value.strip()
        if not value:
            return None

        # 1. Sprawdź aktywne kody w tabeli ProductCode
        match = cls.objects.filter(codes__code=value, codes__is_active=True).first()
        if match:
            return match

        # 2. Sprawdź kody systemowe (np. symbol z Subiekta)
        try:
            return cls.objects.get(code__iexact=value)
        except cls.DoesNotExist:
            pass

        # 3. Sprawdź po nazwie produktu
        return cls.objects.filter(name__iexact=value).first()
    
    @classmethod
    def find_by_any_code(cls, code):
        """Znajduje produkt po dowolnym kodzie (barcode, QR, etc.)"""
        return cls.find_by_code(code)
    
    @property
    def primary_photo(self):
        """Returns the primary photo for this product"""
        return self.images.filter(is_primary=True).first()


class Location(models.Model):
    """Lokalizacja w magazynie"""
    LOCATION_TYPES = [
        ('shelf', 'Półka'),
        ('rack', 'Regał'),
        ('zone', 'Strefa'),
    ]
    
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
        return f"{self.name}, {self.get_location_type_display()}"
    
    @property
    def primary_photo(self):
        """Returns the primary photo for this location"""
        return self.images.filter(is_primary=True).first()


class LocationImage(models.Model):
    """Zdjęcia lokalizacji w magazynie"""
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='images', verbose_name="Lokalizacja")
    image = models.ImageField(upload_to=location_image_path, verbose_name="Zdjęcie")
    title = models.CharField(max_length=200, blank=True, verbose_name="Tytuł")
    description = models.TextField(blank=True, verbose_name="Opis")
    is_primary = models.BooleanField(default=False, verbose_name="Zdjęcie główne")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    
    class Meta:
        verbose_name = "Zdjęcie lokalizacji"
        verbose_name_plural = "Zdjęcia lokalizacji"
        ordering = ['location', 'is_primary', 'order', 'created_at']
    
    def __str__(self):
        if self.title:
            return f"{self.location.barcode} - {self.title}"
        return f"{self.location.barcode} - Zdjęcie {self.id}"
    
    def save(self, *args, **kwargs):
        # Jeśli to zdjęcie jest oznaczone jako główne, odznacz inne zdjęcia tej lokalizacji
        if self.is_primary:
            LocationImage.objects.filter(location=self.location, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Zdjęcia produktów"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Produkt")
    image = models.ImageField(upload_to=product_image_path, verbose_name="Zdjęcie")
    description = models.TextField(blank=True, verbose_name="Opis")
    is_primary = models.BooleanField(default=False, verbose_name="Zdjęcie główne")
    order = models.PositiveIntegerField(default=0, verbose_name="Kolejność")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    
    class Meta:
        verbose_name = "Zdjęcie produktu"
        verbose_name_plural = "Zdjęcia produktów"
        ordering = ['product', 'is_primary', 'order', 'created_at']
    
    def __str__(self):
        if self.description:
            return f"{self.product.code} - {self.description}"
        return f"{self.product.code} - Zdjęcie {self.id}"
    
    def save(self, *args, **kwargs):
        # Jeśli to zdjęcie jest oznaczone jako główne, odznacz inne zdjęcia tego produktu
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


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
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena całkowita")
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Ilość zrealizowana")

    class Meta:
        verbose_name = "Pozycja zamówienia"
        verbose_name_plural = "Pozycje zamówienia"

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class PickingOrder(models.Model):
    """Zlecenie kompletacji (Terminacja)"""
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
        return f"Terminacja {self.order_number} - {self.customer_order.customer_name}"

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
        ('in_receiving', 'W regalacji'),
        ('received', 'Przyjęte'),
        ('partially_received', 'Częściowo przyjęte'),
        ('cancelled', 'Anulowane'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    document_number = models.IntegerField(null=True, blank=True, verbose_name="Oryginalny numer dokumentu", help_text="Oryginalny numer dokumentu z Subiektu")
    document_id = models.IntegerField(null=True, blank=True, verbose_name="ID dokumentu", help_text="ID dokumentu z Subiektu (dok_Id)")
    supplier_name = models.CharField(max_length=200)
    supplier_code = models.CharField(max_length=50, blank=True)
    order_date = models.DateField()
    expected_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SUPPLIER_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    is_new = models.BooleanField(default=False, help_text="Oznacza nowo załadowane zamówienie z Subiektu")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-document_number']
    
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

    @property
    def has_active_receiving(self):
        """Czy istnieją regalacje w trakcie realizacji."""
        return self.receiving_orders.filter(status__in=['pending', 'in_progress']).exists()

    @property
    def has_any_receiving(self):
        """Czy istnieje jakakolwiek regalacja powiązana z tym ZD."""
        return self.receiving_orders.exists()

    @property
    def active_receiving_assignment(self):
        """Zwraca użytkownika przypisanego do aktywnej regalacji (pending/in_progress)."""
        active_order = self.receiving_orders.filter(
            status__in=['pending', 'in_progress']
        ).select_related('assigned_to').first()
        if active_order and active_order.assigned_to:
            return active_order.assigned_to
        return None

    @property
    def active_receiving(self):
        """Zwraca aktywną regalację (pending/in_progress) lub None."""
        return self.receiving_orders.filter(status__in=['pending', 'in_progress']).order_by('id').first()

    @property
    def last_receiving(self):
        """Zwraca ostatnią regalację powiązaną z ZD (dowolny status) lub None."""
        return self.receiving_orders.order_by('-created_at').first()


class SupplierOrderItem(models.Model):
    """Pozycje zamówienia do dostawcy"""
    supplier_order = models.ForeignKey(SupplierOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))])
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        unique_together = ['supplier_order', 'product']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity_ordered} szt."


class ReceivingOrder(models.Model):
    """Rejestr przyjęć (Regalacja)"""
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
        return f"Regalacja {self.order_number} - {self.supplier_order.supplier_name}"
    
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
    
    class Meta:
        unique_together = ['document', 'product', 'location']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} w {self.location.name}"
