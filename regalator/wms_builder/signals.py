from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='wms.Location')
def update_location_to_builder(sender, instance, created, **kwargs):
    """Aktualizuje Location w odpowiednim elemencie buildera (tylko update)"""
    # Obsługuj tylko zdarzenia typu update (nie tworzenie nowych)
    if created:
        return
    
    toast_message = None
    element_type = None
    
    try:
        # Sprawdź czy Location już ma powiązanie z builderem
        if hasattr(instance, 'warehouse_zone') and instance.warehouse_zone:
            # Aktualizuj istniejącą strefę
            zone = instance.warehouse_zone
            zone.name = instance.name
            zone.save(update_fields=['name'])
            toast_message = f'Strefa "{instance.name}" została zaktualizowana.'
            element_type = 'zone'
        
        elif hasattr(instance, 'warehouse_rack') and instance.warehouse_rack:
            # Aktualizuj istniejący regał
            rack = instance.warehouse_rack
            rack.name = instance.name
            rack.save(update_fields=['name'])
            toast_message = f'Regał "{instance.name}" został zaktualizowany.'
            element_type = 'rack'
        
        elif hasattr(instance, 'warehouse_shelf') and instance.warehouse_shelf:
            # Aktualizuj istniejącą półkę
            shelf = instance.warehouse_shelf
            shelf.name = instance.name
            shelf.save(update_fields=['name'])
            toast_message = f'Półka "{instance.name}" została zaktualizowana.'
            element_type = 'shelf'
        
        # Jeśli Location nie ma powiązania, nic nie rób (tylko update)
        
        # Zapisz wiadomość toast w cache dla wyświetlenia przy następnym request
        if toast_message:
            cache_key = f'location_update_toast_{instance.id}_{element_type}'
            cache.set(cache_key, {
                'message': toast_message,
                'type': 'success',
                'location_id': instance.id,
                'element_type': element_type
            }, timeout=300)  # 5 minut
        
    except Exception as e:
        # Ignoruj błędy synchronizacji (np. jeśli wms_builder nie jest zainstalowany)
        logger.warning(f"Błąd aktualizacji Location w builderze: {e}")


@receiver(pre_delete, sender='wms.Location')
def delete_builder_element_on_location_delete(sender, instance, **kwargs):
    """Usuwa powiązany element w builderze przed usunięciem Location"""
    try:
        # Sprawdź czy Location jest usuwane z powodu usuwania elementu buildera
        # (w takim przypadku element buildera jest już w trakcie usuwania i nie powinniśmy go usuwać ponownie)
        if hasattr(instance, '_deleting_from_builder') and instance._deleting_from_builder:
            return
        
        if hasattr(instance, 'warehouse_zone') and instance.warehouse_zone:
            zone = instance.warehouse_zone
            # Oznacz Location że jest usuwane z powodu usuwania elementu buildera
            instance._deleting_from_builder = True
            zone.delete()
        
        if hasattr(instance, 'warehouse_rack') and instance.warehouse_rack:
            rack = instance.warehouse_rack
            instance._deleting_from_builder = True
            rack.delete()
        
        if hasattr(instance, 'warehouse_shelf') and instance.warehouse_shelf:
            shelf = instance.warehouse_shelf
            instance._deleting_from_builder = True
            shelf.delete()
    
    except Exception as e:
        # Ignoruj błędy (np. jeśli wms_builder nie jest zainstalowany)
        logger.warning(f"Błąd usuwania elementu buildera przy usuwaniu Location: {e}")

