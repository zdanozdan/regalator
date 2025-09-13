from django.contrib import admin
from .models import (
    Product, Location, Stock, CustomerOrder, OrderItem,
    PickingOrder, PickingItem, PickingHistory,
    SupplierOrder, SupplierOrderItem, ReceivingOrder, 
    ReceivingItem, ReceivingHistory, WarehouseDocument, DocumentItem, UserProfile, ProductGroup, ProductCode
)


class ProductCodeInline(admin.TabularInline):
    model = ProductCode
    extra = 1
    fields = ['code', 'code_type', 'is_primary', 'is_active', 'description']
    ordering = ['-is_primary', 'code_type', 'code']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'display_name', 'department', 'position', 'phone']
    list_filter = ['department', 'position']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'department', 'position']
    readonly_fields = ['created_at', 'updated_at']
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'Nazwa wyświetlana'


@admin.register(ProductCode)
class ProductCodeAdmin(admin.ModelAdmin):
    list_display = ['product', 'code', 'code_type', 'is_primary', 'is_active', 'description']
    list_filter = ['code_type', 'is_primary', 'is_active', 'created_at']
    search_fields = ['code', 'product__name', 'product__code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['product__name', 'code_type', 'code']
    autocomplete_fields = ['product']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('product', 'code', 'code_type', 'description')
        }),
        ('Ustawienia', {
            'fields': ('is_primary', 'is_active')
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['subiekt_id', 'code', 'name', 'display_groups', 'primary_barcode_display', 'total_stock', 'subiekt_stock', 'stock_difference', 'needs_sync', 'unit']
    list_filter = ['unit', 'groups', 'last_sync_date']
    search_fields = ['code', 'name', 'codes__code', 'subiekt_id']
    readonly_fields = ['created_at', 'updated_at', 'total_stock', 'stock_difference', 'needs_sync']
    filter_horizontal = ['groups']
    inlines = [ProductCodeInline]
    
    def display_groups(self, obj):
        """Wyświetla grupy produktu"""
        return ', '.join([group.name for group in obj.groups.all()])
    display_groups.short_description = 'Grupy'
    
    def primary_barcode_display(self, obj):
        """Wyświetla główny kod kreskowy"""
        return obj.primary_barcode or '-'
    primary_barcode_display.short_description = 'Główny kod kreskowy'
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('code', 'name', 'description', 'unit', 'groups','variants')
        }),
        ('Synchronizacja z Subiektem', {
            'fields': ('subiekt_id', 'subiekt_stock', 'subiekt_stock_reserved', 'last_sync_date')
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at', 'total_stock', 'stock_difference', 'needs_sync'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'location_type', 'barcode', 'is_active']
    list_filter = ['location_type', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'barcode', 'description']
    ordering = ['code']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'quantity', 'reserved_quantity', 'updated_at']
    list_filter = ['location', 'updated_at']
    search_fields = ['product__name', 'product__code', 'location__name', 'location__code']
    ordering = ['location__code', 'product__name']


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'order_date', 'status', 'total_value']
    list_filter = ['status', 'order_date', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'total_price', 'completed_quantity']
    list_filter = ['order__status', 'product__unit']
    search_fields = ['order__order_number', 'product__name', 'product__code']
    ordering = ['order__created_at']


