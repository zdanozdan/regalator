from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf
from .forms import WarehouseForm, ZoneForm, RackForm, ShelfForm, ZoneSyncForm, RackSyncForm, ShelfSyncForm
from decimal import Decimal, InvalidOperation
import json


def _generate_copy_label(name):
    base = (name or '').strip() or 'Kopia'
    suffix = ' (kopia)'
    normalized_suffix = suffix.strip().lower()
    if base.lower().endswith(normalized_suffix):
        return base
    return f'{base}{suffix}'


def _get_deleted_item_label(item_type, item_name):
    """Zwraca etykietę dla usuniętego elementu"""
    labels = {
        'zone': f'Strefa "{item_name}"',
        'rack': f'Regał "{item_name}"',
        'shelf': f'Półka "{item_name}"',
        'zone_location': f'Lokalizacja strefy "{item_name}"',
        'rack_location': f'Lokalizacja regału "{item_name}"',
        'shelf_location': f'Lokalizacja półki "{item_name}"',
    }
    return labels.get(item_type, f'"{item_name}"')


def _build_toast_triggers(deleted_items):
    """Buduje HX-Trigger z wieloma toastami dla usuniętych elementów"""
    if not deleted_items:
        return {}
    
    # Jeśli jest tylko jeden element, użyj standardowego toastMessage
    if len(deleted_items) == 1:
        item = deleted_items[0]
        item_label = _get_deleted_item_label(item['type'], item['name'])
        return {
            'toastMessage': {
                'value': f'{item_label} została usunięta.',
                'type': 'success'
            }
        }
    
    # Jeśli jest wiele elementów, prześlij listę toastów i użyj specjalnego triggera
    # Frontend wyświetli je jeden po drugim
    toast_list = []
    for item in deleted_items:
        item_label = _get_deleted_item_label(item['type'], item['name'])
        toast_list.append({
            'value': f'{item_label} została usunięta.',
            'type': 'success'
        })
    
    return {
        'toastMessageList': {
            'toasts': toast_list
        },
        # Dodaj również główny toast dla kompatybilności
        'toastMessage': {
            'value': f'Usunięto {len(deleted_items)} element(ów).',
            'type': 'success'
        }
    }


def _serialize_shelf(shelf):
    return {
        'id': shelf.id,
        'name': shelf.name,
        'x': float(shelf.x),
        'y': float(shelf.y),
        'width': float(shelf.width),
        'height': float(shelf.height),
        'color': shelf.color,
        'synced': bool(shelf.location_id)
    }


def _serialize_rack(rack):
    return {
        'id': rack.id,
        'name': rack.name,
        'x': float(rack.x),
        'y': float(rack.y),
        'width': float(rack.width),
        'height': float(rack.height),
        'color': rack.color,
        'synced': bool(rack.location_id),
        'shelves': [_serialize_shelf(shelf) for shelf in rack.shelves.all()]
    }


def _serialize_zone(zone):
    return {
        'id': zone.id,
        'name': zone.name,
        'x': float(zone.x),
        'y': float(zone.y),
        'width': float(zone.width),
        'height': float(zone.height),
        'color': zone.color,
        'synced': bool(zone.location_id),
        'racks': [_serialize_rack(rack) for rack in zone.racks.all()]
    }


def _generate_default_zone_name(warehouse):
    base = "Nowa strefa"
    existing = set(warehouse.zones.values_list('name', flat=True))
    if base not in existing:
        return base
    suffix = 2
    while True:
        candidate = f"{base} {suffix}"
        if candidate not in existing:
            return candidate
        suffix += 1


def _generate_default_rack_name(zone):
    base = "Nowy regał"
    existing = set(zone.racks.values_list('name', flat=True))
    if base not in existing:
        return base
    suffix = 2
    while True:
        candidate = f"{base} {suffix}"
        if candidate not in existing:
            return candidate
        suffix += 1


def _generate_default_shelf_name(rack):
    base = "Nowa półka"
    existing = set(rack.shelves.values_list('name', flat=True))
    if base not in existing:
        return base
    suffix = 2
    while True:
        candidate = f"{base} {suffix}"
        if candidate not in existing:
            return candidate
        suffix += 1


