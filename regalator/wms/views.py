from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from decimal import Decimal
from .models import *
from .forms import UserProfileForm
from assets.models import Asset
import json


def login_view(request):
    """Widok logowania"""
    if request.user.is_authenticated:
        return redirect('wms:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    return render(request, 'wms/login.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard główny - wybór procesu"""
    # Pobierz splash image
    try:
        splash_image = Asset.objects.get(slug='regalator')
    except Asset.DoesNotExist:
        splash_image = None
    
    # Ogólne statystyki
    total_zk_orders = CustomerOrder.objects.count()
    total_zd_orders = SupplierOrder.objects.count()
    total_products = Product.objects.count()
    total_locations = Location.objects.count()
    
    context = {
        'splash_image': splash_image,
        'total_zk_orders': total_zk_orders,
        'total_zd_orders': total_zd_orders,
        'total_products': total_products,
        'total_locations': total_locations,
    }
    return render(request, 'wms/dashboard.html', context)


@login_required
def kompletacja_dashboard(request):
    """Dashboard kompletacji (ZK)"""
    # Statystyki kompletacji
    pending_orders = CustomerOrder.objects.filter(status='pending').count()
    in_progress_orders = CustomerOrder.objects.filter(status='in_progress').count()
    completed_orders = CustomerOrder.objects.filter(status='completed').count()
    active_picking_orders = PickingOrder.objects.filter(status='in_progress').count()
    
    # Ostatnie zamówienia
    recent_orders = CustomerOrder.objects.all().order_by('-created_at')[:5]
    
    context = {
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'active_picking_orders': active_picking_orders,
        'recent_orders': recent_orders,
    }
    return render(request, 'wms/kompletacja_dashboard.html', context)


@login_required
def przyjecia_dashboard(request):
    """Dashboard przyjęć (ZD)"""
    # Statystyki przyjęć
    pending_supplier_orders = SupplierOrder.objects.filter(status='pending').count()
    in_transit_supplier_orders = SupplierOrder.objects.filter(status='in_transit').count()
    received_supplier_orders = SupplierOrder.objects.filter(status='received').count()
    active_receiving = ReceivingOrder.objects.filter(status='in_progress').count()
    
    # Ostatnie zamówienia ZD
    recent_supplier_orders = SupplierOrder.objects.all().order_by('-created_at')[:5]
    
    context = {
        'pending_supplier_orders': pending_supplier_orders,
        'in_transit_supplier_orders': in_transit_supplier_orders,
        'received_supplier_orders': received_supplier_orders,
        'active_receiving': active_receiving,
        'recent_supplier_orders': recent_supplier_orders,
    }
    return render(request, 'wms/przyjecia_dashboard.html', context)


@login_required
def order_list(request):
    """Lista zamówień klientów"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    orders = CustomerOrder.objects.all()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer_name__icontains=search_query)
        )
    
    orders = orders.order_by('-created_at')
    
    # Paginacja
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': CustomerOrder.ORDER_STATUS,
    }
    return render(request, 'wms/order_list.html', context)


@login_required
def order_detail(request, order_id):
    """Szczegóły zamówienia klienta"""
    order = get_object_or_404(CustomerOrder, id=order_id)
    picking_orders = PickingOrder.objects.filter(customer_order=order)
    
    context = {
        'order': order,
        'picking_orders': picking_orders,
    }
    return render(request, 'wms/order_detail.html', context)


@login_required
def create_picking_order(request, order_id):
    """Tworzenie zlecenia kompletacji dla zamówienia"""
    customer_order = get_object_or_404(CustomerOrder, id=order_id)
    
    if request.method == 'POST':
        # Sprawdź czy już istnieje zlecenie kompletacji dla tego zamówienia
        existing_picking = PickingOrder.objects.filter(customer_order=customer_order).first()
        if existing_picking:
            messages.warning(request, f'Zlecenie kompletacji już istnieje: {existing_picking.order_number}')
            return redirect('wms:order_detail', order_id=order_id)
        
        # Utwórz nowe zlecenie kompletacji
        picking_order = PickingOrder.objects.create(
            order_number=f"RegOut-{customer_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
            customer_order=customer_order,
            status='created',
            assigned_to=request.user
        )
        
        # Utwórz pozycje kompletacji na podstawie pozycji zamówienia klienta
        sequence = 1
        for order_item in customer_order.items.all():
            # Znajdź lokalizację z największą ilością produktu
            stock = Stock.objects.filter(
                product=order_item.product,
                quantity__gt=0
            ).order_by('-quantity').first()
            
            if stock:
                location = stock.location
            else:
                # Jeśli nie ma stanu, użyj pierwszej dostępnej lokalizacji
                location = Location.objects.first()
            
            PickingItem.objects.create(
                picking_order=picking_order,
                order_item=order_item,
                product=order_item.product,
                location=location,
                quantity_to_pick=order_item.quantity,
                quantity_picked=0,
                is_completed=False,
                sequence=sequence
            )
            sequence += 1
        
        messages.success(request, f'Utworzono zlecenie kompletacji: {picking_order.order_number}')
        return redirect('wms:picking_detail', picking_id=picking_order.id)
    
    return redirect('wms:order_detail', order_id=order_id)


