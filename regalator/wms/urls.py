from django.urls import path
from . import views
from django.urls import include

app_name = 'wms'

urlpatterns = [
    # Dashboard główny
    path('', views.dashboard, name='dashboard'),
    
    # Dashboard kompletacji
    path('kompletacja/', views.kompletacja_dashboard, name='kompletacja_dashboard'),
    
    # Dashboard przyjęć
    path('przyjecia/', views.przyjecia_dashboard, name='przyjecia_dashboard'),
    
    # Zamówienia klientów
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/create-picking/', views.create_picking_order, name='create_picking_order'),
    
    # Zlecenia kompletacji (RegOut)
    path('picking/', views.picking_list, name='picking_list'),
    path('picking/<int:picking_id>/', views.picking_detail, name='picking_detail'),
    path('picking/<int:picking_id>/start/', views.start_picking, name='start_picking'),
    path('picking/<int:picking_id>/scan-location/', views.scan_location, name='scan_location'),
    path('picking/<int:picking_id>/scan-product/', views.scan_product, name='scan_product'),
    path('picking/<int:picking_id>/enter-quantity/<int:item_id>/', views.enter_quantity, name='enter_quantity'),
    path('picking/<int:picking_id>/complete/', views.complete_picking, name='complete_picking'),
    
    # Zamówienia do dostawców (ZD)
    path('supplier-orders/', views.supplier_order_list, name='supplier_order_list'),
    path('supplier-orders/<int:order_id>/', views.supplier_order_detail, name='supplier_order_detail'),
    path('supplier-orders/<int:supplier_order_id>/create-receiving/', views.create_receiving_order, name='create_receiving_order'),
    
    # Rejestry przyjęć (RegIn)
    path('receiving/', views.receiving_order_list, name='receiving_order_list'),
    path('receiving/<int:receiving_id>/', views.receiving_order_detail, name='receiving_order_detail'),
    path('receiving/<int:receiving_id>/scan-location/', views.scan_receiving_location, name='scan_receiving_location'),
    path('receiving/<int:receiving_id>/scan-product/', views.scan_receiving_product, name='scan_receiving_product'),
    path('receiving/<int:receiving_id>/enter-quantity/<int:item_id>/', views.enter_receiving_quantity, name='enter_receiving_quantity'),
    path('receiving/<int:receiving_id>/complete/', views.complete_receiving, name='complete_receiving'),
    
    # Katalogi
    path('products/', views.product_list, name='product_list'),
    path('product-groups/', views.product_group_list, name='product_group_list'),
    path('product-groups/<int:group_id>/', views.product_group_detail, name='product_group_detail'),
    path('locations/', views.location_list, name='location_list'),
    path('stock/', views.stock_list, name='stock_list'),
    
    # Autentykacja
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API
    path('api/scan-barcode/', views.api_scan_barcode, name='api_scan_barcode'),
    path('api/product-details/<int:product_id>/', views.api_product_details, name='api_product_details'),
    path('htmx/sync-product/<int:product_id>/', views.htmx_sync_product, name='htmx_sync_product'),
    
    # Profile
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Assets
    path('assets/', include('assets.urls')),
] 