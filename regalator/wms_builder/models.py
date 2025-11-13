from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal


class Warehouse(models.Model):
    """Main warehouse container"""
    name = models.CharField(max_length=200, verbose_name="Nazwa magazynu")
    description = models.TextField(blank=True, verbose_name="Opis")
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1000.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Szerokość (jednostki)"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1000.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Wysokość (jednostki)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utworzył"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    class Meta:
        verbose_name = "Magazyn"
        verbose_name_plural = "Magazyny"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WarehouseZone(models.Model):
    """Strefa - top-level areas in warehouse"""
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='zones',
        verbose_name="Magazyn"
    )
    name = models.CharField(max_length=200, verbose_name="Nazwa strefy")
    x = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Pozycja X"
    )
    y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Pozycja Y"
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('200.00'),
        validators=[MinValueValidator(Decimal('50.00'))],
        verbose_name="Szerokość"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('150.00'),
        validators=[MinValueValidator(Decimal('50.00'))],
        verbose_name="Wysokość"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name="Kolor"
    )
    location = models.OneToOneField(
        'wms.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_zone',
        verbose_name="Lokalizacja WMS"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    class Meta:
        verbose_name = "Strefa"
        verbose_name_plural = "Strefy"
        ordering = ['name']

    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"
    
    def is_location_empty(self):
        """Sprawdza czy powiązana Location jest pusta (nie ma powiązań)"""
        if not self.location:
            return True
        
        from wms.models import Stock, StockMovement, PickingHistory, ReceivingHistory, DocumentItem, Location
        
        # Sprawdź wszystkie powiązania
        has_stock = Stock.objects.filter(location=self.location).exists()
        has_movements = StockMovement.objects.filter(
            Q(source_location=self.location) | Q(target_location=self.location)
        ).exists()
        has_picking_history = PickingHistory.objects.filter(location_scanned=self.location).exists()
        has_receiving_history = ReceivingHistory.objects.filter(location=self.location).exists()
        has_document_items = DocumentItem.objects.filter(location=self.location).exists()
        has_children = Location.objects.filter(parent=self.location).exists()
        
        return not any([
            has_stock,
            has_movements,
            has_picking_history,
            has_receiving_history,
            has_document_items,
            has_children
        ])
    
    def can_delete(self):
        """Sprawdza czy można usunąć strefę (Location musi być pusta)"""
        if not self.location:
            return True
        return self.is_location_empty()
    
    def sync_to_location(self, barcode):
        """Synchronizuje strefę do Location w WMS"""
        from wms.models import Location
        
        if not barcode:
            raise ValueError("Barcode jest wymagany")
        
        # Sprawdź czy barcode już istnieje
        existing_location = Location.objects.filter(barcode=barcode).first()
        if existing_location and existing_location != self.location:
            raise ValueError(f"Barcode '{barcode}' jest już używany przez inną lokalizację")
        
        if self.location:
            # Aktualizacja istniejącej Location
            self.location.name = self.name
            self.location.barcode = barcode
            self.location.location_type = 'zone'
            self.location.parent = None  # Strefy nie mają parent
            self.location.description = f"Strefa z buildera: {self.name}"
            self.location.save()
        else:
            # Tworzenie nowej Location
            self.location = Location.objects.create(
                name=self.name,
                location_type='zone',
                barcode=barcode,
                parent=None,
                description=f"Strefa z buildera: {self.name}"
            )
            self.save(update_fields=['location'])
        
        return self.location
    
    def delete(self, *args, **kwargs):
        """Usuwa strefę, sprawdzając czy Location jest pusta"""
        if self.location:
            if not self.is_location_empty():
                raise ValidationError(
                    f"Nie można usunąć strefy '{self.name}' - powiązana lokalizacja '{self.location.name}' "
                    f"ma powiązania z innymi obiektami (Stock, StockMovement, PickingHistory, itp.)"
                )
            # Usuń Location jeśli jest pusta
            self.location.delete()
        super().delete(*args, **kwargs)


class WarehouseRack(models.Model):
    """Regał - racks within zones"""
    zone = models.ForeignKey(
        WarehouseZone,
        on_delete=models.CASCADE,
        related_name='racks',
        verbose_name="Strefa"
    )
    name = models.CharField(max_length=200, verbose_name="Nazwa regału")
    x = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Pozycja X"
    )
    y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Pozycja Y"
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('80.00'),
        validators=[MinValueValidator(Decimal('20.00'))],
        verbose_name="Szerokość"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('60.00'),
        validators=[MinValueValidator(Decimal('20.00'))],
        verbose_name="Wysokość"
    )
    color = models.CharField(
        max_length=7,
        default='#28a745',
        verbose_name="Kolor"
    )
    location = models.OneToOneField(
        'wms.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_rack',
        verbose_name="Lokalizacja WMS"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    class Meta:
        verbose_name = "Regał"
        verbose_name_plural = "Regały"
        ordering = ['name']

    def __str__(self):
        return f"{self.zone.name} - {self.name}"
    
    def is_location_empty(self):
        """Sprawdza czy powiązana Location jest pusta (nie ma powiązań)"""
        if not self.location:
            return True
        
        from wms.models import Stock, StockMovement, PickingHistory, ReceivingHistory, DocumentItem, Location
        
        # Sprawdź wszystkie powiązania
        has_stock = Stock.objects.filter(location=self.location).exists()
        has_movements = StockMovement.objects.filter(
            Q(source_location=self.location) | Q(target_location=self.location)
        ).exists()
        has_picking_history = PickingHistory.objects.filter(location_scanned=self.location).exists()
        has_receiving_history = ReceivingHistory.objects.filter(location=self.location).exists()
        has_document_items = DocumentItem.objects.filter(location=self.location).exists()
        has_children = Location.objects.filter(parent=self.location).exists()
        
        return not any([
            has_stock,
            has_movements,
            has_picking_history,
            has_receiving_history,
            has_document_items,
            has_children
        ])
    
    def can_delete(self):
        """Sprawdza czy można usunąć regał (Location musi być pusta)"""
        if not self.location:
            return True
        return self.is_location_empty()
    
    def sync_to_location(self, barcode):
        """Synchronizuje regał do Location w WMS"""
        from wms.models import Location
        
        if not barcode:
            raise ValueError("Barcode jest wymagany")
        
        # Sprawdź czy barcode już istnieje
        existing_location = Location.objects.filter(barcode=barcode).first()
        if existing_location and existing_location != self.location:
            raise ValueError(f"Barcode '{barcode}' jest już używany przez inną lokalizację")
        
        # Określ parent (strefa jeśli ma Location)
        parent_location = None
        if self.zone.location:
            parent_location = self.zone.location
        
        if self.location:
            # Aktualizacja istniejącej Location
            self.location.name = self.name
            self.location.barcode = barcode
            self.location.location_type = 'rack'
            self.location.parent = parent_location
            self.location.description = f"Regał z buildera: {self.name}"
            self.location.save()
        else:
            # Tworzenie nowej Location
            self.location = Location.objects.create(
                name=self.name,
                location_type='rack',
                barcode=barcode,
                parent=parent_location,
                description=f"Regał z buildera: {self.name}"
            )
            self.save(update_fields=['location'])
        
        return self.location
    
    def delete(self, *args, **kwargs):
        """Usuwa regał, sprawdzając czy Location jest pusta"""
        if self.location:
            if not self.is_location_empty():
                raise ValidationError(
                    f"Nie można usunąć regału '{self.name}' - powiązana lokalizacja '{self.location.name}' "
                    f"ma powiązania z innymi obiektami (Stock, StockMovement, PickingHistory, itp.)"
                )
            # Usuń Location jeśli jest pusta
            self.location.delete()
        super().delete(*args, **kwargs)


class WarehouseShelf(models.Model):
    """Półka - shelves within racks"""
    rack = models.ForeignKey(
        WarehouseRack,
        on_delete=models.CASCADE,
        related_name='shelves',
        verbose_name="Regał"
    )
    name = models.CharField(max_length=200, verbose_name="Nazwa półki")
    x = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Pozycja X"
    )
    y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Pozycja Y"
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('60.00'),
        validators=[MinValueValidator(Decimal('15.00'))],
        verbose_name="Szerokość"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(Decimal('10.00'))],
        verbose_name="Wysokość"
    )
    color = models.CharField(
        max_length=7,
        default='#ffc107',
        verbose_name="Kolor"
    )
    location = models.OneToOneField(
        'wms.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='warehouse_shelf',
        verbose_name="Lokalizacja WMS"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")

    class Meta:
        verbose_name = "Półka"
        verbose_name_plural = "Półki"
        ordering = ['name']

    def __str__(self):
        return f"{self.rack.name} - {self.name}"
    
    def is_location_empty(self):
        """Sprawdza czy powiązana Location jest pusta (nie ma powiązań)"""
        if not self.location:
            return True
        
        from wms.models import Stock, StockMovement, PickingHistory, ReceivingHistory, DocumentItem, Location
        
        # Sprawdź wszystkie powiązania
        has_stock = Stock.objects.filter(location=self.location).exists()
        has_movements = StockMovement.objects.filter(
            Q(source_location=self.location) | Q(target_location=self.location)
        ).exists()
        has_picking_history = PickingHistory.objects.filter(location_scanned=self.location).exists()
        has_receiving_history = ReceivingHistory.objects.filter(location=self.location).exists()
        has_document_items = DocumentItem.objects.filter(location=self.location).exists()
        has_children = Location.objects.filter(parent=self.location).exists()
        
        return not any([
            has_stock,
            has_movements,
            has_picking_history,
            has_receiving_history,
            has_document_items,
            has_children
        ])
    
    def can_delete(self):
        """Sprawdza czy można usunąć półkę (Location musi być pusta)"""
        if not self.location:
            return True
        return self.is_location_empty()
    
    def sync_to_location(self, barcode):
        """Synchronizuje półkę do Location w WMS"""
        from wms.models import Location
        
        if not barcode:
            raise ValueError("Barcode jest wymagany")
        
        # Sprawdź czy barcode już istnieje
        existing_location = Location.objects.filter(barcode=barcode).first()
        if existing_location and existing_location != self.location:
            raise ValueError(f"Barcode '{barcode}' jest już używany przez inną lokalizację")
        
        # Określ parent (regał jeśli ma Location, w przeciwnym razie strefa)
        parent_location = None
        if self.rack.location:
            parent_location = self.rack.location
        elif self.rack.zone.location:
            parent_location = self.rack.zone.location
        
        if self.location:
            # Aktualizacja istniejącej Location
            self.location.name = self.name
            self.location.barcode = barcode
            self.location.location_type = 'shelf'
            self.location.parent = parent_location
            self.location.description = f"Półka z buildera: {self.name}"
            self.location.save()
        else:
            # Tworzenie nowej Location
            self.location = Location.objects.create(
                name=self.name,
                location_type='shelf',
                barcode=barcode,
                parent=parent_location,
                description=f"Półka z buildera: {self.name}"
            )
            self.save(update_fields=['location'])
        
        return self.location
    
    def delete(self, *args, **kwargs):
        """Usuwa półkę, sprawdzając czy Location jest pusta"""
        if self.location:
            if not self.is_location_empty():
                raise ValidationError(
                    f"Nie można usunąć półki '{self.name}' - powiązana lokalizacja '{self.location.name}' "
                    f"ma powiązania z innymi obiektami (Stock, StockMovement, PickingHistory, itp.)"
                )
            # Usuń Location jeśli jest pusta
            self.location.delete()
        super().delete(*args, **kwargs)