@login_required
def picking_list(request):
    """Lista zleceń kompletacji"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    picking_orders = PickingOrder.objects.all()
    
    if status_filter:
        picking_orders = picking_orders.filter(status=status_filter)
    
    if search_query:
        picking_orders = picking_orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer_order__customer_name__icontains=search_query)
        )
    
    picking_orders = picking_orders.order_by('-created_at')
    
    # Paginacja
    paginator = Paginator(picking_orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': PickingOrder.PICKING_STATUS,
    }
    return render(request, 'wms/picking_list.html', context)


@login_required
def picking_detail(request, picking_id):
    """Szczegóły zlecenia kompletacji"""
    picking_order = get_object_or_404(PickingOrder, id=picking_id)
    
    context = {
        'picking_order': picking_order,
    }
    return render(request, 'wms/picking_detail.html', context)


@login_required
def start_picking(request, picking_id):
    """Rozpoczęcie kompletacji"""
    picking_order = get_object_or_404(PickingOrder, id=picking_id)
    
    if picking_order.status == 'created':
        picking_order.status = 'in_progress'
        picking_order.started_at = timezone.now()
        picking_order.save()
        
        messages.success(request, f'Rozpoczęto kompletację {picking_order.order_number}')
        return redirect('wms:scan_location', picking_id=picking_id)
    else:
        messages.warning(request, f'Zlecenie {picking_order.order_number} nie może być rozpoczęte (status: {picking_order.get_status_display()})')
    
    return redirect('wms:picking_detail', picking_id=picking_id)


@login_required
def scan_location(request, picking_id):
    picking_order = get_object_or_404(PickingOrder, id=picking_id)
    
    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        
        if barcode:
            # Sprawdź czy lokalizacja istnieje (używając barcode)
            location = Location.objects.filter(barcode=barcode).first()
            
            if location:
                # Sprawdź czy w tej lokalizacji są produkty z tego zlecenia
                picking_items = PickingItem.objects.filter(
                    picking_order=picking_order,
                    location=location
                ).distinct()
                
                if picking_items.exists():
                    # Zapisz location_id w sesji
                    request.session['picking_location_id'] = location.id
                    # Przejdź do skanowania produktów
                    return redirect('wms:scan_product', picking_id=picking_id)
                else:
                    messages.warning(request, f'W lokalizacji {barcode} nie ma produktów do kompletacji.')
            else:
                messages.error(request, f'Lokalizacja {barcode} nie istnieje.')
        else:
            messages.error(request, 'Proszę wprowadzić kod lokalizacji.')
    
    return render(request, 'wms/scan_location.html', {
        'picking_order': picking_order,
        'pending_items': PickingItem.objects.filter(picking_order=picking_order, quantity_picked=0)
    })


@login_required
def scan_product(request, picking_id):
    """Skanowanie produktu"""
    picking_order = get_object_or_404(PickingOrder, id=picking_id)

    # Pobierz location_id z sesji
    location_id = request.session.get('picking_location_id')
    if not location_id:
        messages.error(request, "Najpierw zeskanuj lokalizację!")
        return redirect('wms:scan_location', picking_id=picking_id)

    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        messages.error(request, "Nieprawidłowa lokalizacja!")
        return redirect('wms:scan_location', picking_id=picking_id)

    if request.method == 'POST':
        barcode = request.POST.get('barcode', '').strip()
        
        if barcode:
            try:
                product = Product.objects.get(barcode=barcode)
                
                # Znajdź pozycję kompletacji dla tego produktu w tej lokalizacji
                picking_item = PickingItem.objects.filter(
                    picking_order=picking_order,
                    product=product,
                    location=location,
                    is_completed=False
                ).first()
                
                if picking_item:
                    # Sprawdź stan magazynowy
                    stock = Stock.objects.filter(
                        product=product,
                        location=location
                    ).first()
                    
                    if stock and stock.quantity >= picking_item.quantity_to_pick:
                        # Przekieruj do enter_quantity z item_id
                        return redirect('wms:enter_quantity', picking_id=picking_id, item_id=picking_item.id)
                    else:
                        messages.error(request, f'Niewystarczający stan magazynowy. Dostępne: {stock.quantity if stock else 0}')
                else:
                    messages.error(request, f'Produkt {product.name} nie jest w tej lokalizacji lub już został skompletowany.')
                    
            except Product.DoesNotExist:
                messages.error(request, f'Produkt o kodzie {barcode} nie istnieje.')
        else:
            messages.error(request, 'Proszę wprowadzić kod produktu.')
    
    return render(request, 'wms/scan_product.html', {
        'picking_order': picking_order,
        'location': location,
        'current_item': picking_order.next_item,
        'pending_items': PickingItem.objects.filter(
            picking_order=picking_order, 
            location=location,
            is_completed=False
        )
    })


@login_required
def enter_quantity(request, picking_id, item_id):
    """Wprowadzenie ilości pobranej"""
    picking_order = get_object_or_404(PickingOrder, id=picking_id)
    picking_item = get_object_or_404(PickingItem, id=item_id, picking_order=picking_order)
    
    if request.method == 'POST':
        quantity_picked = request.POST.get('quantity_picked')
        
        try:
            quantity_picked = Decimal(quantity_picked)
            
            if quantity_picked > 0 and quantity_picked <= picking_item.quantity_to_pick:
                with transaction.atomic():
                    # Zapisz historię kompletacji
                    PickingHistory.objects.create(
                        picking_item=picking_item,
                        user=request.user,
                        location_scanned=picking_item.location,
                        product_scanned=picking_item.product,
                        quantity_picked=quantity_picked
                    )
                    
                    # Zaktualizuj pozycję kompletacji
                    picking_item.quantity_picked = quantity_picked
                    picking_item.is_completed = True
                    picking_item.save()
                    
                    # Zmniejsz stan magazynowy
                    stock = Stock.objects.get(
                        product=picking_item.product,
                        location=picking_item.location
                    )
                    stock.quantity -= quantity_picked
                    stock.save()
                    
                    # Zaktualizuj pozycję zamówienia
                    order_item = picking_item.order_item
                    order_item.completed_quantity += quantity_picked
                    order_item.save()
                    
                    messages.success(request, f'Pobrano {quantity_picked} {picking_item.product.name}')
                    
                    # Sprawdź czy to ostatnia pozycja
                    remaining_items = picking_order.items.filter(is_completed=False)
                    if not remaining_items.exists():
                        return redirect('wms:complete_picking', picking_id=picking_id)
                    else:
                        return redirect('wms:scan_location', picking_id=picking_id)
                        
            else:
                messages.error(request, 'Nieprawidłowa ilość.')
                
        except ValueError:
            messages.error(request, 'Nieprawidłowa wartość ilości.')
    
    # Renderuj szablon z danymi
    context = {
        'picking_order': picking_order,
        'current_item': picking_item,
        'product': picking_item.product,
        'stock': Stock.objects.filter(
            product=picking_item.product,
            location=picking_item.location
        ).first(),
        'location': picking_item.location,
        'scan_type': 'quantity',
    }
    return render(request, 'wms/enter_quantity.html', context)


@login_required
def complete_picking(request, picking_id):
    """Zakończenie kompletacji"""
    picking_order = get_object_or_404(PickingOrder, id=picking_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Zakończ zlecenie kompletacji
            picking_order.status = 'completed'
            picking_order.completed_at = timezone.now()
            picking_order.save()
            
            # Sprawdź czy wszystkie pozycje zamówienia zostały zrealizowane
            customer_order = picking_order.customer_order
            all_completed = True
            partially_completed = False
            
            for order_item in customer_order.items.all():
                if order_item.completed_quantity < order_item.quantity:
                    all_completed = False
                    if order_item.completed_quantity > 0:
                        partially_completed = True
            
            # Zaktualizuj status zamówienia
            if all_completed:
                customer_order.status = 'completed'
            elif partially_completed:
                customer_order.status = 'partially_completed'
            customer_order.save()
            
            # Utwórz dokument magazynowy (WZ)
            warehouse_doc = WarehouseDocument.objects.create(
                document_number=f"WZ-{customer_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
                document_type='WZ',
                customer_order=customer_order
            )
            
            # Utwórz pozycje dokumentu
            for picking_item in picking_order.items.all():
                if picking_item.quantity_picked > 0:
                    DocumentItem.objects.create(
                        document=warehouse_doc,
                        product=picking_item.product,
                        location=picking_item.location,
                        quantity=picking_item.quantity_picked,
                        unit_price=picking_item.order_item.unit_price
                    )
            
            messages.success(request, f'Zakończono kompletację. Utworzono dokument WZ {warehouse_doc.document_number}')
            return redirect('wms:order_detail', order_id=customer_order.id)
    
    context = {
        'picking_order': picking_order,
    }
    return render(request, 'wms/complete_picking.html', context)


@login_required
def product_list(request):
    """Lista produktów"""
    search_query = request.GET.get('search', '')
    sync_filter = request.GET.get('sync', '')
    group_filter = request.GET.get('group', '')
    subiekt_filter = request.GET.get('subiekt', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    
    # Filtrowanie po grupie
    if group_filter:
        if group_filter == 'no_group':
            products = products.filter(groups__isnull=True)
        else:
            products = products.filter(groups__id=group_filter)
    
    # Filtrowanie po subiekt_id
    if subiekt_filter:
        if subiekt_filter == 'has_subiekt':
            products = products.filter(subiekt_id__isnull=False)
        elif subiekt_filter == 'no_subiekt':
            products = products.filter(subiekt_id__isnull=True)
        else:
            # Filtrowanie po konkretnym subiekt_id (może być częściowe dopasowanie)
            try:
                # Sprawdź czy to liczba całkowita
                subiekt_id_int = int(subiekt_filter)
                products = products.filter(subiekt_id=subiekt_id_int)
            except ValueError:
                # Jeśli nie jest liczbą, spróbuj dopasować jako string
                products = products.filter(subiekt_id__icontains=subiekt_filter)
    
    # Filtrowanie po statusie synchronizacji
    if sync_filter == 'needs_sync':
        products = products.filter(subiekt_id__isnull=False)
        # Filtrowanie po różnicy stanów (wykonane w Pythonie dla lepszej wydajności)
        products = [p for p in products if p.needs_sync]
    elif sync_filter == 'synced':
        products = products.filter(subiekt_id__isnull=False)
        products = [p for p in products if not p.needs_sync]
    elif sync_filter == 'not_synced':
        products = products.filter(subiekt_id__isnull=True)
    
    # Sprawdź czy products to lista (po filtrowaniu Python) czy QuerySet
    if isinstance(products, list):
        # Jeśli to lista, sortuj w Pythonie
        products.sort(key=lambda x: x.name)
    else:
        # Jeśli to QuerySet, użyj order_by
        products = products.order_by('name')
    
    # Paginacja
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Pobierz wszystkie grupy dla filtra
    groups = ProductGroup.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sync_filter': sync_filter,
        'group_filter': group_filter,
        'subiekt_filter': subiekt_filter,
        'groups': groups,
    }
    return render(request, 'wms/product_list.html', context)


@login_required
def location_list(request):
    """Lista lokalizacji"""
    search_query = request.GET.get('search', '')
    location_type = request.GET.get('type', '')
    
    locations = Location.objects.filter(is_active=True)
    
    if search_query:
        locations = locations.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    if location_type:
        locations = locations.filter(location_type=location_type)
    
    locations = locations.order_by('code')
    
    # Paginacja
    paginator = Paginator(locations, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'location_type': location_type,
        'location_types': Location.LOCATION_TYPES,
    }
    return render(request, 'wms/location_list.html', context)


@login_required
def stock_list(request):
    """Lista stanów magazynowych"""
    search_query = request.GET.get('search', '')
    location_filter = request.GET.get('location', '')
    product_filter = request.GET.get('product', '')
    
    stocks = Stock.objects.select_related('product', 'location').filter(quantity__gt=0)
    
    if search_query:
        stocks = stocks.filter(
            Q(product__code__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(location__code__icontains=search_query)
        )
    
    if location_filter:
        stocks = stocks.filter(location__code=location_filter)
    
    if product_filter:
        stocks = stocks.filter(product__code=product_filter)
    
    stocks = stocks.order_by('location__code', 'product__name')
    
    # Paginacja
    paginator = Paginator(stocks, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'location_filter': location_filter,
        'product_filter': product_filter,
    }
    return render(request, 'wms/stock_list.html', context)


# API endpoints dla skanowania
@login_required
def api_scan_barcode(request):
    """API do skanowania kodów kreskowych"""
    if request.method == 'POST':
        data = json.loads(request.body)
        barcode = data.get('barcode', '').strip()
        scan_type = data.get('scan_type', 'product')
        
        try:
            if scan_type == 'location':
                location = Location.objects.get(barcode=barcode)
                return JsonResponse({
                    'success': True,
                    'type': 'location',
                    'data': {
                        'id': location.id,
                        'code': location.code,
                        'name': location.name,
                        'barcode': location.barcode,
                    }
                })
            else:
                product = Product.objects.get(barcode=barcode)
                return JsonResponse({
                    'success': True,
                    'type': 'product',
                    'data': {
                        'id': product.id,
                        'code': product.code,
                        'name': product.name,
                        'barcode': product.barcode,
                    }
                })
        except (Location.DoesNotExist, Product.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Nie znaleziono obiektu o podanym kodzie kreskowym.'
            })
    
    return JsonResponse({'success': False, 'error': 'Nieprawidłowe żądanie.'})



@login_required
def htmx_sync_product(request, product_id):
    """HTMX view do synchronizacji produktu z Subiektem"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Import subiekt models
            from subiekt.models import tw_Towar
            from decimal import Decimal
            
            # Pobierz produkt z Subiektu
            subiekt_product = tw_Towar.subiekt_objects.get_product_by_id(product.subiekt_id)
            
            if not subiekt_product:
                raise Exception(f'Produkt o ID {product.subiekt_id} nie istnieje w Subiekcie')
            
            # Aktualizuj dane produktu z Subiektu
            product.code = subiekt_product.tw_Symbol
            product.name = subiekt_product.tw_Nazwa
            product.description = subiekt_product.tw_Opis or ''
            product.barcode = subiekt_product.tw_Id
            
            # Aktualizuj stany magazynowe z Subiektu
            product.subiekt_stock = Decimal(str(getattr(subiekt_product, 'st_Stan', 0)))
            product.subiekt_stock_reserved = Decimal(str(getattr(subiekt_product, 'st_StanRez', 0)))
            product.last_sync_date = timezone.now()
            
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
                if wms_group not in product.groups.all():
                    product.groups.add(wms_group)
            
            product.save()
            
            # Create response
            response = render(request, 'wms/partials/sync_success.html', {
                'product': product,
                'subiekt_stock': product.subiekt_stock,
                'subiekt_stock_reserved': product.subiekt_stock_reserved
            })
            
            # Add success toast trigger
            import json
            response['HX-Trigger'] = json.dumps({
                'toastMessage': {'value': f'Produkt {product.name} został zsynchronizowany', 'type': 'success'}
            })
            
            return response
            
        except Exception as e:
            # Create response
            response = render(request, 'wms/partials/sync_error.html', {
                'error': str(e)
            })
            
            # Add error toast trigger
            import json
            response['HX-Trigger'] = json.dumps({
                'toastMessage': {'value': f'Błąd synchronizacji: {str(e)}', 'type': 'error'}
            })
            
            return response
    
    # Create response for invalid method
    response = render(request, 'wms/partials/sync_error.html', {
        'error': 'Metoda nie dozwolona'
    })
    
    # Add error toast trigger
    import json
    response['HX-Trigger'] = json.dumps({
        'toastMessage': {'value': 'Metoda nie dozwolona', 'type': 'error'}
    })
    
    return response


