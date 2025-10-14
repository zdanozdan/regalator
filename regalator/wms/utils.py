"""
Utility functions for WMS app
"""
from django.utils import timezone
from decimal import Decimal
from wms.models import Product, ProductGroup


def sync_product_from_subiekt(subiekt_product, stdout=None):
    """
    Synchronizes a product from Subiekt to WMS.
    
    Args:
        subiekt_product: Subiekt product object (tw_Towar)
        stdout: Optional output stream for logging (from management command)
    
    Returns:
        Product: The created or updated WMS product
    """
    # Mapowanie pól zgodnie z wymaganiami:
    # code = tw_Symbol
    # name = tw_Nazwa  
    # description = tw_Opis
    # subiekt_id = tw_Id
    # subiekt_stock = st_Stan
    # subiekt_stock_reserved = st_StanRez
    
    # Sprawdź czy produkt już istnieje w WMS
    wms_product, created = Product.objects.get_or_create(
        subiekt_id=subiekt_product.tw_Id,
        defaults={
            'code': subiekt_product.tw_Symbol,
            'name': subiekt_product.tw_Nazwa,
            'description': subiekt_product.tw_Opis or '',
            'unit': 'szt',  # Domyślna jednostka
        }
    )
    
    if not created:
        # Aktualizuj istniejący produkt
        wms_product.code = subiekt_product.tw_Symbol
        wms_product.name = subiekt_product.tw_Nazwa
        wms_product.description = subiekt_product.tw_Opis or ''
    
    # Aktualizuj dane z Subiektu
    wms_product.subiekt_stock = Decimal(str(getattr(subiekt_product, 'st_Stan', 0)))
    wms_product.subiekt_stock_reserved = Decimal(str(getattr(subiekt_product, 'st_StanRez', 0)))
    wms_product.last_sync_date = timezone.now()
    
    # Obsługa grupy produktów
    subiekt_group = getattr(subiekt_product, 'grt_Nazwa', '')
    if subiekt_group:
        wms_group, group_created = ProductGroup.objects.get_or_create(
            name=subiekt_group,
            defaults={
                'code': subiekt_group[:20],  # Używamy nazwy jako kodu (max 20 znaków)
                'description': f'Grupa z Subiektu: {subiekt_group}',
                'color': '#007bff',  # Domyślny kolor
            }
        )
        
        # Dodaj produkt do grupy (jeśli nie jest już w tej grupie)
        if wms_group not in wms_product.groups.all():
            wms_product.groups.add(wms_group)
            if stdout and group_created:
                stdout.write(f'  → Utworzono nową grupę: {wms_group.name}')
            elif stdout:
                stdout.write(f'  → Dodano do grupy: {wms_group.name}')
    
    wms_product.save()
    
    if stdout:
        if created:
            stdout.write(f'  → Utworzono nowy produkt: {wms_product.name}')
        else:
            stdout.write(f'  → Zaktualizowano produkt: {wms_product.name}')
    
    return wms_product


def get_or_create_product_from_subiekt(subiekt_id, stdout=None):
    """
    Gets a product from WMS by Subiekt ID, or creates it if it doesn't exist.
    
    Args:
        subiekt_id: Subiekt product ID (tw_Id)
        stdout: Optional output stream for logging (from management command)
    
    Returns:
        Product or None: The WMS product, or None if product not found in Subiekt
    """
    from subiekt.models import tw_Towar
    
    # Try to find product in WMS first
    product = Product.objects.filter(subiekt_id=subiekt_id).first()
    
    if product:
        return product
    
    # Product not in WMS, try to get it from Subiekt and sync it
    try:
        subiekt_product = tw_Towar.subiekt_objects.get_product_by_id(subiekt_id)
        if subiekt_product:
            if stdout:
                stdout.write(f'  → Produkt nie znaleziony w WMS, synchronizuję z Subiektu (ID: {subiekt_id})')
            product = sync_product_from_subiekt(subiekt_product, stdout=stdout)
            return product
        else:
            if stdout:
                stdout.write(f'  ⚠️  Produkt o ID {subiekt_id} nie istnieje ani w WMS, ani w Subiekcie')
            return None
    except Exception as e:
        if stdout:
            stdout.write(f'  ❌ Błąd podczas pobierania produktu z Subiektu (ID: {subiekt_id}): {str(e)}')
        return None

