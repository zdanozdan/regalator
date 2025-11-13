from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf
from .forms import WarehouseForm, ZoneForm, RackForm, ShelfForm, ZoneSyncForm, RackSyncForm, ShelfSyncForm
from decimal import Decimal


@login_required
def warehouse_list(request):
    """List all warehouses"""
    warehouses = Warehouse.objects.all().order_by('-created_at')
    return render(request, 'wms_builder/warehouse_list.html', {
        'warehouses': warehouses
    })


@login_required
def warehouse_detail(request, warehouse_id):
    """Main view with SVG canvas showing warehouse layout"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    zones = warehouse.zones.all().prefetch_related('racks__shelves')
    
    # Calculate absolute positions for rendering
    zones_data = []
    for zone in zones:
        racks_data = []
        for rack in zone.racks.all():
            shelves_data = []
            for shelf in rack.shelves.all():
                abs_x = float(zone.x + rack.x + shelf.x)
                abs_y = float(zone.y + rack.y + shelf.y)
                shelves_data.append({
                    'shelf': shelf,
                    'abs_x': abs_x,
                    'abs_y': abs_y,
                    'text_x': abs_x + float(shelf.width) / 2,
                    'text_y': abs_y + float(shelf.height) / 2,
                })
            abs_x = float(zone.x + rack.x)
            abs_y = float(zone.y + rack.y)
            racks_data.append({
                'rack': rack,
                'abs_x': abs_x,
                'abs_y': abs_y,
                'text_x': abs_x + float(rack.width) / 2,
                'text_y': abs_y + float(rack.height) / 2,
                'shelves': shelves_data,
            })
        zones_data.append({
            'zone': zone,
            'text_x': float(zone.x + zone.width / 2),
            'text_y': float(zone.y + zone.height / 2),
            'racks': racks_data,
        })
    
    context = {
        'warehouse': warehouse,
        'zones': zones,
        'zones_data': zones_data,
    }
    return render(request, 'wms_builder/warehouse_detail.html', context)


@login_required
def warehouse_create(request):
    """Create new warehouse"""
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.created_by = request.user
            warehouse.save()
            return redirect('wms_builder:warehouse_detail', warehouse_id=warehouse.id)
    else:
        form = WarehouseForm()
    
    return render(request, 'wms_builder/warehouse_form.html', {
        'form': form,
        'title': 'Utwórz magazyn'
    })


@login_required
def warehouse_edit(request, warehouse_id):
    """Edit warehouse properties"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            return redirect('wms_builder:warehouse_detail', warehouse_id=warehouse.id)
    else:
        form = WarehouseForm(instance=warehouse)
    
    return render(request, 'wms_builder/warehouse_form.html', {
        'form': form,
        'warehouse': warehouse,
        'title': 'Edytuj magazyn'
    })