@login_required
def api_product_details(request, product_id):
    """API do pobierania szczegółów produktu"""
    if request.method == 'GET':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Pobierz stany magazynowe w lokalizacjach
            stocks = Stock.objects.filter(product=product).select_related('location')
            
            # Oblicz statystyki
            total_reserved = sum(stock.reserved_quantity for stock in stocks)
            quantities = [stock.quantity for stock in stocks if stock.quantity > 0]
            
            max_stock = max(quantities) if quantities else None
            min_stock = min(quantities) if quantities else None
            avg_stock = sum(quantities) / len(quantities) if quantities else None
            
            # Przygotuj dane lokalizacji
            locations_data = []
            for stock in stocks:
                if stock.quantity > 0 or stock.reserved_quantity > 0:
                    locations_data.append({
                        'code': stock.location.code,
                        'name': stock.location.name,
                        'quantity': float(stock.quantity),
                        'reserved_quantity': float(stock.reserved_quantity),
                        'updated_at': stock.updated_at.strftime('%d.%m.%Y %H:%M') if stock.updated_at else '-'
                    })
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'code': product.code,
                    'barcode': product.barcode,
                    'unit': product.unit,
                    'description': product.description,
                    'total_stock': float(product.total_stock),
                    'subiekt_stock': float(product.subiekt_stock),
                    'stock_difference': float(product.stock_difference),
                    'subiekt_id': product.subiekt_id,

                    'last_sync_date': product.last_sync_date.strftime('%d.%m.%Y %H:%M') if product.last_sync_date else None,
                    'needs_sync': product.needs_sync,
                    'locations_count': len(locations_data),
                    'reserved_stock': float(total_reserved),
                    'max_stock': float(max_stock) if max_stock else None,
                    'min_stock': float(min_stock) if min_stock else None,
                    'avg_stock': float(avg_stock) if avg_stock else None,
                    'locations': locations_data,
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Metoda nie dozwolona'}, status=405)