@login_required
def warehouse_list(request):
    """List all warehouses"""
    warehouses = Warehouse.objects.all().order_by('-created_at')
    return render(request, 'wms_builder/warehouse_list.html', {
        'warehouses': warehouses
    })


@login_required
def warehouse_detail(request, warehouse_id, zone_id=None, rack_id=None):
    """Main view with SVG canvas showing warehouse layout"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    zones = warehouse.zones.all().prefetch_related('racks__shelves')
    active_zone = None
    active_rack = None

    if rack_id is not None:
        try:
            active_rack = WarehouseRack.objects.select_related('zone').get(
                id=rack_id,
                zone__warehouse=warehouse
            )
            active_zone = active_rack.zone
        except WarehouseRack.DoesNotExist:
            # Regał został usunięty, przekieruj do widoku magazynu lub strefy
            if zone_id:
                redirect_url = reverse('wms_builder:warehouse_detail_zone', 
                                     args=[warehouse_id, zone_id])
            else:
                redirect_url = reverse('wms_builder:warehouse_detail', 
                                     args=[warehouse_id])
            return redirect(f'{redirect_url}?not_found=rack')
    elif zone_id is not None:
        active_zone = get_object_or_404(warehouse.zones, id=zone_id)
    
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
    
    breadcrumbs = [
        {'label': 'Magazyny', 'url': reverse('wms_builder:warehouse_list')},
        {'label': warehouse.name, 'url': reverse('wms_builder:warehouse_detail', args=[warehouse.id])}
    ]
    if active_zone:
        breadcrumbs.append({
            'label': active_zone.name,
            'url': reverse('wms_builder:warehouse_detail_zone', args=[warehouse.id, active_zone.id]) if not active_rack else reverse('wms_builder:warehouse_detail_zone', args=[warehouse.id, active_zone.id])
        })
    if active_rack:
        breadcrumbs.append({'label': active_rack.name, 'url': None})
    else:
        breadcrumbs[-1]['url'] = None
    
    context = {
        'warehouse': warehouse,
        'zones': zones,
        'zones_data': zones_data,
        'active_zone': active_zone,
        'active_rack': active_rack,
        'detail_base_url': reverse('wms_builder:warehouse_detail', args=[warehouse.id]),
        'breadcrumbs': breadcrumbs,
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
        initial = {}
        x_param = request.GET.get('x')
        y_param = request.GET.get('y')
        if x_param is not None:
            try:
                initial['x'] = Decimal(x_param)
            except (InvalidOperation, ValueError, TypeError):
                pass
        if y_param is not None:
            try:
                initial['y'] = Decimal(y_param)
            except (InvalidOperation, ValueError, TypeError):
                pass
        form = ZoneForm(initial=initial or None)
    
    return render(request, 'wms_builder/partials/_zone_form.html', {
        'form': form,
        'warehouse': warehouse
    })


@login_required
@require_http_methods(["POST"])
def htmx_zone_quick_create(request, warehouse_id):
    """Create a zone immediately with default values"""
    warehouse = get_object_or_404(Warehouse, id=warehouse_id)
    default_width = WarehouseZone._meta.get_field('width').default or Decimal('200')
    default_height = WarehouseZone._meta.get_field('height').default or Decimal('150')
    default_color = WarehouseZone._meta.get_field('color').default or '#007bff'

    def _parse_decimal(value, default):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return default

    x = _parse_decimal(request.POST.get('x'), Decimal('0'))
    y = _parse_decimal(request.POST.get('y'), Decimal('0'))
    width = _parse_decimal(request.POST.get('width'), default_width)
    height = _parse_decimal(request.POST.get('height'), default_height)
    if width < 1:
        width = Decimal('1')
    if height < 1:
        height = Decimal('1')

    name = request.POST.get('name') or _generate_default_zone_name(warehouse)
    color = request.POST.get('color') or default_color

    zone = WarehouseZone.objects.create(
        warehouse=warehouse,
        name=name,
        x=x,
        y=y,
        width=width,
        height=height,
        color=color
    )

    return JsonResponse({'zone': _serialize_zone(zone)}, status=201)


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
        if width < 1 or height < 1:
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
        deleted_items = []
        zone.delete(deleted_items=deleted_items)
        
        # Wyświetl toasty dla wszystkich usuniętych elementów
        triggers = _build_toast_triggers(deleted_items)
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps(triggers)
        return response
    except ValidationError as e:
        error_message = str(e) if hasattr(e, '__str__') else (e.messages[0] if hasattr(e, 'messages') and e.messages else 'Błąd walidacji')
        response = HttpResponse(
            f'<div class="alert alert-danger">{error_message}</div>',
            status=400
        )
        toast_message = {
            "toastMessage": {
                "value": error_message,
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
@require_http_methods(["POST"])
def htmx_zone_duplicate(request, zone_id):
    """Duplicate a zone along with its racks and shelves"""
    zone = get_object_or_404(
        WarehouseZone.objects.prefetch_related('racks__shelves'),
        id=zone_id
    )
    try:
        target_x = Decimal(request.POST.get('x', zone.x))
        target_y = Decimal(request.POST.get('y', zone.y))
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'error': 'Nieprawidłowe współrzędne.'}, status=400)

    with transaction.atomic():
        new_zone = WarehouseZone.objects.create(
            warehouse=zone.warehouse,
            name=_generate_copy_label(zone.name),
            x=target_x,
            y=target_y,
            width=zone.width,
            height=zone.height,
            color=zone.color
        )
        for rack in zone.racks.all():
            new_rack = WarehouseRack.objects.create(
                zone=new_zone,
                name=_generate_copy_label(rack.name),
                x=rack.x,
                y=rack.y,
                width=rack.width,
                height=rack.height,
                color=rack.color
            )
            for shelf in rack.shelves.all():
                WarehouseShelf.objects.create(
                    rack=new_rack,
                    name=_generate_copy_label(shelf.name),
                    x=shelf.x,
                    y=shelf.y,
                    width=shelf.width,
                    height=shelf.height,
                    color=shelf.color
                )

    return JsonResponse({'zone': _serialize_zone(new_zone)}, status=201)


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
            redirect_url = reverse('wms_builder:warehouse_detail_zone', args=[zone.warehouse_id, zone.id])
            return HttpResponse(status=204, headers={'HX-Redirect': redirect_url})
    else:
        form = RackForm()
    
    return render(request, 'wms_builder/partials/_rack_form.html', {
        'form': form,
        'zone': zone
    })


@login_required
@require_http_methods(["POST"])
def htmx_rack_quick_create(request, zone_id):
    """Create rack immediately with default values"""
    zone = get_object_or_404(WarehouseZone, id=zone_id)
    rack_model = WarehouseRack
    default_width = rack_model._meta.get_field('width').default or Decimal('80')
    default_height = rack_model._meta.get_field('height').default or Decimal('60')
    default_color = rack_model._meta.get_field('color').default or '#28a745'

    def _parse_decimal(value, default):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return default

    x = _parse_decimal(request.POST.get('x'), Decimal('0'))
    y = _parse_decimal(request.POST.get('y'), Decimal('0'))
    width = _parse_decimal(request.POST.get('width'), default_width)
    height = _parse_decimal(request.POST.get('height'), default_height)
    if width < 1:
        width = Decimal('1')
    if height < 1:
        height = Decimal('1')

    name = request.POST.get('name') or _generate_default_rack_name(zone)
    color = request.POST.get('color') or default_color

    rack = WarehouseRack.objects.create(
        zone=zone,
        name=name,
        x=x,
        y=y,
        width=width,
        height=height,
        color=color
    )
    rack = WarehouseRack.objects.filter(id=rack.id).prefetch_related('shelves').first()

    return JsonResponse({'rack': _serialize_rack(rack)}, status=201)


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
        if width < 1 or height < 1:
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
        deleted_items = []
        rack.delete(deleted_items=deleted_items)
        
        # Wyświetl toasty dla wszystkich usuniętych elementów
        triggers = _build_toast_triggers(deleted_items)
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps(triggers)
        return response
    except ValidationError as e:
        error_message = str(e) if hasattr(e, '__str__') else (e.messages[0] if hasattr(e, 'messages') and e.messages else 'Błąd walidacji')
        response = HttpResponse(
            f'<div class="alert alert-danger">{error_message}</div>',
            status=400
        )
        toast_message = {
            "toastMessage": {
                "value": error_message,
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
@require_http_methods(["POST"])
def htmx_rack_duplicate(request, rack_id):
    """Duplicate a rack (with shelves) into the selected zone"""
    rack = get_object_or_404(
        WarehouseRack.objects.prefetch_related('shelves'),
        id=rack_id
    )
    target_zone_id = request.POST.get('target_zone_id')
    if not target_zone_id:
        return JsonResponse({'error': 'Brak docelowej strefy.'}, status=400)
    target_zone = get_object_or_404(WarehouseZone, id=target_zone_id)

    try:
        target_x = Decimal(request.POST.get('x', rack.x))
        target_y = Decimal(request.POST.get('y', rack.y))
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'error': 'Nieprawidłowe współrzędne.'}, status=400)

    with transaction.atomic():
        new_rack = WarehouseRack.objects.create(
            zone=target_zone,
            name=_generate_copy_label(rack.name),
            x=target_x,
            y=target_y,
            width=rack.width,
            height=rack.height,
            color=rack.color
        )

        for shelf in rack.shelves.all():
            WarehouseShelf.objects.create(
                rack=new_rack,
                name=_generate_copy_label(shelf.name),
                x=shelf.x,
                y=shelf.y,
                width=shelf.width,
                height=shelf.height,
                color=shelf.color
            )

    return JsonResponse({'rack': _serialize_rack(new_rack)}, status=201)


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
def htmx_shelf_quick_create(request, rack_id):
    """Create shelf immediately with default values"""
    rack = get_object_or_404(WarehouseRack, id=rack_id)
    shelf_model = WarehouseShelf
    default_width = shelf_model._meta.get_field('width').default or Decimal('60')
    default_height = shelf_model._meta.get_field('height').default or Decimal('20')
    default_color = shelf_model._meta.get_field('color').default or '#ffc107'

    def _parse_decimal(value, default):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return default

    x = _parse_decimal(request.POST.get('x'), Decimal('0'))
    y = _parse_decimal(request.POST.get('y'), Decimal('0'))
    width = _parse_decimal(request.POST.get('width'), default_width)
    height = _parse_decimal(request.POST.get('height'), default_height)
    if width < 1:
        width = Decimal('1')
    if height < 1:
        height = Decimal('1')

    name = request.POST.get('name') or _generate_default_shelf_name(rack)
    color = request.POST.get('color') or default_color

    shelf = WarehouseShelf.objects.create(
        rack=rack,
        name=name,
        x=x,
        y=y,
        width=width,
        height=height,
        color=color
    )

    return JsonResponse({'shelf': _serialize_shelf(shelf)}, status=201)


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
        if width < 1 or height < 1:
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
        deleted_items = []
        shelf.delete(deleted_items=deleted_items)
        
        # Wyświetl toasty dla wszystkich usuniętych elementów
        triggers = _build_toast_triggers(deleted_items)
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps(triggers)
        return response
    except ValidationError as e:
        error_message = str(e) if hasattr(e, '__str__') else (e.messages[0] if hasattr(e, 'messages') and e.messages else 'Błąd walidacji')
        response = HttpResponse(
            f'<div class="alert alert-danger">{error_message}</div>',
            status=400
        )
        toast_message = {
            "toastMessage": {
                "value": error_message,
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
@require_http_methods(["POST"])
def htmx_shelf_duplicate(request, shelf_id):
    """Duplicate shelf into the selected rack"""
    shelf = get_object_or_404(WarehouseShelf, id=shelf_id)
    target_rack_id = request.POST.get('target_rack_id')
    if not target_rack_id:
        return JsonResponse({'error': 'Brak docelowego regału.'}, status=400)
    target_rack = get_object_or_404(WarehouseRack, id=target_rack_id)

    try:
        target_x = Decimal(request.POST.get('x', shelf.x))
        target_y = Decimal(request.POST.get('y', shelf.y))
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({'error': 'Nieprawidłowe współrzędne.'}, status=400)

    new_shelf = WarehouseShelf.objects.create(
        rack=target_rack,
        name=_generate_copy_label(shelf.name),
        x=target_x,
        y=target_y,
        width=shelf.width,
        height=shelf.height,
        color=shelf.color
    )

    return JsonResponse({'shelf': _serialize_shelf(new_shelf)}, status=201)


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
                # Generuj automatyczny kod kreskowy na podstawie ID strefy
                # Jeśli Location już istnieje, użyj istniejącego kodu
                barcode = zone.location.barcode if zone.location else f"ZONE-{zone.id}"
                zone.sync_to_location(barcode)
                
                # Odśwież obiekt, aby mieć aktualne dane z Location
                zone.refresh_from_db()
                
                # Przygotuj toast message z nazwą i kodem kreskowym
                location_name = zone.location.name if zone.location else zone.name
                location_barcode = zone.location.barcode if zone.location else barcode
                toast_message = f'Strefa "{location_name}" została zsynchronizowana ({location_barcode})'
                
                # Zwróć odpowiedź z toast message i zamknij modal
                response = HttpResponse(status=204)
                response['HX-Refresh'] = 'true'
                response['HX-Trigger'] = json.dumps({
                    'toastMessage': {
                        'value': toast_message,
                        'type': 'success'
                    },
                    'modalHide': {}
                })
                return response
            except ValueError as e:
                # Jeśli błąd, wyświetl komunikat w modalu
                form.add_error(None, str(e))
    else:
        form = ZoneSyncForm()
    
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
                # Generuj automatyczny kod kreskowy na podstawie ID regału i strefy
                # Jeśli Location już istnieje, użyj istniejącego kodu
                if rack.location:
                    barcode = rack.location.barcode
                elif rack.zone.location:
                    barcode = f"{rack.zone.location.barcode}-R{rack.id}"
                else:
                    barcode = f"ZONE-{rack.zone.id}-R{rack.id}"
                rack.sync_to_location(barcode)
                
                # Odśwież obiekt, aby mieć aktualne dane z Location
                rack.refresh_from_db()
                
                # Przygotuj toast message z nazwą i kodem kreskowym
                location_name = rack.location.name if rack.location else rack.name
                location_barcode = rack.location.barcode if rack.location else barcode
                toast_message = f'Regał "{location_name}" został zsynchronizowany ({location_barcode})'
                
                # Zwróć odpowiedź z toast message i zamknij modal
                response = HttpResponse(status=204)
                response['HX-Refresh'] = 'true'
                response['HX-Trigger'] = json.dumps({
                    'toastMessage': {
                        'value': toast_message,
                        'type': 'success'
                    },
                    'modalHide': {}
                })
                return response
            except ValueError as e:
                # Jeśli błąd, wyświetl komunikat w modalu
                form.add_error(None, str(e))
    else:
        form = RackSyncForm()
    
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
                # Generuj automatyczny kod kreskowy na podstawie ID półki, regału i strefy
                # Jeśli Location już istnieje, użyj istniejącego kodu
                if shelf.location:
                    barcode = shelf.location.barcode
                elif shelf.rack.location:
                    barcode = f"{shelf.rack.location.barcode}-S{shelf.id}"
                elif shelf.rack.zone.location:
                    barcode = f"{shelf.rack.zone.location.barcode}-R{shelf.rack.id}-S{shelf.id}"
                else:
                    barcode = f"ZONE-{shelf.rack.zone.id}-R{shelf.rack.id}-S{shelf.id}"
                shelf.sync_to_location(barcode)
                
                # Odśwież obiekt, aby mieć aktualne dane z Location
                shelf.refresh_from_db()
                
                # Przygotuj toast message z nazwą i kodem kreskowym
                location_name = shelf.location.name if shelf.location else shelf.name
                location_barcode = shelf.location.barcode if shelf.location else barcode
                toast_message = f'Półka "{location_name}" została zsynchronizowana ({location_barcode})'
                
                # Zwróć odpowiedź z toast message i zamknij modal
                response = HttpResponse(status=204)
                response['HX-Refresh'] = 'true'
                response['HX-Trigger'] = json.dumps({
                    'toastMessage': {
                        'value': toast_message,
                        'type': 'success'
                    },
                    'modalHide': {}
                })
                return response
            except ValueError as e:
                # Jeśli błąd, wyświetl komunikat w modalu
                form.add_error(None, str(e))
    else:
        form = ShelfSyncForm()
    
    return render(request, 'wms_builder/partials/_shelf_sync_form.html', {
        'form': form,
        'shelf': shelf
    })

