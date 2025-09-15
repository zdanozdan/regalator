from django.contrib import admin
from .models import (
    Product, Location, Stock, CustomerOrder, OrderItem,
    PickingOrder, PickingItem, PickingHistory,
    SupplierOrder, SupplierOrderItem, ReceivingOrder, 
    ReceivingItem, ReceivingHistory, WarehouseDocument, DocumentItem, UserProfile, ProductGroup, ProductCode, ProductImage
)


class ProductCodeInline(admin.TabularInline):
    model = ProductCode
    extra = 1
    fields = ['code', 'code_type', 'is_active', 'description']
    ordering = ['code_type', 'code']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'description', 'is_primary', 'order']
    ordering = ['is_primary', 'order', 'created_at']


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
    list_display = ['product', 'code', 'code_type', 'is_active', 'description']
    list_filter = ['code_type', 'is_active', 'created_at']
    search_fields = ['code', 'product__name', 'product__code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['product__name', 'code_type', 'code']
    autocomplete_fields = ['product']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('product', 'code', 'code_type', 'description')
        }),
        ('Ustawienia', {
            'fields': ('is_active',)
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['subiekt_id', 'code', 'name', 'display_groups', 'total_stock', 'subiekt_stock', 'stock_difference', 'needs_sync', 'unit']
    list_filter = ['unit', 'groups', 'last_sync_date']
    search_fields = ['code', 'name', 'codes__code', 'subiekt_id']
    readonly_fields = ['created_at', 'updated_at', 'total_stock', 'stock_difference', 'needs_sync']
    filter_horizontal = ['groups']
    inlines = [ProductCodeInline, ProductImageInline]
    actions = ['update_variants_to_size_and_color']
    
    def display_groups(self, obj):
        """Wyświetla grupy produktu"""
        return ', '.join([group.name for group in obj.groups.all()])
    display_groups.short_description = 'Grupy'
    
    
    def update_variants_to_size_and_color(self, request, queryset):
        """Admin action to update variants JSON field to include SizeAndColor type for products without parents"""
        # Filter only products without parents
        products_without_parents = queryset.filter(parent__isnull=True)
        
        updated_count = 0
        for product in products_without_parents:
            # Get current variants or initialize with default
            variants = product.variants or {'size': '', 'color': ''}
            
            # Add the type field
            variants['type'] = 'SizeAndColor'
            
            # Update the product
            product.variants = variants
            product.save(update_fields=['variants'])
            updated_count += 1
        
        if updated_count > 0:
            self.message_user(
                request,
                f'Successfully updated variants for {updated_count} product(s) without parents to include SizeAndColor type.',
                level='SUCCESS'
            )
        else:
            self.message_user(
                request,
                'No products without parents were selected. Only products without parent products can be updated.',
                level='WARNING'
            )
    
    update_variants_to_size_and_color.short_description = "Dodaj kolor i rozmiar"
    
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
    list_display = ['name', 'location_type', 'barcode', 'is_active']
    list_filter = ['location_type', 'is_active', 'created_at']
    search_fields = ['name', 'barcode', 'description']
    ordering = ['barcode']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'quantity', 'reserved_quantity', 'updated_at']
    list_filter = ['location', 'updated_at']
    search_fields = ['product__name', 'product__code', 'location__name', 'location__barcode']
    ordering = ['location__barcode', 'product__name']


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


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'description', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at', 'product__groups']
    search_fields = ['product__name', 'product__code', 'description']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    ordering = ['product__name', 'is_primary', 'order', 'created_at']
    autocomplete_fields = ['product']
    
    def image_preview(self, obj):
        """Wyświetla podgląd zdjęcia"""
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 100px; max-height: 100px;" />'
        return "Brak zdjęcia"
    image_preview.short_description = 'Podgląd'
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('product', 'image', 'description')
        }),
        ('Ustawienia', {
            'fields': ('is_primary', 'order')
        }),
        ('Podgląd', {
            'fields': ('image_preview',),
            'classes': ('collapse',)
        }),
        ('Informacje systemowe', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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