@login_required
def supplier_order_list(request):
    """Lista zamówień do dostawców (ZD)"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    supplier_orders = SupplierOrder.objects.all()
    
    if search_query:
        supplier_orders = supplier_orders.filter(
            Q(order_number__icontains=search_query) |
            Q(supplier_name__icontains=search_query) |
            Q(supplier_code__icontains=search_query)
        )
    
    if status_filter:
        supplier_orders = supplier_orders.filter(status=status_filter)
    
    context = {
        'supplier_orders': supplier_orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': SupplierOrder.SUPPLIER_STATUS_CHOICES,
    }
    return render(request, 'wms/supplier_order_list.html', context)


@login_required
def supplier_order_detail(request, order_id):
    """Szczegóły zamówienia do dostawcy"""
    supplier_order = get_object_or_404(SupplierOrder, id=order_id)
    
    context = {
        'supplier_order': supplier_order,
        'receiving_orders': supplier_order.receiving_orders.all(),
    }
    return render(request, 'wms/supplier_order_detail.html', context)


@login_required
def create_receiving_order(request, supplier_order_id):
    """Tworzenie rejestru przyjęć (RegIn)"""
    supplier_order = get_object_or_404(SupplierOrder, id=supplier_order_id)
    
    if request.method == 'POST':
        # Sprawdź czy już istnieje aktywny RegIn dla tego ZD
        existing_receiving = ReceivingOrder.objects.filter(
            supplier_order=supplier_order,
            status__in=['pending', 'in_progress']
        ).first()
        
        if existing_receiving:
            messages.warning(request, f'Rejestr przyjęć już istnieje: {existing_receiving.order_number}')
            return redirect('wms:supplier_order_detail', order_id=supplier_order_id)
        
        # Utwórz nowy RegIn
        receiving_order = ReceivingOrder.objects.create(
            order_number=f"RegIn-{supplier_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
            supplier_order=supplier_order,
            status='pending',
            assigned_to=request.user
        )
        
        # Utwórz pozycje RegIn na podstawie pozycji ZD
        sequence = 1
        for supplier_item in supplier_order.items.all():
            ReceivingItem.objects.create(
                receiving_order=receiving_order,
                supplier_order_item=supplier_item,
                product=supplier_item.product,
                quantity_ordered=supplier_item.quantity_ordered,
                quantity_received=0,
                sequence=sequence
            )
            sequence += 1
        
        messages.success(request, f'Utworzono rejestr przyjęć: {receiving_order.order_number}')
        return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)
    
    return redirect('wms:supplier_order_detail', order_id=supplier_order_id)


@login_required
def receiving_order_list(request):
    """Lista rejestrów przyjęć (RegIn)"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    receiving_orders = ReceivingOrder.objects.all()
    
    if search_query:
        receiving_orders = receiving_orders.filter(
            Q(order_number__icontains=search_query) |
            Q(supplier_order__order_number__icontains=search_query) |
            Q(supplier_order__supplier_name__icontains=search_query)
        )
    
    if status_filter:
        receiving_orders = receiving_orders.filter(status=status_filter)
    
    context = {
        'receiving_orders': receiving_orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': ReceivingOrder.RECEIVING_STATUS_CHOICES,
    }
    return render(request, 'wms/receiving_order_list.html', context)


