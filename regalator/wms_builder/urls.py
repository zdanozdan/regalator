from django.urls import path
from . import views

app_name = 'wms_builder'

urlpatterns = [
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:warehouse_id>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<int:warehouse_id>/zones/<int:zone_id>/', views.warehouse_detail, name='warehouse_detail_zone'),
    path('warehouses/<int:warehouse_id>/zones/<int:zone_id>/racks/<int:rack_id>/', views.warehouse_detail, name='warehouse_detail_rack'),
    path('warehouses/<int:warehouse_id>/edit/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouses/<int:warehouse_id>/delete/', views.warehouse_delete, name='warehouse_delete'),
    
    # Zone HTMX endpoints
    path('warehouses/<int:warehouse_id>/zones/create/', views.htmx_zone_create, name='htmx_zone_create'),
    path('warehouses/<int:warehouse_id>/zones/quick-create/', views.htmx_zone_quick_create, name='htmx_zone_quick_create'),
    path('zones/<int:zone_id>/update-position/', views.htmx_zone_update_position, name='htmx_zone_update_position'),
    path('zones/<int:zone_id>/update-size/', views.htmx_zone_update_size, name='htmx_zone_update_size'),
    path('zones/<int:zone_id>/edit/', views.htmx_zone_edit, name='htmx_zone_edit'),
    path('zones/<int:zone_id>/delete/', views.htmx_zone_delete, name='htmx_zone_delete'),
    path('zones/<int:zone_id>/duplicate/', views.htmx_zone_duplicate, name='htmx_zone_duplicate'),
    path('zones/<int:zone_id>/sync-to-location/', views.htmx_zone_sync_to_location, name='htmx_zone_sync_to_location'),
    
    # Rack HTMX endpoints
    path('zones/<int:zone_id>/racks/create/', views.htmx_rack_create, name='htmx_rack_create'),
    path('zones/<int:zone_id>/racks/quick-create/', views.htmx_rack_quick_create, name='htmx_rack_quick_create'),
    path('racks/<int:rack_id>/update-position/', views.htmx_rack_update_position, name='htmx_rack_update_position'),
    path('racks/<int:rack_id>/update-size/', views.htmx_rack_update_size, name='htmx_rack_update_size'),
    path('racks/<int:rack_id>/edit/', views.htmx_rack_edit, name='htmx_rack_edit'),
    path('racks/<int:rack_id>/delete/', views.htmx_rack_delete, name='htmx_rack_delete'),
    path('racks/<int:rack_id>/duplicate/', views.htmx_rack_duplicate, name='htmx_rack_duplicate'),
    path('racks/<int:rack_id>/sync-to-location/', views.htmx_rack_sync_to_location, name='htmx_rack_sync_to_location'),
    
    # Shelf HTMX endpoints
    path('racks/<int:rack_id>/shelves/create/', views.htmx_shelf_create, name='htmx_shelf_create'),
    path('racks/<int:rack_id>/shelves/quick-create/', views.htmx_shelf_quick_create, name='htmx_shelf_quick_create'),
    path('shelves/<int:shelf_id>/update-position/', views.htmx_shelf_update_position, name='htmx_shelf_update_position'),
    path('shelves/<int:shelf_id>/update-size/', views.htmx_shelf_update_size, name='htmx_shelf_update_size'),
    path('shelves/<int:shelf_id>/edit/', views.htmx_shelf_edit, name='htmx_shelf_edit'),
    path('shelves/<int:shelf_id>/delete/', views.htmx_shelf_delete, name='htmx_shelf_delete'),
    path('shelves/<int:shelf_id>/duplicate/', views.htmx_shelf_duplicate, name='htmx_shelf_duplicate'),
    path('shelves/<int:shelf_id>/sync-to-location/', views.htmx_shelf_sync_to_location, name='htmx_shelf_sync_to_location'),
]

