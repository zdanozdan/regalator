from django.contrib import admin
from .models import Asset, Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    list_filter = ['parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'name': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    prepopulated_fields = {'name': ('name',)}


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'file_type', 'category', 'uploaded_by', 'uploaded_at', 'is_public']
    list_filter = ['file_type', 'category', 'uploaded_at', 'is_public', 'tags']
    search_fields = ['title', 'description', 'filename', 'slug']
    readonly_fields = ['uploaded_at', 'updated_at', 'file_size', 'file_extension']
    filter_horizontal = ['tags']
    date_hierarchy = 'uploaded_at'
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('title', 'slug', 'description', 'file', 'file_type')
        }),
        ('Kategoryzacja', {
            'fields': ('category', 'tags')
        }),
        ('Ustawienia', {
            'fields': ('uploaded_by', 'is_public')
        }),
        ('Informacje techniczne', {
            'fields': ('uploaded_at', 'updated_at', 'file_size', 'file_extension'),
            'classes': ('collapse',)
        }),
    )
