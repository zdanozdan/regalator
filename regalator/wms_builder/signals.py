from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='wms.Location')
def sync_location_to_builder(sender, instance, created, **kwargs):
    """Synchronizuje Location do odpowiedniego elementu w builderze"""
    # Sprawdź czy Location już ma powiązanie z builderem
    if hasattr(instance, 'warehouse_zone') and instance.warehouse_zone:
        # Aktualizuj istniejącą strefę
        zone = instance.warehouse_zone
        zone.name = instance.name
        zone.save(update_fields=['name'])
        return
    
    if hasattr(instance, 'warehouse_rack') and instance.warehouse_rack:
        # Aktualizuj istniejący regał
        rack = instance.warehouse_rack
        rack.name = instance.name
        rack.save(update_fields=['name'])
        return
    
    if hasattr(instance, 'warehouse_shelf') and instance.warehouse_shelf:
        # Aktualizuj istniejącą półkę
        shelf = instance.warehouse_shelf
        shelf.name = instance.name
        shelf.save(update_fields=['name'])
        return
    
    # Jeśli Location nie ma powiązania, utwórz odpowiedni element w builderze
    try:
        from wms_builder.models import Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf
        
        # Znajdź lub utwórz domyślny magazyn
        warehouse = Warehouse.objects.first()
        if not warehouse:
            warehouse = Warehouse.objects.create(
                name="Domyślny magazyn",
                description="Utworzony automatycznie z synchronizacji Location"
            )
        
        if instance.location_type == 'zone':
            # Utwórz strefę
            zone = WarehouseZone.objects.create(
                warehouse=warehouse,
                name=instance.name,
                x=Decimal('0.00'),
                y=Decimal('0.00')
            )
            # Połącz Location ze strefą
            instance.warehouse_zone = zone
            instance.save(update_fields=[])
        
        elif instance.location_type == 'rack':
            # Znajdź parent (strefa) lub utwórz domyślną
            parent_zone = None
            if instance.parent and hasattr(instance.parent, 'warehouse_zone'):
                parent_zone = instance.parent.warehouse_zone
            else:
                # Utwórz domyślną strefę jeśli nie ma
                parent_zone = WarehouseZone.objects.filter(warehouse=warehouse).first()
                if not parent_zone:
                    parent_zone = WarehouseZone.objects.create(
                        warehouse=warehouse,
                        name="Domyślna strefa",
                        x=Decimal('0.00'),
                        y=Decimal('0.00')
                    )
            
            # Utwórz regał
            rack = WarehouseRack.objects.create(
                zone=parent_zone,
                name=instance.name,
                x=Decimal('0.00'),
                y=Decimal('0.00')
            )
            # Połącz Location z regałem
            instance.warehouse_rack = rack
            instance.save(update_fields=[])
        
        elif instance.location_type == 'shelf':
            # Znajdź parent (regał) lub utwórz domyślny
            parent_rack = None
            if instance.parent:
                if hasattr(instance.parent, 'warehouse_rack'):
                    parent_rack = instance.parent.warehouse_rack
                elif hasattr(instance.parent, 'warehouse_zone'):
                    # Jeśli parent to strefa, utwórz regał w tej strefie
                    parent_zone = instance.parent.warehouse_zone
                    parent_rack = WarehouseRack.objects.filter(zone=parent_zone).first()
                    if not parent_rack:
                        parent_rack = WarehouseRack.objects.create(
                            zone=parent_zone,
                            name="Domyślny regał",
                            x=Decimal('0.00'),
                            y=Decimal('0.00')
                        )
            
            if not parent_rack:
                # Utwórz domyślną strukturę
                parent_zone = WarehouseZone.objects.filter(warehouse=warehouse).first()
                if not parent_zone:
                    parent_zone = WarehouseZone.objects.create(
                        warehouse=warehouse,
                        name="Domyślna strefa",
                        x=Decimal('0.00'),
                        y=Decimal('0.00')
                    )
                parent_rack = WarehouseRack.objects.filter(zone=parent_zone).first()
                if not parent_rack:
                    parent_rack = WarehouseRack.objects.create(
                        zone=parent_zone,
                        name="Domyślny regał",
                        x=Decimal('0.00'),
                        y=Decimal('0.00')
                    )
            
            # Utwórz półkę
            shelf = WarehouseShelf.objects.create(
                rack=parent_rack,
                name=instance.name,
                x=Decimal('0.00'),
                y=Decimal('0.00')
            )
            # Połącz Location z półką
            instance.warehouse_shelf = shelf
            instance.save(update_fields=[])
    
    except Exception as e:
        # Ignoruj błędy synchronizacji (np. jeśli wms_builder nie jest zainstalowany)
        logger.warning(f"Błąd synchronizacji Location do buildera: {e}")


@receiver(pre_delete, sender='wms.Location')
def delete_builder_element_on_location_delete(sender, instance, **kwargs):
    """Usuwa powiązany element w builderze przed usunięciem Location"""
    try:
        from wms_builder.models import WarehouseZone, WarehouseRack, WarehouseShelf
        
        if hasattr(instance, 'warehouse_zone') and instance.warehouse_zone:
            instance.warehouse_zone.delete()
        
        if hasattr(instance, 'warehouse_rack') and instance.warehouse_rack:
            instance.warehouse_rack.delete()
        
        if hasattr(instance, 'warehouse_shelf') and instance.warehouse_shelf:
            instance.warehouse_shelf.delete()
    
    except Exception as e:
        # Ignoruj błędy (np. jeśli wms_builder nie jest zainstalowany)
        logger.warning(f"Błąd usuwania elementu buildera przy usuwaniu Location: {e}")