@login_required
def receiving_order_detail(request, receiving_id):
    """Szczegóły rejestru przyjęć"""
    receiving_order = get_object_or_404(ReceivingOrder, id=receiving_id)
    
    context = {
        'receiving_order': receiving_order,
        'pending_items': receiving_order.items.filter(quantity_received=0),
        'received_items': receiving_order.items.filter(quantity_received__gt=0),
        'history': receiving_order.history.all()[:10],  # Ostatnie 10 wpisów
    }
    return render(request, 'wms/receiving_order_detail.html', context)


@login_required
def scan_receiving_location(request, receiving_id):
    """Skanowanie lokalizacji przy przyjmowaniu"""
    receiving_order = get_object_or_404(ReceivingOrder, id=receiving_id)
    
    # Aktualizuj status na 'in_progress' jeśli jest 'pending'
    if receiving_order.status == 'pending':
        receiving_order.status = 'in_progress'
        receiving_order.started_at = timezone.now()
        receiving_order.save()
    
    if request.method == 'POST':
        location_code = request.POST.get('location_code', '').strip()
        
        if location_code:
            # Sprawdź czy lokalizacja istnieje (używając barcode)
            location = Location.objects.filter(barcode=location_code).first()
            
            if location:
                # Sprawdź czy w tej lokalizacji są produkty z tego RegIn
                receiving_items = ReceivingItem.objects.filter(
                    receiving_order=receiving_order
                ).distinct()
                
                if receiving_items.exists():
                    # Zapisz location_id w sesji
                    request.session['receiving_location_id'] = location.id
                    # Przejdź do skanowania produktów
                    return redirect('wms:scan_receiving_product', receiving_id=receiving_id)
                else:
                    messages.warning(request, f'W lokalizacji {location_code} nie ma produktów do przyjęcia.')
            else:
                messages.error(request, f'Lokalizacja {location_code} nie istnieje.')
        else:
            messages.error(request, 'Proszę wprowadzić kod lokalizacji.')
    
    return render(request, 'wms/scan_receiving_location.html', {
        'receiving_order': receiving_order,
        'pending_items': ReceivingItem.objects.filter(receiving_order=receiving_order, quantity_received=0)
    })


