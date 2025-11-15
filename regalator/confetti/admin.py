from django.contrib import admin

from .models import ConfettiGlobalSetting, ConfettiUserSetting


@admin.register(ConfettiGlobalSetting)
class ConfettiGlobalSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value_type", "updated_at")
    search_fields = ("key", "description")
    ordering = ("key",)
    list_filter = ("value_type",)


@admin.register(ConfettiUserSetting)
class ConfettiUserSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "user", "updated_at")
    search_fields = ("key", "user__username", "user__email")
    list_filter = ("key",)
    raw_id_fields = ("user",)