@login_required
def warehouse_delete(request, warehouse_id):
    """Delete warehouse"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    if request.method == 'POST':
        warehouse.delete()
        return redirect('wms_builder:warehouse_list')
    
    return render(request, 'wms_builder/warehouse_confirm_delete.html', {
        'warehouse': warehouse
    })


# HTMX endpoints for zones
@login_required
@require_http_methods(["GET", "POST"])
def htmx_zone_create(request, warehouse_id):
    """Create zone via HTMX"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    
    if request.method == 'POST':
        form = ZoneForm(request.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.warehouse = warehouse
            zone.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = ZoneForm()
    
    return render(request, 'wms_builder/partials/_zone_form.html', {
        'form': form,
        'warehouse': warehouse
    })


@login_required
@require_http_methods(["POST"])
def htmx_zone_update_position(request, zone_id):
    """Update zone position after drag"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    
    try:
        x = Decimal(request.POST.get('x', '0'))
        y = Decimal(request.POST.get('y', '0'))
        zone.x = x
        zone.y = y
        zone.save()
        return HttpResponse(status=204)
    except (ValueError, TypeError):
        return HttpResponse(status=400)


@login_required
@require_http_methods(["POST"])
def htmx_zone_update_size(request, zone_id):
    """Update zone size after resize"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    
    try:
        width = Decimal(request.POST.get('width', '200'))
        height = Decimal(request.POST.get('height', '150'))
        if width < 50 or height < 50:
            return HttpResponse(status=400)
        zone.width = width
        zone.height = height
        zone.save()
        return HttpResponse(status=204)
    except (ValueError, TypeError):
        return HttpResponse(status=400)


@login_required
@require_http_methods(["GET", "POST"])
def htmx_zone_edit(request, zone_id):
    """Open edit modal for zone"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    
    if request.method == 'POST':
        form = ZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = ZoneForm(instance=zone)
    
    return render(request, 'wms_builder/partials/_zone_form.html', {
        'form': form,
        'zone': zone,
        'warehouse': zone.warehouse
    })


@login_required
@require_http_methods(["POST"])
def htmx_zone_delete(request, zone_id):
    """Delete zone"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    try:
        zone.delete()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    except ValidationError as e:
        error_message = str(e) if hasattr(e, '__str__') else (e.messages[0] if hasattr(e, 'messages') and e.messages else 'Błąd walidacji')
        return HttpResponse(
            f'<div class="alert alert-danger">{error_message}</div>',
            status=400
        )


# HTMX endpoints for racks
@login_required
@require_http_methods(["GET", "POST"])
def htmx_rack_create(request, zone_id):
    """Create rack via HTMX"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    
    if request.method == 'POST':
        form = RackForm(request.POST)
        if form.is_valid():
            rack = form.save(commit=False)
            rack.zone = zone
            rack.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = RackForm()
    
    return render(request, 'wms_builder/partials/_rack_form.html', {
        'form': form,
        'zone': zone
    })


@login_required
@require_http_methods(["POST"])
def htmx_rack_update_position(request, rack_id):
    """Update rack position after drag"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    
    try:
        x = Decimal(request.POST.get('x', '0'))
        y = Decimal(request.POST.get('y', '0'))
        rack.x = x
        rack.y = y
        rack.save()
        return HttpResponse(status=204)
    except (ValueError, TypeError):
        return HttpResponse(status=400)


@login_required
@require_http_methods(["POST"])
def htmx_rack_update_size(request, rack_id):
    """Update rack size after resize"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    try:
        width = Decimal(request.POST.get('width', '80'))
        height = Decimal(request.POST.get('height', '60'))
        if width < 20 or height < 20:
            return HttpResponse(status=400)
        rack.width = width
        rack.height = height
        rack.save()
        return HttpResponse(status=204)
    except (ValueError, TypeError):
        return HttpResponse(status=400)


@login_required
@require_http_methods(["GET", "POST"])
def htmx_rack_edit(request, rack_id):
    """Open edit modal for rack"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    
    if request.method == 'POST':
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = RackForm(instance=rack)
    
    return render(request, 'wms_builder/partials/_rack_form.html', {
        'form': form,
        'rack': rack,
        'zone': rack.zone
    })


@login_required
@require_http_methods(["POST"])
def htmx_rack_delete(request, rack_id):
    """Delete rack"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    try:
        rack.delete()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    except ValidationError as e:
        error_message = str(e) if hasattr(e, '__str__') else (e.messages[0] if hasattr(e, 'messages') and e.messages else 'Błąd walidacji')
        return HttpResponse(
            f'<div class="alert alert-danger">{error_message}</div>',
            status=400
        )


# HTMX endpoints for shelves
@login_required
@require_http_methods(["GET", "POST"])
def htmx_shelf_create(request, rack_id):
    """Create shelf via HTMX"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    
    if request.method == 'POST':
        form = ShelfForm(request.POST)
        if form.is_valid():
            shelf = form.save(commit=False)
            shelf.rack = rack
            shelf.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = ShelfForm()
    
    return render(request, 'wms_builder/partials/_shelf_form.html', {
        'form': form,
        'rack': rack
    })


@login_required
@require_http_methods(["POST"])
def htmx_shelf_update_position(request, shelf_id):
    """Update shelf position after drag"""
    shelf = get_object_or_404(WarehouseShelf, id=shelf_id)
    
    try:
        x = Decimal(request.POST.get('x', '0'))
        y = Decimal(request.POST.get('y', '0'))
        shelf.x = x
        shelf.y = y
        shelf.save()
        return HttpResponse(status=204)
    except (ValueError, TypeError):
        return HttpResponse(status=400)


@login_required
@require_http_methods(["POST"])
def htmx_shelf_update_size(request, shelf_id):
    """Update shelf size after resize"""
    shelf = get_object_or_404(WarehouseShelf, id=shelf_id)
    try:
        width = Decimal(request.POST.get('width', '60'))
        height = Decimal(request.POST.get('height', '20'))
        if width < 15 or height < 10:
            return HttpResponse(status=400)
        shelf.width = width
        shelf.height = height
        shelf.save()
        return HttpResponse(status=204)
    except (ValueError, TypeError):
        return HttpResponse(status=400)


@login_required
@require_http_methods(["GET", "POST"])
def htmx_shelf_edit(request, shelf_id):
    """Open edit modal for shelf"""
    shelf = get_object_or_404(WarehouseShelf, id=shelf_id)
    
    if request.method == 'POST':
        form = ShelfForm(request.POST, instance=shelf)
        if form.is_valid():
            form.save()
            return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    else:
        form = ShelfForm(instance=shelf)
    
    return render(request, 'wms_builder/partials/_shelf_form.html', {
        'form': form,
        'shelf': shelf,
        'rack': shelf.rack
    })


@login_required
@require_http_methods(["POST"])
def htmx_shelf_delete(request, shelf_id):
    """Delete shelf"""
    shelf = get_object_or_404(WarehouseShelf, id=shelf_id)
    try:
        shelf.delete()
        return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
    except ValidationError as e:
        error_message = str(e) if hasattr(e, '__str__') else (e.messages[0] if hasattr(e, 'messages') and e.messages else 'Błąd walidacji')
        return HttpResponse(
            f'<div class="alert alert-danger">{error_message}</div>',
            status=400
        )


# HTMX endpoints for synchronization
@login_required
@require_http_methods(["GET", "POST"])
def htmx_zone_sync_to_location(request, zone_id):
    """Synchronize zone to Location"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    
    if request.method == 'POST':
        form = ZoneSyncForm(request.POST)
        if form.is_valid():
            try:
                barcode = form.cleaned_data['barcode']
                zone.sync_to_location(barcode)
                return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
            except ValueError as e:
                form.add_error('barcode', str(e))
    else:
        # Pre-fill barcode if location exists
        initial = {}
        if zone.location:
            initial['barcode'] = zone.location.barcode
        form = ZoneSyncForm(initial=initial)
    
    return render(request, 'wms_builder/partials/_zone_sync_form.html', {
        'form': form,
        'zone': zone
    })


@login_required
@require_http_methods(["GET", "POST"])
def htmx_rack_sync_to_location(request, rack_id):
    """Synchronize rack to Location"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    
    if request.method == 'POST':
        form = RackSyncForm(request.POST)
        if form.is_valid():
            try:
                barcode = form.cleaned_data['barcode']
                rack.sync_to_location(barcode)
                return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
            except ValueError as e:
                form.add_error('barcode', str(e))
    else:
        # Pre-fill barcode if location exists
        initial = {}
        if rack.location:
            initial['barcode'] = rack.location.barcode
        form = RackSyncForm(initial=initial)
    
    return render(request, 'wms_builder/partials/_rack_sync_form.html', {
        'form': form,
        'rack': rack
    })


@login_required
@require_http_methods(["GET", "POST"])
def htmx_shelf_sync_to_location(request, shelf_id):
    """Synchronize shelf to Location"""
    shelf = get_object_or_404(WarehouseShelf, id=shelf_id)
    
    if request.method == 'POST':
        form = ShelfSyncForm(request.POST)
        if form.is_valid():
            try:
                barcode = form.cleaned_data['barcode']
                shelf.sync_to_location(barcode)
                return HttpResponse(status=204, headers={'HX-Refresh': 'true'})
            except ValueError as e:
                form.add_error('barcode', str(e))
    else:
        # Pre-fill barcode if location exists
        initial = {}
        if shelf.location:
            initial['barcode'] = shelf.location.barcode
        form = ShelfSyncForm(initial=initial)
    
    return render(request, 'wms_builder/partials/_shelf_sync_form.html', {
        'form': form,
        'shelf': shelf
    })

