from django.contrib import admin
from .models import Warehouse, WarehouseZone, WarehouseRack, WarehouseShelf


class WarehouseShelfInline(admin.TabularInline):
    model = WarehouseShelf
    extra = 0
    fields = ('name', 'x', 'y', 'color')


class WarehouseRackInline(admin.TabularInline):
    model = WarehouseRack
    extra = 0
    fields = ('name', 'x', 'y', 'color')
    inlines = [WarehouseShelfInline]


class WarehouseZoneInline(admin.TabularInline):
    model = WarehouseZone
    extra = 0
    fields = ('name', 'x', 'y', 'color')
    inlines = [WarehouseRackInline]


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'width', 'height', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    inlines = [WarehouseZoneInline]


@admin.register(WarehouseZone)
class WarehouseZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'warehouse', 'x', 'y', 'created_at']
    list_filter = ['warehouse', 'created_at']
    search_fields = ['name', 'warehouse__name']


@admin.register(WarehouseRack)
class WarehouseRackAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone', 'x', 'y', 'created_at']
    list_filter = ['zone__warehouse', 'created_at']
    search_fields = ['name', 'zone__name']


@admin.register(WarehouseShelf)
class WarehouseShelfAdmin(admin.ModelAdmin):
    list_display = ['name', 'rack', 'x', 'y', 'created_at']
    list_filter = ['rack__zone__warehouse', 'created_at']
    search_fields = ['name', 'rack__name']