@admin.register(PickingOrder)
class PickingOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_order', 'assigned_to', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'started_at', 'completed_at']
    search_fields = ['order_number', 'customer_order__order_number', 'customer_order__customer_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(PickingItem)
class PickingItemAdmin(admin.ModelAdmin):
    list_display = ['picking_order', 'product', 'location', 'quantity_to_pick', 'quantity_picked', 'is_completed']
    list_filter = ['is_completed', 'sequence', 'picking_order__status']
    search_fields = ['picking_order__order_number', 'product__name', 'location__name']
    ordering = ['picking_order__created_at', 'sequence']


@admin.register(PickingHistory)
class PickingHistoryAdmin(admin.ModelAdmin):
    list_display = ['picking_item', 'user', 'location_scanned', 'product_scanned', 'quantity_picked', 'scanned_at']
    list_filter = ['scanned_at', 'user']
    search_fields = ['picking_item__picking_order__order_number', 'product_scanned__name', 'location_scanned__name']
    ordering = ['-scanned_at']
    readonly_fields = ['scanned_at']


@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier_name', 'order_date', 'expected_delivery_date', 'status', 'total_items', 'received_items']
    list_filter = ['status', 'order_date', 'expected_delivery_date']
    search_fields = ['order_number', 'supplier_name', 'supplier_code']
    date_hierarchy = 'order_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('order_number', 'supplier_name', 'supplier_code', 'status')
        }),
        ('Daty', {
            'fields': ('order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Dodatkowe', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )


@admin.register(SupplierOrderItem)
class SupplierOrderItemAdmin(admin.ModelAdmin):
    list_display = ['supplier_order', 'product', 'quantity_ordered', 'quantity_received']
    list_filter = ['supplier_order__status', 'product']
    search_fields = ['supplier_order__order_number', 'product__name', 'product__codes__code']


@admin.register(ReceivingOrder)
class ReceivingOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier_order', 'status', 'assigned_to', 'created_at', 'total_items', 'received_items']
    list_filter = ['status', 'created_at', 'assigned_to']
    search_fields = ['order_number', 'supplier_order__order_number', 'supplier_order__supplier_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('order_number', 'supplier_order', 'status', 'assigned_to')
        }),
        ('Daty', {
            'fields': ('started_at', 'completed_at', 'created_at')
        }),
        ('Dodatkowe', {
            'fields': ('notes',)
        }),
    )


@admin.register(ReceivingItem)
class ReceivingItemAdmin(admin.ModelAdmin):
    list_display = ['receiving_order', 'product', 'quantity_ordered', 'quantity_received', 'location', 'sequence']
    list_filter = ['receiving_order__status', 'product', 'location']
    search_fields = ['receiving_order__order_number', 'product__name', 'product__codes__code']
    ordering = ['receiving_order', 'sequence']


@admin.register(ReceivingHistory)
class ReceivingHistoryAdmin(admin.ModelAdmin):
    list_display = ['receiving_order', 'product', 'location', 'quantity_received', 'scanned_by', 'scanned_at']
    list_filter = ['scanned_at', 'product', 'location', 'scanned_by']
    search_fields = ['receiving_order__order_number', 'product__name', 'product__codes__code']
    date_hierarchy = 'scanned_at'
    readonly_fields = ['scanned_at']


@admin.register(WarehouseDocument)
class WarehouseDocumentAdmin(admin.ModelAdmin):
    list_display = ['document_number', 'document_type', 'document_date', 'status', 'supplier_order', 'customer_order']
    list_filter = ['document_type', 'status', 'document_date']
    search_fields = ['document_number', 'supplier_order__order_number', 'customer_order__order_number']
    date_hierarchy = 'document_date'
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('document_number', 'document_type', 'document_date', 'status')
        }),
        ('Powiązania', {
            'fields': ('supplier_order', 'customer_order')
        }),
        ('Dodatkowe', {
            'fields': ('notes', 'created_at')
        }),
    )


@admin.register(DocumentItem)
class DocumentItemAdmin(admin.ModelAdmin):
    list_display = ['document', 'product', 'location', 'quantity']
    list_filter = ['document__document_type', 'document__status', 'product', 'location']
    search_fields = ['document__document_number', 'product__name', 'product__codes__code']
    ordering = ['document', 'product']


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'products_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'products_count']
    ordering = ['name']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('name', 'code', 'description', 'color')
        }),
        ('Ustawienia', {
            'fields': ('is_active',)
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at', 'products_count'),
            'classes': ('collapse',)
        }),
    )
