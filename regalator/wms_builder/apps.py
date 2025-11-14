from django.apps import AppConfig


class WmsBuilderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wms_builder'
    verbose_name = 'WMS Builder'
    
    def ready(self):
        import wms_builder.signals