@login_required
def scan_receiving_product(request, receiving_id):
    """Skanowanie produktu przy przyjmowaniu"""
    receiving_order = get_object_or_404(ReceivingOrder, id=receiving_id)
    
    # Pobierz location_id z sesji
    location_id = request.session.get('receiving_location_id')
    if not location_id:
        messages.error(request, "Najpierw zeskanuj lokalizację!")
        return redirect('wms:scan_receiving_location', receiving_id=receiving_id)

    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        messages.error(request, "Nieprawidłowa lokalizacja!")
        return redirect('wms:scan_receiving_location', receiving_id=receiving_id)

    if request.method == 'POST':
        product_barcode = request.POST.get('product_barcode', '').strip()
        
        if product_barcode:
            try:
                product = Product.objects.get(barcode=product_barcode)
                
                # Sprawdź czy produkt jest w tym RegIn
                receiving_item = ReceivingItem.objects.filter(
                    receiving_order=receiving_order,
                    product=product
                ).first()
                
                if receiving_item:
                    # Przejdź do wprowadzenia ilości
                    return redirect('wms:enter_receiving_quantity', receiving_id=receiving_id, item_id=receiving_item.id)
                else:
                    messages.error(request, f'Produkt {product.name} nie jest w tym rejestrze przyjęć.')
                    
            except Product.DoesNotExist:
                messages.error(request, f'Produkt o kodzie {product_barcode} nie istnieje.')
        else:
            messages.error(request, 'Proszę wprowadzić kod produktu.')
    
    return render(request, 'wms/scan_receiving_product.html', {
        'receiving_order': receiving_order,
        'pending_items': ReceivingItem.objects.filter(receiving_order=receiving_order, quantity_received=0),
        'location': location
    })


