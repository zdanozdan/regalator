from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg, Max, Min, Prefetch, F
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.models import User
from decimal import Decimal
from .models import *
from .forms import UserProfileForm, ProductCodeForm, LocationEditForm, LocationImageForm, ProductColorSizeForm, ProductStockInlineFormSet, ProductForm
from assets.models import Asset
import json
import logging
from django.template.loader import render_to_string
from django.urls import reverse
from django.db import IntegrityError
from .signals import product_updated

# Import subiekt models
from subiekt.models import tw_Towar
            

logger = logging.getLogger(__name__)


def login_view(request):
    """Widok logowania"""
    if request.user.is_authenticated:
        return redirect('wms:dashboard')
    
    # Pobierz listę wszystkich użytkowników
    users = User.objects.all().order_by('username')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Sprawdź czy użytkownik musi zmienić hasło
                profile, created = UserProfile.objects.get_or_create(user=user)
                if not profile.password_changed:
                    return redirect('wms:change_password_first_time')
                
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    return render(request, 'wms/login.html', {'form': form, 'users': users})


@login_required
def change_password_first_time(request):
    """Widok zmiany hasła dla użytkowników logujących się po raz pierwszy"""
    # Sprawdź czy użytkownik rzeczywiście musi zmienić hasło
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if profile.password_changed:
        return redirect('wms:dashboard')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            
            # Oznacz że użytkownik zmienił hasło
            profile.password_changed = True
            profile.save()
            
            messages.success(request, 'Hasło zostało pomyślnie zmienione!')
            return redirect('wms:dashboard')
    else:
        form = SetPasswordForm(request.user)
    
    return render(request, 'wms/change_password_first_time.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard główny - wybór procesu"""
    # Pobierz splash image
    splash_image = Asset.get_splash_image()
        
    
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
            order_number=f"Terminacja-{customer_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
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
    
    # Get unique locations that have pending items for this picking order
    locations_with_items = Location.objects.filter(
        pickingitem__picking_order=picking_order,
        pickingitem__quantity_picked__lt=F('pickingitem__quantity_to_pick'),
        is_active=True
    ).distinct().order_by('name')[:10]
    
    return render(request, 'wms/scan_location.html', {
        'picking_order': picking_order,
        'pending_items': PickingItem.objects.filter(picking_order=picking_order, quantity_picked=0),
        'picked_items': PickingItem.objects.filter(picking_order=picking_order, quantity_picked__gt=0),
        'available_locations': locations_with_items
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
        scanned_code = request.POST.get('barcode', '').strip()
        
        if scanned_code:
            # Znajdź produkt po dowolnym kodzie (barcode, QR, etc.)
            product = Product.find_by_code(scanned_code)
            
            if product:
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
            else:
                messages.error(request, f'Produkt o kodzie {scanned_code} nie istnieje.')
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
        ),
        'picked_items': PickingItem.objects.filter(
            picking_order=picking_order,
            quantity_picked__gt=0
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
                        quantity=picking_item.quantity_picked
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
    group_filter = request.GET.get('group_id', '') or request.GET.get('group', '')
    subiekt_filter = request.GET.get('subiekt', '')
    
    # Initialize error list
    errors = []
    
    products = Product.objects.prefetch_related('images', 'parent').all()

    if search_query:
        products = products.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(codes__code__icontains=search_query) |
            Q(variants__icontains=search_query)
        ).distinct()
    
    # Filtrowanie po grupie
    if group_filter:
        if group_filter == 'no_group':
            products = products.filter(groups__isnull=True)
        else:
            try:
                # Try to convert to integer, if it fails, ignore the filter
                group_id = int(group_filter)
                products = products.filter(groups__id=group_id)
            except (ValueError, TypeError):
                products = products.filter(groups__id__icontains=group_filter)
                # If group_filter is not a valid integer, ignore the filter and add error
                errors.append(f'Nieprawidłowy identyfikator grupy: "{group_filter}"')
    
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
                errors.append(f'Nieprawidłowy identyfikator PLU Subiekt: "{subiekt_filter}"')
    
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
    
    # Remove duplicates: only show products without parents, or the first occurrence of each parent
    seen_parent_ids = set()
    unique_products = []
    for product in products:
        # Determine which product to display (parent or self)
        display_product = product.parent if product.parent else product
        
        # Only add if we haven't seen this parent before
        if display_product.id not in seen_parent_ids:
            seen_parent_ids.add(display_product.id)
            unique_products.append(product)
    
    products = unique_products
    
    # Paginacja
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Create dictionary mapping product_id to list of variants (only for current page)
    # Get all unique product IDs from current page
    current_page_product_ids = set()
    for product in page_obj:
        display_product = product.parent if product.parent else product
        current_page_product_ids.add(display_product.id)
    
    # Apply same filters to variants query as main product query
    variants_query = Product.objects.filter(parent_id__in=current_page_product_ids)
    
    # Apply search filter to variants if present
    if search_query:
        variants_query = variants_query.filter(
            Q(code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(codes__code__icontains=search_query)
        ).distinct()
    
    # Apply group filter to variants if present
    if group_filter:
        if group_filter == 'no_group':
            variants_query = variants_query.filter(groups__isnull=True)
        else:
            try:
                # Try to convert to integer, if it fails, ignore the filter
                group_id = int(group_filter)
                variants_query = variants_query.filter(groups__id=group_id)
            except (ValueError, TypeError):
                # If group_filter is not a valid integer, ignore the filter
                # Error already added above, no need to duplicate
                pass
    
    # Apply subiekt filter to variants if present
    if subiekt_filter:
        if subiekt_filter == 'has_subiekt':
            variants_query = variants_query.filter(subiekt_id__isnull=False)
        elif subiekt_filter == 'no_subiekt':
            variants_query = variants_query.filter(subiekt_id__isnull=True)
        else:
            try:
                subiekt_id_int = int(subiekt_filter)
                variants_query = variants_query.filter(subiekt_id=subiekt_id_int)
            except ValueError:
                variants_query = variants_query.filter(subiekt_id__icontains=subiekt_filter)
    
    # Apply sync filter to variants if present
    if sync_filter == 'needs_sync':
        variants_query = variants_query.filter(subiekt_id__isnull=False)
        # Note: needs_sync property filtering would need to be done in Python for variants too
    elif sync_filter == 'synced':
        variants_query = variants_query.filter(subiekt_id__isnull=False)
    elif sync_filter == 'not_synced':
        variants_query = variants_query.filter(subiekt_id__isnull=True)
    
    # Final query with ordering
    variants_query = variants_query.select_related('parent').order_by('parent_id', 'name')
    
    # Build dictionary efficiently
    product_variants_dict = {}
    product_variant_ids_dict = {}
    for variant in variants_query:
        parent_id = variant.parent_id
        if parent_id not in product_variants_dict:
            product_variants_dict[parent_id] = []
            product_variant_ids_dict[parent_id] = []
        product_variants_dict[parent_id].append(variant)
        product_variant_ids_dict[parent_id].append(variant.id)
    
    # Pobierz wszystkie grupy dla filtra
    groups = ProductGroup.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'sync_filter': sync_filter,
        'group_filter': group_filter,
        'subiekt_filter': subiekt_filter,
        'groups': groups,
        'product_variants_dict': product_variants_dict,
        'product_variant_ids_dict': product_variant_ids_dict,
        'errors': errors,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'wms/product_list.html#product-list-table', context)

    return render(request, 'wms/product_list.html', context)


@login_required
def htmx_product_row(request, product_id):
    """HTMX endpoint for displaying product row inline in the next row"""
    product = get_object_or_404(Product, id=product_id)
    context = {
        'display_product': product,
    }
    return render(request, 'wms/product_list.html#product-row-partial', context)

@login_required
def htmx_stock_row(request, product_id):
    """HTMX endpoint for displaying stock row inline in the next row"""
    product = get_object_or_404(Product, id=product_id)
    stock = Stock.objects.get(product=product)
    context = {
        'product': product,
        'stock': stock,
    }
    
    response = HttpResponse(status=200)
    response.content = render(request, 'wms/stock_list.html#stock-row-partial', context)
    return response

@login_required
def location_list(request):
    """Lista lokalizacji"""
    search_query = request.GET.get('search', '')
    location_type = request.GET.get('type', '')

    locations = Location.objects.prefetch_related('images')
    
    if search_query:
        locations = locations.filter(
            Q(name__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )
    
    if location_type:
        locations = locations.filter(location_type=location_type)
    
    locations = locations.order_by('barcode')
    
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

    # Check if request comes from HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'wms/location_list.html#location-table', context)
    
    return render(request, 'wms/location_list.html', context)


@login_required
def barcodes_list(request):
    """Lista kodów produktów"""
    search_query = request.GET.get('search', '')
    code_type_filter = request.GET.get('type', '')

    barcodes = ProductCode.objects.select_related('product').filter(is_active=True)
    
    if search_query:
        barcodes = barcodes.filter(
            Q(code__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(product__code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if code_type_filter:
        barcodes = barcodes.filter(code_type=code_type_filter)
    
    barcodes = barcodes.order_by('product__name', 'code')
    
    # Paginacja
    paginator = Paginator(barcodes, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'code_type_filter': code_type_filter,
        'code_types': ProductCode.CODE_TYPES,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'wms/barcodes_list.html#barcodes-table', context)

    return render(request, 'wms/barcodes_list.html', context)


@login_required
def stock_list(request):
    """Lista stanów magazynowych"""
    search_query = request.GET.get('search', '')
    location_filter = request.GET.get('location', '')
    product_filter = request.GET.get('product', '')
    product_id = request.GET.get('product_id', '')
    subiekt_id_filter = request.GET.get('subiekt_id', '')

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        product = None
    except ValueError:
        product = None
    
    stocks = Stock.objects.select_related('product', 'location').filter(quantity__gt=0)
    
    if search_query:
        stocks = stocks.filter(
            Q(product__code__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(location__barcode__icontains=search_query) |
            Q(product__codes__code__icontains=search_query)
        ).distinct()
    
    if location_filter:
        stocks = stocks.filter(location__name__icontains=location_filter)
    
    if product_filter:
        stocks = stocks.filter(product__code=product_filter)

    if product_id:
        stocks = stocks.filter(product__id=product_id)
    
    if subiekt_id_filter:
        stocks = stocks.filter(
            Q(product__subiekt_id=subiekt_id_filter) |
            Q(product__parent__subiekt_id=subiekt_id_filter)
        )
    
    stocks = stocks.order_by('location__barcode', 'product__name')
    
    # Paginacja
    paginator = Paginator(stocks, 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all active locations for the dropdown
    locations = Location.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'location_filter': location_filter,
        'product_filter': product_filter,
        'subiekt_id_filter': subiekt_id_filter,
        'product': product,
        'locations': locations,
    }

    # Check if request comes from HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'wms/stock_list.html#stock-table', context)
    
    return render(request, 'wms/stock_list.html', context)


# API endpoints dla skanowania
@login_required
def api_scan_barcode(request):
    """API do skanowania kodów kreskowych i QR"""
    if request.method == 'POST':
        data = json.loads(request.body)
        scanned_code = data.get('barcode', '').strip()
        scan_type = data.get('scan_type', 'product')
        
        try:
            if scan_type == 'location':
                location = Location.objects.get(barcode=scanned_code)
                return JsonResponse({
                    'success': True,
                    'type': 'location',
                    'data': {
                        'id': location.id,
                        'code': location.barcode,
                        'name': location.name,
                        'barcode': location.barcode,
                    }
                })
            else:
                # Znajdź produkt po dowolnym kodzie (barcode, QR, etc.)
                product = Product.find_by_code(scanned_code)
                if product:
                    return JsonResponse({
                        'success': True,
                        'type': 'product',
                        'data': {
                            'id': product.id,
                            'code': product.code,
                            'name': product.name,
                        }
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Nie znaleziono produktu o podanym kodzie.'
                    })
        except Location.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Nie znaleziono lokalizacji o podanym kodzie kreskowym.'
            })
    
    return JsonResponse({'success': False, 'error': 'Nieprawidłowe żądanie.'})



@login_required
def htmx_sync_product(request, product_id, stock_id=None):
    """HTMX view do synchronizacji produktu z Subiektem"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)

            # Pobierz produkt z Subiektu
            subiekt_product = tw_Towar.subiekt_objects.get_product_by_id(product.subiekt_id)

            if not subiekt_product:
                raise Exception(f'Produkt o ID {product.subiekt_id} nie istnieje w Subiekcie')
            
            # Aktualizuj dane produktu z Subiektu
            product.code = subiekt_product.tw_Symbol
            product.name = subiekt_product.tw_Nazwa
            product.description = subiekt_product.tw_Opis or ''
            
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
                        'description': f'Grupa z Subiekta: {subiekt_group}',
                        'color': '#007bff',  # Domyślny kolor
                    }
                )
                
                if wms_group not in product.groups.all():
                    product.groups.add(wms_group)
            
            product.save()
            
            # Create response
            response = render(request, 'wms/product_list.html#product-row', {
                'product': product,
                'subiekt_stock': product.subiekt_stock,
                'subiekt_stock_reserved': product.subiekt_stock_reserved
            })
            
            # Add success toast trigger
            response['HX-Trigger'] = json.dumps({
                'toastMessage': {'value': f'Produkt {product.name} został zsynchronizowany. Stan w Subiekcie: {product.subiekt_stock}', 'type': 'success'},
                'subiekt-stock-synced-'+str(product.id): {'value': 'true'}
            })
            
            return response
            
        except Exception as e:            # Add error toast trigger
            response = HttpResponse(status=500)
            response['HX-Trigger'] = json.dumps({
                'toastMessage': {'value': f'Błąd synchronizacji: {str(e)}', 'type': 'danger'}
            })
            
            return response
    
    # Add error toast trigger
    response['HX-Trigger'] = json.dumps({
        'toastMessage': {'value': 'Metoda nie dozwolona', 'type': 'danger'}
    })
    
    return response

@login_required
def htmx_product_details(request, product_id):
    """HTMX view do pobierania szczegółów produktu"""
    if request.method == 'GET':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Pobierz stany magazynowe w lokalizacjach
            stocks = Stock.objects.filter(product=product).select_related('location')
            
            # Pobierz kody produktu (barcodes, QR codes)
            product_codes = product.codes.filter(is_active=True).order_by('code_type', 'code')
            
            # Oblicz statystyki
            total_reserved = sum(stock.reserved_quantity for stock in stocks)
            quantities = [stock.quantity for stock in stocks if stock.quantity > 0]
            
            max_stock = max(quantities) if quantities else None
            min_stock = min(quantities) if quantities else None
            avg_stock = sum(quantities) / len(quantities) if quantities else None
            
            # Oblicz statystyki dla HTML
            total_stock = sum(stock.quantity for stock in stocks)
            locations_count = stocks.values('location').distinct().count()
            
            # Oblicz różnicę z Subiektem
            stock_difference = 0
            if product.subiekt_stock is not None:
                stock_difference = total_stock - product.subiekt_stock
            
            # Calculate available stock for each stock item
            for stock in stocks:
                stock.available_quantity = stock.quantity - stock.reserved_quantity
            
            context = {
                'product': product,
                'stocks': stocks,
                'product_codes': product_codes,
                'total_stock': total_stock,
                'locations_count': locations_count,
                'stock_difference': stock_difference,
                'total_reserved': total_reserved,
                'max_stock': max_stock,
                'min_stock': min_stock,
                'avg_stock': avg_stock,
            }
            
            # Create response
            response = render(request, 'wms/partials/product_details_modal.html', context)
            
            # Add modal trigger
            response['HX-Trigger'] = json.dumps({
                'modalMessage': {
                    'title': f'Szczegóły produktu: {product.name}',
                    #'body': response.content.decode('utf-8')
                }
            })
            
            return response
            
        except Exception as e:
            # Create error response
            response = render(request, 'wms/partials/error_modal.html', {
                'error': str(e)
            })
            
            # Add modal trigger
            response['HX-Trigger'] = json.dumps({
                'modalMessage': {
                    'title': 'Błąd',
                    'body': f'Wystąpił błąd podczas ładowania szczegółów produktu: {str(e)}'
                }
            })
            
            return response
    
    # Create response for invalid method
    response = render(request, 'wms/partials/error_modal.html', {
        'error': 'Metoda nie dozwolona'
    })
    
    # Add modal trigger
    response['HX-Trigger'] = json.dumps({
        'modalMessage': {
            'title': 'Błąd',
            'body': 'Metoda nie dozwolona'
        }
    })
    
    return response


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
def sync_zd_orders(request):
    """Sync ZD orders from Subiekt"""
    if request.method != 'POST':
        messages.error(request, 'Nieprawidłowa metoda żądania')
        return redirect('wms:supplier_order_list')
    
    try:
        from subiekt.models import dok_Dokument
        from wms.utils import get_or_create_product_from_subiekt
        from decimal import Decimal
        
        # Get the latest document_id from SupplierOrder
        latest_document_id = SupplierOrder.objects.filter(
            document_id__isnull=False
        ).order_by('-document_id').values_list('document_id', flat=True).first() or 0

        if latest_document_id == 0:
            subiekt_zd_documents = dok_Dokument.dokument_objects.get_zd(limit=20)
        else:
            subiekt_zd_documents = dok_Dokument.dokument_objects.get_new_zd(
                latest_document_id=latest_document_id, 
                limit=20
            )
        
        if not subiekt_zd_documents:
            messages.info(request, 'Brak nowych dokumentów ZD do synchronizacji')
            return redirect('wms:supplier_order_list')
        
        new_orders = []
        updated_orders = []
        
        for zd_doc in subiekt_zd_documents:
            try:
                # Check if order already exists
                existing_order = SupplierOrder.objects.filter(order_number=zd_doc.dok_NrPelny).first()
                
                if existing_order:
                    # Check if order needs updating
                    new_supplier_name = zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna or 'Nieznany dostawca'
                    new_order_date = zd_doc.dok_DataWyst or timezone.now().date()
                    new_expected_delivery_date = zd_doc.dok_PlatTermin or zd_doc.dok_DataMag or zd_doc.dok_DataWyst or timezone.now().date()
                    new_actual_delivery_date = zd_doc.dok_DataOtrzym
                    new_notes = f'ZD z Subiektu: {zd_doc.dok_NrPelny}'
                    
                    # Only update if there are actual changes
                    new_document_number = zd_doc.dok_Nr
                    new_document_id = zd_doc.dok_Id
                    if (existing_order.supplier_name != new_supplier_name or
                        existing_order.order_date != new_order_date or
                        existing_order.expected_delivery_date != new_expected_delivery_date or
                        existing_order.actual_delivery_date != new_actual_delivery_date or
                        existing_order.notes != new_notes or
                        existing_order.document_number != new_document_number or
                        existing_order.document_id != new_document_id):
                        
                        existing_order.supplier_name = new_supplier_name
                        existing_order.supplier_code = ''
                        existing_order.document_number = new_document_number  # Store original document number
                        existing_order.document_id = new_document_id  # Store document ID
                        existing_order.order_date = new_order_date
                        existing_order.expected_delivery_date = new_expected_delivery_date
                        existing_order.actual_delivery_date = new_actual_delivery_date
                        existing_order.notes = new_notes
                        existing_order.updated_at = timezone.now()
                        existing_order.save()
                        updated_orders.append(existing_order.order_number)
                else:
                    # Create new order
                    supplier_order = SupplierOrder.objects.create(
                        order_number=zd_doc.dok_NrPelny,
                        document_number=zd_doc.dok_Nr,  # Store original document number
                        document_id=zd_doc.dok_Id,  # Store document ID
                        supplier_name=zd_doc.adr_Nazwa or zd_doc.adr_NazwaPelna or 'Nieznany dostawca',
                        supplier_code='',
                        order_date=zd_doc.dok_DataWyst or timezone.now().date(),
                        expected_delivery_date=zd_doc.dok_PlatTermin or zd_doc.dok_DataMag or zd_doc.dok_DataWyst or timezone.now().date(),
                        actual_delivery_date=zd_doc.dok_DataOtrzym,
                        status='pending',
                        notes=f'ZD z Subiektu: {zd_doc.dok_NrPelny}',
                        is_new=True  # Mark as new
                    )
                    new_orders.append(supplier_order.order_number)
                    
                    # Try to sync order items if available
                    try:
                        zd_positions = dok_Dokument.dokument_objects.get_zd_pozycje(zd_doc.dok_Id)
                        
                        if zd_positions:
                            for position in zd_positions:
                                product = get_or_create_product_from_subiekt(position['tw_Id'])
                                
                                if product:
                                    SupplierOrderItem.objects.get_or_create(
                                        supplier_order=supplier_order,
                                        product=product,
                                        defaults={
                                            'quantity_ordered': Decimal(str(position.get('ob_Ilosc', 0))),
                                            'quantity_received': 0,
                                            'notes': f'Pozycja z Subiektu: {position.get("ob_Id", "")}'
                                        }
                                    )
                    except Exception as e:
                        # Log error but continue with order creation
                        pass
                
            except Exception as e:
                # Log error but continue with other orders
                continue
        
        # Add success messages
        if new_orders:
            order_list = ', '.join(new_orders)
            messages.success(request, f'Załadowano {len(new_orders)} nowych zamówień ZD: {order_list}')
        
        if updated_orders:
            messages.info(request, f'Zaktualizowano {len(updated_orders)} istniejących zamówień')
        
        if not new_orders and not updated_orders:
            messages.warning(request, 'Brak nowych zamówień do załadowania')
        
        return redirect('wms:supplier_order_list')
        
    except Exception as e:
        messages.error(request, f'Błąd podczas synchronizacji: {str(e)}')
        return redirect('wms:supplier_order_list')


@login_required
def htmx_delete_supplier_order(request, order_id):
    """HTMX action to delete a supplier order"""
    if request.method != 'DELETE':
        response = HttpResponse(status=405)
        response['HX-Trigger'] = json.dumps({
            'toastMessage': {
                'type': 'danger',
                'value': 'Metoda nie dozwolona'
            }
        })
        return response
    
    try:
        supplier_order = get_object_or_404(SupplierOrder, id=order_id)
        order_number = supplier_order.order_number
        supplier_name = supplier_order.supplier_name
        
        # Delete the order
        supplier_order.delete()
        
        # Return empty response to remove the row, with toast
        response = HttpResponse(status=200)
        response['HX-Trigger'] = json.dumps({
            'toastMessage': {
                'type': 'success',
                'value': f'✓ Usunięto zamówienie ZD {order_number} - {supplier_name}'
            }
        })
        return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        response['HX-Trigger'] = json.dumps({
            'toastMessage': {
                'type': 'danger',
                'value': f'✗ Błąd podczas usuwania zamówienia: {str(e)}'
            }
        })
        return response


@login_required
def create_receiving_order(request, supplier_order_id):
    """Tworzenie rejestru przyjęć (Regalacja)"""
    supplier_order = get_object_or_404(SupplierOrder, id=supplier_order_id)
    
    if request.method == 'POST':
        # Sprawdź czy już istnieje aktywna Regalacja dla tego ZD
        existing_receiving = ReceivingOrder.objects.filter(
            supplier_order=supplier_order,
            status__in=['pending', 'in_progress']
        ).first()
        
        if existing_receiving:
            messages.warning(request, f'Regalacja już istnieje: {existing_receiving.order_number}')
            return redirect('wms:supplier_order_detail', order_id=supplier_order_id)
        
        # Utwórz nową Regalację
        receiving_order = ReceivingOrder.objects.create(
            order_number=f"Regalacja-{supplier_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
            supplier_order=supplier_order,
            status='pending',
            assigned_to=request.user
        )
        
        # Automatycznie oznacz zamówienie jako przeczytane
        supplier_order.is_new = False
        supplier_order.save()
        
        # Utwórz pozycje Regalacji na podstawie pozycji ZD
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
        
        messages.success(request, f'Utworzono regalację: {receiving_order.order_number}')
        return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)
    
    return redirect('wms:supplier_order_detail', order_id=supplier_order_id)


@login_required
def receiving_order_list(request):
    """Lista rejestrów przyjęć (Regalacja)"""
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
                # Sprawdź czy w tej lokalizacji są produkty z tej Regalacji
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
    
    # Get active locations for receiving (can receive to any location)
    available_locations = Location.objects.filter(
        is_active=True
    ).order_by('name')[:10]
    
    return render(request, 'wms/scan_receiving_location.html', {
        'receiving_order': receiving_order,
        'pending_items': ReceivingItem.objects.filter(receiving_order=receiving_order, quantity_received=0),
        'received_items': ReceivingItem.objects.filter(receiving_order=receiving_order, quantity_received__gt=0),
        'available_locations': available_locations
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
        scanned_code = request.POST.get('product_barcode', '').strip()
        
        if scanned_code:
            # Znajdź produkt po dowolnym kodzie (barcode, QR, etc.)
            product = Product.find_by_code(scanned_code)
            
            if product:
                # Sprawdź czy produkt jest w tej Regalacji
                receiving_item = ReceivingItem.objects.filter(
                    receiving_order=receiving_order,
                    product=product
                ).first()
                
                if receiving_item:
                    # Przejdź do wprowadzenia ilości
                    return redirect('wms:enter_receiving_quantity', receiving_id=receiving_id, item_id=receiving_item.id)
                else:
                    messages.error(request, f'Produkt {product.name} nie jest w tym rejestrze przyjęć.')
            else:
                messages.error(request, f'Produkt o kodzie {scanned_code} nie istnieje.')
        else:
            messages.error(request, 'Proszę wprowadzić kod produktu.')
    
    return render(request, 'wms/scan_receiving_product.html', {
        'receiving_order': receiving_order,
        'pending_items': ReceivingItem.objects.filter(receiving_order=receiving_order, quantity_received=0),
        'received_items': ReceivingItem.objects.filter(receiving_order=receiving_order, quantity_received__gt=0),
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
    """Tworzenie dokumentu PZ na podstawie Regalacji"""
    supplier_order = receiving_order.supplier_order
    
    # Utwórz dokument PZ
    document = WarehouseDocument.objects.create(
        document_number=f"PZ-{supplier_order.order_number}-{timezone.now().strftime('%Y%m%d%H%M')}",
        document_type='PZ',
        supplier_order=supplier_order,
        document_date=timezone.now().date(),
        status='completed',
        notes=f'Utworzone automatycznie z Regalacji {receiving_order.order_number}'
    )
    
    # Utwórz pozycje dokumentu
    for receiving_item in receiving_order.items.filter(quantity_received__gt=0):
        DocumentItem.objects.create(
            document=document,
            product=receiving_item.product,
            location=receiving_item.location,
            quantity=receiving_item.quantity_received
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
    """Zakończenie regalacji"""
    receiving_order = get_object_or_404(ReceivingOrder, id=receiving_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            receiving_order.status = 'completed'
            receiving_order.completed_at = timezone.now()
            receiving_order.save()
            
            # Utwórz dokument PZ
            create_warehouse_document(receiving_order)
            
            messages.success(request, f'Zakończono regalację {receiving_order.order_number}. Utworzono dokument PZ.')
            return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)
    
    return redirect('wms:receiving_order_detail', receiving_id=receiving_order.id)


def logout_view(request):
    """Widok wylogowania"""
    logout(request)
    messages.success(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('wms:login')


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


@login_required
def htmx_edit_product_codes(request, product_id, code_id=None):
    """Edycja kodów produktu z możliwością skanowania"""
    product = get_object_or_404(Product, id=product_id)    
    # Get existing codes
    product_codes = product.codes.all().order_by('code_type', 'code')
    
    # If code_id is provided, we're editing an existing code
    editing_code = None
    if code_id:
        editing_code = get_object_or_404(ProductCode, id=code_id, product=product)

    context = {
        'product': product,
        'product_codes': product_codes,
        'code_types': ProductCode.CODE_TYPES,
        'form': ProductCodeForm(product=product, instance=editing_code),
        'editing_code': editing_code,
    }
    
    # Handle POST request for form submission
    if request.method == 'POST':
        form = ProductCodeForm(request.POST, product=product, instance=editing_code)
        context['form'] = form
        context['editing_code'] = editing_code
        
        if form.is_valid():
            code = form.save(commit=False)
            code.product = product
            code.save()
                    
                    
            context['editing_code'] = None
            context['form'] = ProductCodeForm(product=product)
                    
            response = HttpResponse(status=200)
            response.content = render(request, 'wms/partials/_product_codes_modal.html', context)
            response['HX-Trigger'] = json.dumps({
                'toastMessage': {
                    'value': 'Kod zapisany pomyślnie!',
                    'type': 'success'
                },
                'barcodes-list-updated': {
                    'value': 'barcodes-list-updated'
                }
            })

            return response                

    response = HttpResponse(status=200)
    response.content = render(request, 'wms/partials/_product_codes_modal.html', context)

    response['HX-Trigger'] = json.dumps({
        'modalMessage': {
            'title': f'Kody produktu - {product.name}',
            #'body': response.content.decode('utf-8')
        },
    })

    return response

@login_required
def api_add_scanned_code(request, product_id):
    """API endpoint for adding scanned codes"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            data = json.loads(request.body)
            scanned_code = data.get('code', '').strip()
            code_type = data.get('type', 'barcode')
            
            if not scanned_code:
                return JsonResponse({'success': False, 'error': 'Brak kodu do dodania'})
            
            # Check if code already exists
            if ProductCode.objects.filter(code=scanned_code).exists():
                return JsonResponse({'success': False, 'error': f'Kod {scanned_code} już istnieje w systemie'})
            
            # Create new code
            ProductCode.objects.create(
                product=product,
                code=scanned_code,
                code_type=code_type,
                description=f'Dodano przez skanowanie ({code_type})',
            )
            
            response = JsonResponse({
                'success': True, 
                'message': f'Dodano kod {scanned_code}',
                'code': scanned_code,
                'type': code_type
            })
            
            # Add HTMX trigger for product codes list refresh
            response['HX-Trigger'] = json.dumps({
                "product-codes-list": {
                    "value": "product-codes-list"
                }
            })
            
            return response
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Nieprawidłowe żądanie'})


@login_required
def htmx_add_code_modal(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Create form instance
    form = ProductCodeForm(product=product)
    
    context = {
        'product': product,
        'code_types': ProductCode.CODE_TYPES,
        'form': form
    }

    response = HttpResponse(status=200)

    if request.method == 'POST':
        # Handle form submission
        action = request.POST.get('action')
        code_id = request.POST.get('code_id')
        
        if action == 'add':
            # Use form for validation
            form = ProductCodeForm(request.POST, product=product)
            if form.is_valid():
                
                # Create new code
                form.instance.product = product
                form.save()
                
                toast_message = {
                    "toastMessage": {
                        "value": f"Dodano kod: {form.cleaned_data['code']}",
                        "type": "success"
                    },
                    "product-codes-list": {
                        "value": "product-codes-list"
                    }
                }
                response['HX-Trigger'] = json.dumps(toast_message)

            else:
                # Form validation failed
                context['form'] = form
                response.content = render(request, 'wms/partials/_product_codes_modal.html', context)
                return response


        #return HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_product_codes_modal.html', context)
        return response

    # Create response
    response.content = render(request, 'wms/partials/_product_codes_modal.html', context)
            
    # Add modal trigger
    response['HX-Trigger'] = json.dumps({
        'modalMessage': {
            'title': f'Dodaj kod ręcznie',
            #'body': response.content.decode('utf-8')
        }
    })

    return response

@login_required
def htmx_delete_code(request, product_id, code_id):
    if request.method == 'DELETE':
        try:
            product = get_object_or_404(Product, id=product_id)
            code = get_object_or_404(ProductCode, id=code_id, product=product)
            code_value = code.code
            code.delete()           
            
            # Create response
            response = HttpResponse(status=200)
            
            # Add toast message header
            toast_message = {
                "toastMessage": {
                    "value": f"Usunięto kod: {code_value}",
                    "type": "success"
                },
                "product-codes-list": {
                    "value": "product-codes-list"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            
            return response
        except ProductCode.DoesNotExist:
            # Handle error with toast
            response = HttpResponse(status=404)
            toast_message = {
                "toastMessage": {
                    "value": "Nie znaleziono kodu do usunięcia",
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        except Exception as e:
            # Handle other errors with toast
            response = HttpResponse(status=500)
            toast_message = {
                "toastMessage": {
                    "value": f"Błąd podczas usuwania kodu: {str(e)}",
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response

    # For non-DELETE requests
    response = HttpResponse(status=405) # Method not allowed
    toast_message = {
        "toastMessage": {
            "value": "Nieprawidłowe żądanie",
            "type": "danger"
        }
    }
    response['HX-Trigger'] = json.dumps(toast_message)
    return response


@login_required
def htmx_product_codes_list(request, product_id):
    """HTMX endpoint for refreshing product codes list"""
    product = get_object_or_404(Product, id=product_id)
    product_codes = product.codes.all().order_by('code_type', 'code')

    context = {
        'product': product,
        'product_codes': product_codes,
    }
    
    return render(request, 'wms/partials/_product_codes_modal.html#product_codes_list', context)

@login_required
def htmx_add_code_inline(request, product_id):
    """HTMX endpoint for adding scanned codes inline from barcode scanner"""
    context = {}

    response = HttpResponse(status=200)

    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            scanned_code = request.POST.get('code', '').strip()
            scanner_active = request.POST.get('scanner_active', 'false')

            if scanner_active == 'false':
                toast_message = {
                    "toastMessage": {
                        "value": "Skaner został zatrzymany. Uruchom skaner aby dodać kody.",
                        "type": "danger"
                    }
                }
                context['success'] = False
                context['message'] = 'Skaner został zatrzymany. Uruchom skaner aby dodać kody.'
                response.content = render(request, 'wms/partials/_product_codes_modal.html', context)
                response['HX-Trigger'] = json.dumps(toast_message)
                return response
            
            if not scanned_code:
                context['success'] = False
                context['message'] = 'Brak kodu do dodania'
                return render(request, 'wms/partials/_product_codes_modal.html', context)

            new_code = ProductCode.objects.create(
                product=product,
                code=scanned_code,
                code_type='barcode',
                description=f'Zeskanowano: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")} przez {request.user.username}',
  # Don't make scanned codes primary by default
            )
            
            # Return success response
            context['success'] = True
            context['message'] = f'Dodano zeskanowany kod: {scanned_code}'
            context['code_id'] = new_code.id
            context['code'] = new_code.code
            reload_codes = {
                "product-codes-list": {
                    "value": "product-codes-list"
                }
            }
            response.content = render(request, 'wms/partials/_product_codes_modal.html', context)
            response['HX-Trigger'] = json.dumps(reload_codes)
            return response
            
        except IntegrityError as e:
            code = ProductCode.objects.get(code=scanned_code)
            context['success'] = False
            if code.product == product:
                context['message'] = f'Kod {scanned_code} już istnieje dla tego produktu'
            else:
                context['message'] = f'Kod {scanned_code} już jest używany dla produktu {code.product.name}'

            return render(request, 'wms/partials/_product_codes_modal.html', context)
        except Exception as e:
            context['success'] = False
            context['message'] = f'Błąd podczas dodawania kodu: {str(e)}'
            return render(request, 'wms/partials/_product_codes_modal.html', context)
    
    context['success'] = False
    context['message'] = 'Nieprawidłowe żądanie'
    return render(request, 'wms/partials/_product_codes_modal.html', context)


@login_required
def htmx_location_edit(request, location_id=None):
    """HTMX endpoint for creating/editing location - returns edit form"""
    location = None
    if location_id:
        location = get_object_or_404(Location, id=location_id)
    
    if request.method == 'GET':
        form = LocationEditForm(instance=location, location=location)
        
        context = {
            'form': form,
            'location': location,
        }

        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_location_edit_form.html', context)

        response['HX-Trigger'] = json.dumps({
            'modalMessage': {
                'title': 'Nowa lokalizacja' if not location else 'Edycja lokalizacji',
                #'body': response.content.decode('utf-8')
            },
        })

        return response
    
    # Handle POST for form submission
    if request.method == 'POST':
        form = LocationEditForm(request.POST, instance=location, location=location)

        context = {
                'form': form,
                'location': location,
            }
        
        if form.is_valid():
            try:
                form.save()
                
                # Return success response with updated row
                response = HttpResponse(status=200)
                toast_message = {
                    "toastMessage": {
                        "value": "Lokalizacja została utworzona" if not location else "Lokalizacja została zaktualizowana",
                        "type": "success"
                    },
                    'modalHide': {
                        'value': 'modalHide'
                    },
                    "location-list-updated": {
                        "value": "location-list-updated"
                    }
                }
                response['HX-Trigger'] = json.dumps(toast_message)
                return response
                
            except Exception as e:
                context = {
                    'form': form,
                    'location': location,
                    'error': f'Błąd podczas zapisu formularza: {str(e)}'
                }
           
        return render(request, 'wms/partials/_location_edit_form.html', context)
    
    return HttpResponse(status=405)  # Method not allowed


@login_required
def htmx_location_delete(request, location_id):
    """HTMX endpoint for deleting location"""
    if request.method != 'DELETE':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        location = get_object_or_404(Location, id=location_id)
        
        # Check if location has any stock
        if Stock.objects.filter(location=location).exists():
            response = HttpResponse(status=400)
            toast_message = {
                "toastMessage": {
                    "value": "Nie można usunąć lokalizacji z produktami w magazynie",
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        
        # Check if location has child locations
        if Location.objects.filter(parent=location).exists():
            response = HttpResponse(status=400)
            toast_message = {
                "toastMessage": {
                    "value": "Nie można usunąć lokalizacji z podlokalizacjami",
                    "type": "danger"
                },
                "location-list-updated": {
                    "value": "location-list-updated"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        
        location_name = location.name
        location.delete()
        
        response = HttpResponse(status=200)
        toast_message = {
            "toastMessage": {
                "value": f"Lokalizacja {location_name} została usunięta",
                "type": "success"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas usuwania lokalizacji: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_location_photos(request, location_id):
    """HTMX endpoint for viewing location photos - returns photos modal"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        location = get_object_or_404(Location, id=location_id)
        photos = location.images.all().order_by('created_at')
        
        # Create form for uploading new photos
        upload_form = LocationImageForm(location=location, is_edit=False)
        
        context = {
            'location': location,
            'photos': photos,
            'upload_form': upload_form,
        }

        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_location_photos_modal.html', context)

        
        response['HX-Trigger'] = json.dumps({
            'modalMessage': {
                'title': f'Zdjęcia lokalizacji: {location.name}',
                #'body': response.content.decode('utf-8')
            }
        })

        return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas ładowania zdjęć: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_location_photo_upload(request, location_id):
    """HTMX endpoint for uploading location photos"""
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        location = get_object_or_404(Location, id=location_id)
        
        # Use the new form for validation and processing
        form = LocationImageForm(request.POST, request.FILES, location=location, is_edit=False)
        
        if form.is_valid():
            # Save the photo using the form's save method
            photo = form.save()
            
            # Refresh photos list
            photos = location.images.all().order_by('created_at')
            upload_form = LocationImageForm(location=location, is_edit=False)
            
            context = {
                'location': location,
                'photos': photos,
                'upload_form': upload_form,
            }
            
            response = HttpResponse(status=200)
            response.content = render(request, 'wms/partials/_location_photos_modal.html', context)
            
            toast_message = {
                "toastMessage": {
                    "value": "Zdjęcie zostało dodane",
                    "type": "success"
                },
                "location-list-updated": {
                    "value": "location-list-updated"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        else:
            # Form validation failed
            photos = location.images.all().order_by('created_at')
            context = {
                'location': location,
                'photos': photos,
                'upload_form': form,  # Pass the form with errors
            }
            
            response = HttpResponse(status=400)
            response.content = render(request, 'wms/partials/_location_photos_modal.html', context)
            
            # Get first error message
            first_error = next(iter(form.errors.values()))[0] if form.errors else "Błąd walidacji formularza"
            toast_message = {
                "toastMessage": {
                    "value": first_error,
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas dodawania zdjęcia: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_location_photo_update(request, location_id):
    """HTMX endpoint for updating location photo details"""

    response = HttpResponse(status=200)

    try:
        location = get_object_or_404(Location, id=location_id)
        photo_id = request.GET.get('photo_id') or request.POST.get('photo_id')
        if not photo_id:
            response = HttpResponse(status=400)
            toast_message = {
                "toastMessage": {
                    "value": "Brak ID zdjęcia",
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        
        photo = get_object_or_404(LocationImage, id=photo_id, location=location)

        if request.method == 'GET':
            form = LocationImageForm(location=location, instance=photo, is_edit=True)
            context = {
                'location': location,
                'photo': photo,
                'upload_form': form,
            }
            response = HttpResponse(status=200)
            response.content = render(request, 'wms/partials/_location_photo_edit_modal.html', context)
            return response
        
        if request.method == 'POST':
        # Use the new form for validation and processing
            form = LocationImageForm(request.POST, location=location, instance=photo, is_edit=True)
        
            if form.is_valid():
            # Save the photo using the form's save method
                form.save()
                context = {
                    'location': location,
                    'photo': photo,
                    'upload_form': form,
                }
            
                response.content = render(request, 'wms/partials/_location_photo_edit_modal.html', context)
            
                toast_message = {
                    "toastMessage": {
                        "value": "Zdjęcie zostało zaktualizowane",
                        "type": "success"
                    }
                }
                response['HX-Trigger'] = json.dumps(toast_message)
                return response
            else:
                context = {
                    'location': location,
                    'photo': photo,
                    'upload_form': form,
                }

                toast_message = {
                    "toastMessage": {
                        "value": "Błąd podczas aktualizacji zdjęcia",
                        "type": "danger"
                    }
                }
                response['HX-Trigger'] = json.dumps(toast_message)
                response.content = render(request, 'wms/partials/_location_photo_edit_modal.html', context)
                return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas aktualizacji zdjęcia: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_location_photo_set_primary(request, location_id):
    """HTMX endpoint for setting location photo as primary"""
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        location = get_object_or_404(Location, id=location_id)
        photo_id = request.POST.get('photo_id')
        if not photo_id:
            response = HttpResponse(status=400)
            toast_message = {
                "toastMessage": {
                    "value": "Brak ID zdjęcia",
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        photo = get_object_or_404(LocationImage, id=photo_id, location=location)
        
        photo.is_primary = True
        photo.save()
        
        # Refresh photos list
        photos = location.images.all().order_by('created_at')
        upload_form = LocationImageForm(location=location, is_edit=False)
        context = {
            'location': location,
            'photos': photos,
            'upload_form': upload_form,
        }
        
        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_location_photos_modal.html', context)
        
        toast_message = {
            "toastMessage": {
                "value": "Zdjęcie zostało ustawione jako główne",
                "type": "success"
            },
            "location-list-updated": {
                "value": "location-list-updated"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas ustawiania zdjęcia głównego: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_location_photo_delete(request, location_id):
    """HTMX endpoint for deleting location photo"""
    print(request.method)

    if request.method != 'POST':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        location = get_object_or_404(Location, id=location_id)
        photo_id = request.POST.get('photo_id')
        if not photo_id:
            response = HttpResponse(status=400)
            toast_message = {
                "toastMessage": {
                    "value": "Brak ID zdjęcia",
                    "type": "danger"
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        photo = get_object_or_404(LocationImage, id=photo_id, location=location)
        
        photo.delete()
        
        # Refresh photos list
        photos = location.images.all().order_by('created_at')
        upload_form = LocationImageForm(location=location, is_edit=False)
        context = {
            'location': location,
            'photos': photos,
            'upload_form': upload_form,
        }
        
        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_location_photos_modal.html', context)
        
        toast_message = {
            "toastMessage": {
                "value": "Zdjęcie zostało usunięte",
                "type": "success"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas usuwania zdjęcia: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_location_photos_inline(request, location_id):
    """HTMX endpoint for displaying location photos inline in the next row"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        location = get_object_or_404(Location, id=location_id)
        photos = location.images.all().order_by('created_at')
        
        context = {
            'location': location,
            'photos': photos,
        }
        
        # Return HTML content directly for inline display
        return render(request, 'wms/partials/_location_photos_inline.html', context)
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas ładowania zdjęć: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_product_images_inline(request, product_id):
    """HTMX endpoint for displaying product images inline in the next row"""
    if request.method != 'GET':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        product = get_object_or_404(Product, id=product_id)
        images = product.images.all().order_by('created_at')
        
        context = {
            'product': product,
            'images': images,
        }
        
        # Return HTML content directly for inline display
        return render(request, 'wms/partials/_product_images_inline.html', context)
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas ładowania zdjęć: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_product_variants(request, product_id):
    """HTMX endpoint for displaying product variants inline in the next row"""

    if request.method != 'GET':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        product = get_object_or_404(Product, id=product_id)

        # Check if variant_ids parameter is provided
        variant_ids_param = request.GET.get('variant_ids')
        if variant_ids_param:
            # Parse comma-separated variant IDs
            try:
                variant_ids = [int(id.strip()) for id in variant_ids_param.split(',') if id.strip()]
                product_variants = Product.objects.filter(id__in=variant_ids)
            except ValueError:
                # Fallback to original behavior if parsing fails
                product_variants = Product.objects.filter(parent=product)
        else:
            # Original behavior - get variants by parent
            product_variants = Product.objects.filter(parent=product)

        context = {
            'product': product,
            'product_variants': product_variants,
            'silent': request.GET.get('silent'),
        }

        # Return HTML content directly for inline display
        return render(request, 'wms/partials/_product_variants_inline.html', context)
        
    except Exception as e:
        response = HttpResponse(status=500)
        toast_message = {
            "toastMessage": {
                "value": f"Błąd podczas ładowania wariantów: {str(e)}",
                "type": "danger"
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response


@login_required
def htmx_delete_variant(request, variant_id):
    """HTMX view for deleting product variants"""
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method not allowed
    
    try:
        # Current implementation stores size/color variants as child Product rows
        variant = get_object_or_404(Product, id=variant_id)
        if not variant.parent:
            response = HttpResponse(status=500)
            toast_message = {
                'toastMessage': {
                    'value': f'Błąd podczas usuwania wariantu: Brak produktu nadrzędnego',
                    'type': 'danger'
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response

        # Capture data before deletion
        parent_id = variant.parent.id
        # Delete the variant
        variant.delete()

        product = get_object_or_404(Product, id=parent_id)
        # Child Product variants for size/color
        product_variants = Product.objects.filter(parent=product).order_by('name')
        
        context = {
            'product': product,
            'product_variants': product_variants,
        }
        
        # Return the updated variants HTML with success toast
        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_product_variants_inline.html', context)
        toast_message = {
            'toastMessage': {
                'value': f'Usunięto wariant',
                'type': 'success'
            }
        }
        response['HX-Trigger'] = json.dumps(toast_message)
        return response
        
    except Exception as e:
        logger.error(f"Error deleting variant: {e}")
        toast_message = {
            'toastMessage': {
                'value': f'Błąd podczas usuwania wariantu: {str(e)}',
                'type': 'danger'
            }
        }
        
        response = HttpResponse(status=500)
        response['HX-Trigger'] = json.dumps(toast_message)
        return response

@login_required
def htmx_edit_product_modal(request, product_id):
    """HTMX view for editing product modal"""
    product = get_object_or_404(Product, id=product_id)
    context = {
        'product': product,
        'action': reverse('wms:htmx_edit_product_modal', kwargs={'product_id': product.id}),
        'mode': 'product',
        'form': ProductForm(instance=product),
        'stock_formset': ProductStockInlineFormSet(instance=product, prefix='stock')
    }
    response = HttpResponse(status=200)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        stock_formset = ProductStockInlineFormSet(request.POST, instance=product, prefix='stock')
        context['form'] = form
        context['stock_formset'] = stock_formset

        if form.is_valid() and stock_formset.is_valid():
            form.save()
            stock_formset.save()
            # Dispatch signal for product update
            product_updated.send(sender=None, product=product)
            # Rebuild fresh, unbound form and formset to avoid rendering deleted rows/errors
            context['form'] = ProductForm(instance=product)
            context['stock_formset'] = ProductStockInlineFormSet(instance=product, prefix='stock')
            response.content = render(request, 'wms/partials/_product_edit_modal_form.html', context)
            toast_message = {
                'toastMessage': {
                    'value': 'Produkt został zaktualizowany',
                    'type': 'success'
                },
                'product-list-updated': {
                    'value': 'product-list-updated'
                },
                'stock-list-updated': {
                    'value': 'stock-list-updated'
                },
                'modalMessage': {
                    'title': f"Edytuj produkt - {product.name}",
                    #'body': response.content.decode('utf-8')
                }
            }
            response['HX-Trigger'] = json.dumps(toast_message)
            return response
        else:
            response.content = render(request, 'wms/partials/_product_edit_modal_form.html', context)
            response['HX-Trigger'] = json.dumps({
                'modalMessage': {
                    'title': f"Edytuj produkt - {product.name}",
                    #'body': response.content.decode('utf-8')
                },
                'toastMessage': {
                    'value': 'Wystąpił błąd podczas zapisywania formularza',
                    'type': 'danger'
                }
            })
            return response

    response.content = render(request, 'wms/partials/_product_edit_modal_form.html', context)
    response['HX-Trigger'] = json.dumps({
        'modalMessage': {
            'title': f"Edytuj produkt - {product.name}",
            #'body': response.content.decode('utf-8')
        }
    })
    return response

@login_required
def htmx_add_size_color_modal(request, product_id, variant_id=None):
    """HTMX view for adding/editing size and color variant modal"""
    product = get_object_or_404(Product, id=product_id)
    variant = None
    if variant_id:
        variant = get_object_or_404(Product, id=variant_id)
        # Ensure the variant belongs to this product
        if not variant.parent or variant.parent.id != product.id:
            return HttpResponse(status=404)

    if request.method == 'GET':
        initial = None
        if variant:
            variants_json = variant.variants or {}
            initial = {
                'size': variants_json.get('size', ''),
                'color': variants_json.get('color', ''),
            }
        form = ProductColorSizeForm(parent=product, instance=variant, initial=initial)
        stock_formset = ProductStockInlineFormSet(instance=variant if variant else Product(), prefix='stock')

        context = {
            'form': form,
            'stock_formset': stock_formset,
            'product': product,
            'variant': variant,
            'action': reverse('wms:htmx_edit_size_color_modal', kwargs={'product_id': product.id, 'variant_id': variant.id}) if variant else reverse('wms:htmx_add_size_color_modal', kwargs={'product_id': product.id})
        }

        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_product_size_color_form.html', context)
        
        response['HX-Trigger'] = json.dumps({
            'modalMessage': {
                'title': (f"Edytuj rozmiar i kolor - {product.name}" if variant else f"Dodaj rozmiar i kolor - {product.name}"),
                #'body': response.content.decode('utf-8')
            }
        })
        
        return response
    
    # Handle POST for form submission
    if request.method == 'POST':
        form = ProductColorSizeForm(request.POST, parent=product, instance=variant)
        stock_formset = ProductStockInlineFormSet(request.POST, instance=variant if variant else Product(), prefix='stock')

        if form.is_valid() and stock_formset.is_valid():
            try:
                variant_obj = form.save()
                # Use the already validated formset and assign the saved variant as instance
                stock_formset.instance = variant_obj
                stock_formset.save()

                size_value = (variant_obj.variants or {}).get('size', '')
                color_value = (variant_obj.variants or {}).get('color', '')
                toast_message = {
                    'toastMessage': {
                        'value': (f"Zaktualizowano wariant: {size_value} - {color_value}" if variant else f"Dodano wariant: {size_value} - {color_value}"),
                        'type': 'success'
                    },
                    'product-variants-updated': {
                        'value': 'product-variants-updated'
                    },
                    'stock-list-updated': {
                        'value': 'stock-list-updated'                    
                    },
                    'modalHide': {
                        'value': 'modalHide'
                    }
                }

                response = HttpResponse(status=200)
                response['HX-Trigger'] = json.dumps(toast_message)
                return response

            except Exception as e:
                toast_message = {
                    'toastMessage': {
                        'value': f'Błąd podczas zapisywania: {str(e)}',
                        'type': 'danger'
                    }
                }
                response = HttpResponse(status=500)
                response['HX-Trigger'] = json.dumps(toast_message)
                return response

        # Form or formset has errors, return with errors
        context = {
            'form': form,
            'stock_formset': stock_formset,
            'product': product,
            'variant': variant,
            'action': reverse('wms:htmx_edit_size_color_modal', kwargs={'product_id': product.id, 'variant_id': variant.id}) if variant else reverse('wms:htmx_add_size_color_modal', kwargs={'product_id': product.id})
        }

        response = HttpResponse(status=200)
        response.content = render(request, 'wms/partials/_product_size_color_form.html', context)

        response['HX-Trigger'] = json.dumps({
            'modalMessage': {
                'title': (f"Edytuj rozmiar i kolor - {product.name}" if variant else f"Dodaj rozmiar i kolor - {product.name}"),
                #'body': response.content.decode('utf-8')
            },
            'toastMessage': {
                'value': 'Wystąpił błąd podczas zapisywania formularza',
                'type': 'danger'
            }
        })

        return response


@login_required
def htmx_product_groups_autocomplete(request):
    """HTMX endpoint for product groups autocomplete"""
    query = request.GET.get('group', '').strip()
    if not query:
        return HttpResponse('')

    # Search for product groups by name or code
    groups = ProductGroup.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query),
        is_active=True
    ).order_by('name')[:10]  # Limit to 10 results

    # Create HTML divs for the autocomplete dropdown
    options_html = ''
    for group in groups:
        options_html += f'<div class="autocomplete-item" data-group-id="{group.id}" data-group-name="{group.name}" data-group-code="{group.code}">{group.code} - {group.name}</div>'
    
    return HttpResponse(options_html)


@login_required
def htmx_locations_autocomplete(request):
    """HTMX endpoint for locations autocomplete"""
    query = request.GET.get('location', '').strip()
    picking_id = request.GET.get('picking_id', '').strip()
    receiving_id = request.GET.get('receiving_id', '').strip()
    
    
    if not query:
        return HttpResponse('')

    # Base query for active locations
    locations_query = Location.objects.filter(
        Q(name__icontains=query) | Q(barcode__icontains=query),
        is_active=True
    )
    
    # If picking_id is provided, filter locations that have items for this picking order
    if picking_id:
        try:
            picking_order = PickingOrder.objects.get(id=picking_id)
            # Get locations that have picking items for this order
            location_ids = PickingItem.objects.filter(
                picking_order=picking_order,
                quantity_picked__lt=F('quantity_to_pick')
            ).values_list('location_id', flat=True).distinct()
            
            if location_ids:
                locations_query = locations_query.filter(id__in=location_ids)
        except PickingOrder.DoesNotExist:
            pass
    
    # If receiving_id is provided, just show all active locations (receiving can go to any location)
    # No need to filter by receiving items as they can be received to any location
    
    locations = locations_query.order_by('name')[:10]  # Limit to 10 results

    # Create HTML divs for the autocomplete dropdown
    options_html = ''
    for location in locations:
        options_html += f'<div class="autocomplete-item" data-location-id="{location.id}" data-location-barcode="{location.barcode}" data-location-name="{location.name}">{location.name} ({location.barcode})</div>'
    
    return HttpResponse(options_html)








