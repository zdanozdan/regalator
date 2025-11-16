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
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Szerokość"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('150.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
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
    
    def sync_to_location(self, barcode, sync_children=True, _syncing=False):
        """Synchronizuje strefę do Location w WMS oraz wszystkie regały i półki w strefie
        
        Args:
            barcode: Kod kreskowy dla Location
            sync_children: Jeśli True, automatycznie synchronizuje wszystkie regały i półki w strefie
            _syncing: Flaga wewnętrzna zapobiegająca cyklicznym wywołaniom
        """
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
        
        # Synchronizuj wszystkie regały w strefie (automatycznie generuj barcode jeśli nie są zsynchronizowane)
        if sync_children and not _syncing:
            for rack in self.racks.all():
                if not rack.location:
                    # Generuj barcode dla regału na podstawie strefy i ID regału
                    rack_barcode = f"{barcode}-R{rack.id}"
                    rack.sync_to_location(rack_barcode, sync_children=True, _syncing=True)
                else:
                    # Zaktualizuj parent jeśli regał już jest zsynchronizowany
                    rack.location.parent = self.location
                    rack.location.save(update_fields=['parent'])
                
                # Synchronizuj wszystkie półki w regale (jeśli regał jest zsynchronizowany)
                if rack.location:
                    for shelf in rack.shelves.all():
                        if not shelf.location:
                            # Generuj barcode dla półki
                            shelf_barcode = f"{rack.location.barcode}-S{shelf.id}"
                            shelf.sync_to_location(shelf_barcode, _syncing=True)
                        else:
                            # Zaktualizuj parent jeśli półka już jest zsynchronizowana
                            shelf.location.parent = rack.location
                            shelf.location.save(update_fields=['parent'])
        
        return self.location
    
    def delete(self, *args, **kwargs):
        """Usuwa strefę, sprawdzając czy Location jest pusta"""
        deleted_items = kwargs.pop('deleted_items', None)  # Lista do zbierania informacji o usuniętych elementach
        
        if self.location:
            # Jeśli Location jest już w trakcie usuwania, po prostu odłącz relację
            if hasattr(self.location, '_deleting_from_builder') and self.location._deleting_from_builder:
                self.location = None
                self.save(update_fields=['location'])
            else:
                from wms.models import Location, Stock, StockMovement, PickingHistory, ReceivingHistory, DocumentItem
                
                # Najpierw usuń Location dla wszystkich półek i regałów w strefie
                # (child locations blokują usunięcie Location strefy)
                # Nie dodawaj ich do deleted_items tutaj - zostaną dodane podczas usuwania samych elementów
                for rack in self.racks.all():
                    # Usuń Location dla wszystkich półek w regale
                    for shelf in rack.shelves.all():
                        if shelf.location:
                            # Sprawdź czy Location półki nie ma innych powiązań
                            has_other_relations = any([
                                Stock.objects.filter(location=shelf.location).exists(),
                                StockMovement.objects.filter(
                                    Q(source_location=shelf.location) | Q(target_location=shelf.location)
                                ).exists(),
                                PickingHistory.objects.filter(location_scanned=shelf.location).exists(),
                                ReceivingHistory.objects.filter(location=shelf.location).exists(),
                                DocumentItem.objects.filter(location=shelf.location).exists(),
                                Location.objects.filter(parent=shelf.location).exists()
                            ])
                            if not has_other_relations:
                                shelf.location._deleting_from_builder = True
                                shelf.location.delete()
                    
                    # Usuń Location dla regału (jeśli nie ma innych powiązań poza child locations)
                    if rack.location:
                        has_other_relations = any([
                            Stock.objects.filter(location=rack.location).exists(),
                            StockMovement.objects.filter(
                                Q(source_location=rack.location) | Q(target_location=rack.location)
                            ).exists(),
                            PickingHistory.objects.filter(location_scanned=rack.location).exists(),
                            ReceivingHistory.objects.filter(location=rack.location).exists(),
                            DocumentItem.objects.filter(location=rack.location).exists(),
                            # Child locations już usunęliśmy powyżej
                        ])
                        if not has_other_relations:
                            rack.location._deleting_from_builder = True
                            rack.location.delete()
                
                # Teraz sprawdź czy Location strefy jest pusta
                if not self.is_location_empty():
                    raise ValidationError(
                        f"Nie można usunąć strefy '{self.name}' - powiązana lokalizacja '{self.location.name}' "
                        f"ma powiązania z innymi obiektami (Stock, StockMovement, PickingHistory, itp.)"
                    )
                # Oznacz Location że jest usuwane z powodu usuwania elementu buildera
                # (zapobiega cyklicznemu usuwaniu w sygnale)
                self.location._deleting_from_builder = True
                # Usuń Location jeśli jest pusta
                location_name = self.location.name
                self.location.delete()
                if deleted_items is not None:
                    deleted_items.append({'type': 'zone_location', 'name': location_name})
        
        # Ręcznie usuń wszystkie regały (aby ich metody delete() były wywoływane i zbierały deleted_items)
        # Zamiast polegać na CASCADE, który nie wywołuje metody delete()
        # Location dla regałów i półek są już usunięte powyżej, więc metody delete() nie będą próbowały usuwać Location ponownie
        racks_to_delete = list(self.racks.all())
        for rack in racks_to_delete:
            rack.delete(deleted_items=deleted_items)
        
        zone_name = self.name
        super().delete(*args, **kwargs)
        if deleted_items is not None:
            deleted_items.append({'type': 'zone', 'name': zone_name})


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
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Szerokość"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('60.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
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
    
    def sync_to_location(self, barcode, sync_children=True, _syncing=False):
        """Synchronizuje regał do Location w WMS oraz nadrzędną strefę jeśli nie jest zsynchronizowana
        
        Args:
            barcode: Kod kreskowy dla Location
            sync_children: Jeśli True, automatycznie synchronizuje wszystkie półki w regale
            _syncing: Flaga wewnętrzna zapobiegająca cyklicznym wywołaniom
        """
        from wms.models import Location
        
        if not barcode:
            raise ValueError("Barcode jest wymagany")
        
        # Sprawdź czy barcode już istnieje
        existing_location = Location.objects.filter(barcode=barcode).first()
        if existing_location and existing_location != self.location:
            raise ValueError(f"Barcode '{barcode}' jest już używany przez inną lokalizację")
        
        # Synchronizuj nadrzędną strefę jeśli nie jest zsynchronizowana (bez synchronizacji dzieci, aby uniknąć rekurencji)
        if not self.zone.location and not _syncing:
            # Generuj barcode dla strefy na podstawie nazwy strefy lub ID
            zone_barcode = f"ZONE-{self.zone.id}"
            self.zone.sync_to_location(zone_barcode, sync_children=False, _syncing=True)
        
        # Określ parent (strefa powinna mieć Location po synchronizacji powyżej)
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
        
        # Synchronizuj wszystkie półki w regale (automatycznie generuj barcode jeśli nie są zsynchronizowane)
        if sync_children and not _syncing:
            for shelf in self.shelves.all():
                if not shelf.location:
                    # Generuj barcode dla półki
                    shelf_barcode = f"{barcode}-S{shelf.id}"
                    shelf.sync_to_location(shelf_barcode, _syncing=True)
                else:
                    # Zaktualizuj parent jeśli półka już jest zsynchronizowana
                    shelf.location.parent = self.location
                    shelf.location.save(update_fields=['parent'])
        
        return self.location
    
    def delete(self, *args, **kwargs):
        """Usuwa regał, sprawdzając czy Location jest pusta"""
        deleted_items = kwargs.pop('deleted_items', None)  # Lista do zbierania informacji o usuniętych elementach
        
        if self.location:
            # Jeśli Location jest już w trakcie usuwania, po prostu odłącz relację
            if hasattr(self.location, '_deleting_from_builder') and self.location._deleting_from_builder:
                self.location = None
                self.save(update_fields=['location'])
            else:
                from wms.models import Stock, StockMovement, PickingHistory, ReceivingHistory, DocumentItem, Location
                
                # Najpierw usuń Location dla wszystkich półek w regale
                # (child locations blokują usunięcie Location regału)
                # Nie dodawaj ich do deleted_items tutaj - zostaną dodane podczas usuwania samych półek
                for shelf in self.shelves.all():
                    if shelf.location:
                        # Sprawdź czy Location półki nie ma innych powiązań
                        has_other_relations = any([
                            Stock.objects.filter(location=shelf.location).exists(),
                            StockMovement.objects.filter(
                                Q(source_location=shelf.location) | Q(target_location=shelf.location)
                            ).exists(),
                            PickingHistory.objects.filter(location_scanned=shelf.location).exists(),
                            ReceivingHistory.objects.filter(location=shelf.location).exists(),
                            DocumentItem.objects.filter(location=shelf.location).exists(),
                            Location.objects.filter(parent=shelf.location).exists()
                        ])
                        if not has_other_relations:
                            shelf.location._deleting_from_builder = True
                            shelf.location.delete()
                
                # Teraz sprawdź czy Location regału jest pusta
                if not self.is_location_empty():
                    raise ValidationError(
                        f"Nie można usunąć regału '{self.name}' - powiązana lokalizacja '{self.location.name}' "
                        f"ma powiązania z innymi obiektami (Stock, StockMovement, PickingHistory, itp.)"
                    )
                # Oznacz Location że jest usuwane z powodu usuwania elementu buildera
                # (zapobiega cyklicznemu usuwaniu w sygnale)
                self.location._deleting_from_builder = True
                # Usuń Location jeśli jest pusta
                location_name = self.location.name
                self.location.delete()
                if deleted_items is not None:
                    deleted_items.append({'type': 'rack_location', 'name': location_name})
        
        # Ręcznie usuń wszystkie półki (aby ich metody delete() były wywoływane i zbierały deleted_items)
        # Zamiast polegać na CASCADE, który nie wywołuje metody delete()
        shelves_to_delete = list(self.shelves.all())
        for shelf in shelves_to_delete:
            shelf.delete(deleted_items=deleted_items)
        
        rack_name = self.name
        super().delete(*args, **kwargs)
        if deleted_items is not None:
            deleted_items.append({'type': 'rack', 'name': rack_name})


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
        validators=[MinValueValidator(Decimal('1.00'))],
        verbose_name="Szerokość"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(Decimal('1.00'))],
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
    
    def sync_to_location(self, barcode, _syncing=False):
        """Synchronizuje półkę do Location w WMS oraz nadrzędny regał i strefę jeśli nie są zsynchronizowane
        
        Args:
            barcode: Kod kreskowy dla Location
            _syncing: Flaga wewnętrzna zapobiegająca cyklicznym wywołaniom
        """
        from wms.models import Location
        
        if not barcode:
            raise ValueError("Barcode jest wymagany")
        
        # Sprawdź czy barcode już istnieje
        existing_location = Location.objects.filter(barcode=barcode).first()
        if existing_location and existing_location != self.location:
            raise ValueError(f"Barcode '{barcode}' jest już używany przez inną lokalizację")
        
        # Synchronizuj nadrzędną strefę jeśli nie jest zsynchronizowana (bez synchronizacji dzieci, aby uniknąć rekurencji)
        if not self.rack.zone.location and not _syncing:
            # Generuj barcode dla strefy
            zone_barcode = f"ZONE-{self.rack.zone.id}"
            self.rack.zone.sync_to_location(zone_barcode, sync_children=False, _syncing=True)
        
        # Synchronizuj nadrzędny regał jeśli nie jest zsynchronizowany (bez synchronizacji dzieci, aby uniknąć rekurencji)
        if not self.rack.location and not _syncing:
            # Generuj barcode dla regału
            rack_barcode = f"{self.rack.zone.location.barcode}-R{self.rack.id}"
            self.rack.sync_to_location(rack_barcode, sync_children=False, _syncing=True)
        
        # Określ parent (regał powinien mieć Location po synchronizacji powyżej)
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
        deleted_items = kwargs.pop('deleted_items', None)  # Lista do zbierania informacji o usuniętych elementach
        
        if self.location:
            # Jeśli Location jest już w trakcie usuwania, po prostu odłącz relację
            if hasattr(self.location, '_deleting_from_builder') and self.location._deleting_from_builder:
                self.location = None
                self.save(update_fields=['location'])
            else:
                if not self.is_location_empty():
                    raise ValidationError(
                        f"Nie można usunąć półki '{self.name}' - powiązana lokalizacja '{self.location.name}' "
                        f"ma powiązania z innymi obiektami (Stock, StockMovement, PickingHistory, itp.)"
                    )
                # Oznacz Location że jest usuwane z powodu usuwania elementu buildera
                # (zapobiega cyklicznemu usuwaniu w sygnale)
                self.location._deleting_from_builder = True
                # Usuń Location jeśli jest pusta
                location_name = self.location.name
                self.location.delete()
                if deleted_items is not None:
                    deleted_items.append({'type': 'shelf_location', 'name': location_name})
        
        shelf_name = self.name
        super().delete(*args, **kwargs)
        if deleted_items is not None:
            deleted_items.append({'type': 'shelf', 'name': shelf_name})