@login_required
def enter_receiving_quantity(request, receiving_id, item_id):
    """Wprowadzenie ilości przyjętej"""
    receiving_order = get_object_or_404(ReceivingOrder, id=receiving_id)
    receiving_item = get_object_or_404(ReceivingItem, id=item_id, receiving_order=receiving_order)
    
    # Pobierz location_id z sesji
    location_id = request.session.get('receiving_location_id')
    if not location_id:
        messages.error(request, "Najpierw zeskanuj lokalizację!")
        return redirect('wms:scan_receiving_location', receiving_id=receiving_id)

    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        messages.error(request, "Nieprawidłowa lokalizacja!")
        return redirect('wms:scan_receiving_location', receiving_id=receiving_id)
    
    if request.method == 'POST':
        quantity_received = request.POST.get('quantity_received', '').strip()
        
        if quantity_received:
            try:
                quantity = Decimal(quantity_received)
                
                if quantity > 0:
                    with transaction.atomic():
                        # Zaktualizuj ilość przyjętą
                        receiving_item.quantity_received += quantity
                        receiving_item.location = location
                        receiving_item.save()
                        
                        # Zaktualizuj ilość w ZD
                        supplier_item = receiving_item.supplier_order_item
                        supplier_item.quantity_received += quantity
                        supplier_item.save()
                        
                        # Zapisz w historii
                        ReceivingHistory.objects.create(
                            receiving_order=receiving_order,
                            product=receiving_item.product,
                            location=location,
                            quantity_received=quantity,
                            scanned_by=request.user
                        )
                        
                        # Aktualizuj stany magazynowe
                        stock, created = Stock.objects.get_or_create(
                            product=receiving_item.product,
                            location=location,
                            defaults={'quantity': 0}
                        )
                        stock.quantity += quantity
                        stock.save()
                        
                        messages.success(request, f'Przyjęto {quantity} szt. {receiving_item.product.name} w {location.name}')
                        
                        # Sprawdź czy wszystkie pozycje zostały przyjęte
                        if receiving_order.received_items == receiving_order.total_items:
                            receiving_order.status = 'completed'
                            receiving_order.completed_at = timezone.now()
                            receiving_order.save()
                            
                            # Utwórz dokument PZ
                            create_warehouse_document(receiving_order)
                            
                            messages.success(request, 'Rejestr przyjęć zakończony. Utworzono dokument PZ.')
                            return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)
                        
                        return redirect('wms:scan_receiving_location', receiving_id=receiving_order.id)
                else:
                    messages.error(request, 'Ilość musi być większa od 0.')
                    
            except (ValueError, TypeError):
                messages.error(request, 'Nieprawidłowa ilość.')
        else:
            messages.error(request, 'Proszę wprowadzić ilość.')
    
    return render(request, 'wms/enter_receiving_quantity.html', {
        'receiving_order': receiving_order,
        'receiving_item': receiving_item,
        'location': location
    })


