from django.contrib import admin
from django.db.models import Q
from .models import tw_Towar, tw_Cena, tw_Stan


@admin.register(tw_Towar)
class TowarAdmin(admin.ModelAdmin):
    """Admin dla modelu Towar z Subiekt"""
    
    list_display = ['tw_Id', 'tw_Symbol', 'tw_Nazwa', 'get_stock_level', 'tw_Opis']
    list_filter = []
    search_fields = ['tw_Symbol', 'tw_Nazwa', 'tw_Opis']
    readonly_fields = ['tw_Id', 'tw_Symbol', 'tw_Nazwa', 'tw_Opis', 'get_stock_level']  # Wszystkie pola tylko do odczytu
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('tw_Id', 'tw_Symbol', 'tw_Nazwa', 'tw_Opis')
        }),
        ('Stan magazynowy', {
            'fields': ('get_stock_level',),
            'classes': ('collapse',)
        }),
    )
    
    def get_stock_level(self, obj):
        """Pobiera stan magazynowy dla magazynu ID=2"""
        try:
            stan = tw_Stan.objects.using('subiekt').filter(
                st_TowId=obj.tw_Id,
                st_MagId=2
            ).first()
            if stan:
                return f"{stan.st_Stan} szt."
            else:
                return "Brak danych"
        except Exception:
            return "Błąd pobierania"
    get_stock_level.short_description = 'Stan magazynowy (Mag=2)'
    get_stock_level.admin_order_field = 'tw_Id'  # Nie można sortować po polu obliczanym
    
    def get_queryset(self, request):
        """Dodaje prefetch_related dla lepszej wydajności"""
        return super().get_queryset(request).using('subiekt')
    
    def has_add_permission(self, request):
        """Wyłącz dodawanie - dane pochodzą z Subiekt"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Wyłącz edycję - dane pochodzą z Subiekt"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Wyłącz usuwanie - dane pochodzą z Subiekt"""
        return False


@admin.register(tw_Cena)
class CenaAdmin(admin.ModelAdmin):
    """Admin dla modelu Cena z Subiekt"""
    
    list_display = ['tc_Id', 'tc_IdTowar', 'tc_Id']
    list_filter = []
    search_fields = ['tc_IdTowar__tw_Symbol', 'tc_IdTowar__tw_Nazwa']
    readonly_fields = ['tc_Id', 'tc_IdTowar']
    
    fieldsets = (
        ('Informacje o cenie', {
            'fields': ('tc_Id', 'tc_IdTowar')
        }),
    )
    
    def has_add_permission(self, request):
        """Wyłącz dodawanie - dane pochodzą z Subiekt"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Wyłącz edycję - dane pochodzą z Subiekt"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Wyłącz usuwanie - dane pochodzą z Subiekt"""
        return False


@admin.register(tw_Stan)
class StanAdmin(admin.ModelAdmin):
    """Admin dla modelu Stan z Subiekt"""
    
    list_display = ['st_TowId', 'st_MagId', 'st_Stan', 'st_StanMin', 'st_StanMax']
    list_filter = ['st_MagId']
    search_fields = ['st_TowId__tw_Symbol', 'st_TowId__tw_Nazwa']
    readonly_fields = ['st_TowId', 'st_MagId', 'st_Stan', 'st_StanMin', 'st_StanRez', 'st_StanMax']
    
    fieldsets = (
        ('Informacje o stanie magazynowym', {
            'fields': ('st_TowId', 'st_MagId', 'st_Stan', 'st_StanMin', 'st_StanRez', 'st_StanMax')
        }),
    )
    
    def has_add_permission(self, request):
        """Wyłącz dodawanie - dane pochodzą z Subiekt"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Wyłącz edycję - dane pochodzą z Subiekt"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Wyłącz usuwanie - dane pochodzą z Subiekt"""
        return False
