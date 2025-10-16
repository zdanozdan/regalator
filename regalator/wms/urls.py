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
    
    # Zlecenia kompletacji (Terminacja)
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
    path('htmx/sync-zd-orders/', views.htmx_sync_zd_orders, name='sync_zd_orders'),
    path('htmx/delete-supplier-order/<int:order_id>/', views.htmx_delete_supplier_order, name='htmx_delete_supplier_order'),
    
    # Rejestry przyjęć (Regalacja)
    path('receiving/', views.receiving_order_list, name='receiving_order_list'),
    path('receiving/<int:receiving_id>/', views.receiving_order_detail, name='receiving_order_detail'),
    path('receiving/<int:receiving_id>/scan-location/', views.scan_receiving_location, name='scan_receiving_location'),
    path('receiving/<int:receiving_id>/scan-product/', views.scan_receiving_product, name='scan_receiving_product'),
    path('receiving/<int:receiving_id>/enter-quantity/<int:item_id>/', views.enter_receiving_quantity, name='enter_receiving_quantity'),
    path('receiving/<int:receiving_id>/complete/', views.complete_receiving, name='complete_receiving'),
    
    # Katalogi
    path('products/', views.product_list, name='product_list'),
    #path('products/<int:product_id>/edit-codes/', views.edit_product_codes, name='edit_product_codes'),
    path('products/<int:product_id>/api/add-scanned-code/', views.api_add_scanned_code, name='api_add_scanned_code'),
    path('product-groups/', views.product_group_list, name='product_group_list'),
    path('product-groups/<int:group_id>/', views.product_group_detail, name='product_group_detail'),
    path('barcodes/', views.barcodes_list, name='barcodes_list'),
    path('locations/', views.location_list, name='location_list'),
    path('htmx/location/create/', views.htmx_location_edit, name='htmx_location_create'),
    path('htmx/location/<int:location_id>/edit/', views.htmx_location_edit, name='htmx_location_edit'),
    path('htmx/location/<int:location_id>/delete/', views.htmx_location_delete, name='htmx_location_delete'),
    path('htmx/location/<int:location_id>/photos/', views.htmx_location_photos, name='htmx_location_photos'),
    path('htmx/location/<int:location_id>/photos-inline/', views.htmx_location_photos_inline, name='htmx_location_photos_inline'),
    path('htmx/location/<int:location_id>/photo/upload/', views.htmx_location_photo_upload, name='htmx_location_photo_upload'),
    path('htmx/location/<int:location_id>/photo/update/', views.htmx_location_photo_update, name='htmx_location_photo_update'),
    path('htmx/location/<int:location_id>/photo/set-primary/', views.htmx_location_photo_set_primary, name='htmx_location_photo_set_primary'),
    path('htmx/location/<int:location_id>/photo/delete/', views.htmx_location_photo_delete, name='htmx_location_photo_delete'),
    path('stock/', views.stock_list, name='stock_list'),
    

    # Autentykacja
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
        # API
    path('api/scan-barcode/', views.api_scan_barcode, name='api_scan_barcode'),
    path('htmx/sync-product/<int:product_id>/', views.htmx_sync_product, name='htmx_sync_product'),
    path('htmx/product-details/<int:product_id>/', views.htmx_product_details, name='htmx_product_details'),
    path('htmx/delete-code/<int:product_id>/<int:code_id>/', views.htmx_delete_code, name='htmx_delete_code'),
    path('htmx/product/<int:product_id>/add-code-modal/', views.htmx_add_code_modal, name='htmx_add_code_modal'),
    path('htmx/product/<int:product_id>/codes-list/', views.htmx_product_codes_list, name='htmx_product_codes_list'),
    path('htmx/product/<int:product_id>/add-code-inline/', views.htmx_add_code_inline, name='htmx_add_code_inline'),
    path('htmx/product/<int:product_id>/images-inline/', views.htmx_product_images_inline, name='htmx_product_images_inline'),
    path('htmx/product/<int:product_id>/variants/', views.htmx_product_variants, name='htmx_product_variants'),
    path('htmx/product/<int:product_id>/row/', views.htmx_product_row, name='htmx_product_row'),
    path('htmx/stock/<int:product_id>/row/', views.htmx_stock_row, name='htmx_stock_row'),
    path('htmx/product/<int:product_id>/add-size-color/', views.htmx_add_size_color_modal, name='htmx_add_size_color_modal'),
    path('htmx/product/<int:product_id>/edit-size-color/<int:variant_id>/', views.htmx_add_size_color_modal, name='htmx_edit_size_color_modal'),
    path('htmx/product/<int:product_id>/edit-product-modal/', views.htmx_edit_product_modal, name='htmx_edit_product_modal'),
    path('htmx/variant/<int:variant_id>/delete/', views.htmx_delete_variant, name='htmx_delete_variant'),
    path('htmx/product/<int:product_id>/edit-codes/', views.htmx_edit_product_codes, name='htmx_edit_product_codes'),
    path('htmx/product/<int:product_id>/edit-codes/<int:code_id>/', views.htmx_edit_product_codes, name='htmx_edit_product_codes'),
    path('htmx/product-groups-autocomplete/', views.htmx_product_groups_autocomplete, name='htmx_product_groups_autocomplete'),
    path('htmx/locations-autocomplete/', views.htmx_locations_autocomplete, name='htmx_locations_autocomplete'),

    
    # Profile
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # Assets
    path('assets/', include('assets.urls')),
] 