def create_warehouse_document(receiving_order):
    """Tworzenie dokumentu PZ na podstawie RegIn"""
    supplier_order = receiving_order.supplier_order
    
    # Utwórz dokument PZ
    document = WarehouseDocument.objects.create(
        document_number=f"PZ-{supplier_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
        document_type='PZ',
        supplier_order=supplier_order,
        document_date=timezone.now().date(),
        status='completed',
        notes=f'Utworzone automatycznie z RegIn {receiving_order.order_number}'
    )
    
    # Utwórz pozycje dokumentu
    for receiving_item in receiving_order.items.filter(quantity_received__gt=0):
        DocumentItem.objects.create(
            document=document,
            product=receiving_item.product,
            location=receiving_item.location,
            quantity=receiving_item.quantity_received,
            unit_price=receiving_item.supplier_order_item.unit_price
        )
    
    # Zaktualizuj status ZD
    if supplier_order.is_fully_received:
        supplier_order.status = 'received'
    else:
        supplier_order.status = 'partially_received'
    supplier_order.actual_delivery_date = timezone.now().date()
    supplier_order.save()


@login_required
def complete_receiving(request, receiving_id):
    """Zakończenie rejestru przyjęć"""
    receiving_order = get_object_or_404(ReceivingOrder, id=receiving_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            receiving_order.status = 'completed'
            receiving_order.completed_at = timezone.now()
            receiving_order.save()
            
            # Utwórz dokument PZ
            create_warehouse_document(receiving_order)
            
            messages.success(request, f'Zakończono rejestr przyjęć {receiving_order.order_number}. Utworzono dokument PZ.')
            return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)
    
    return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)


def logout_view(request):
    """Widok wylogowania"""
    logout(request)
    messages.success(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('login')


@login_required
def profile_edit(request):
    """Edycja profilu użytkownika"""
    # Utwórz profil jeśli nie istnieje
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil został zaktualizowany pomyślnie.')
            return redirect('wms:profile_edit')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'wms/profile_edit.html', context)


@login_required
def product_group_list(request):
    """Lista grup produktów"""
    search_query = request.GET.get('search', '')
    
    groups = ProductGroup.objects.all()
    
    if search_query:
        groups = groups.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    groups = groups.order_by('name')
    
    # Paginacja
    paginator = Paginator(groups, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'wms/product_group_list.html', context)


@login_required
def product_group_detail(request, group_id):
    """Szczegóły grupy produktów"""
    group = get_object_or_404(ProductGroup, id=group_id)
    products = Product.objects.filter(groups=group).order_by('name')
    
    context = {
        'group': group,
        'products': products,
    }
    return render(request, 'wms/product_group_detail.html', context)



