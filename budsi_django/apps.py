from django.apps import AppConfig
import os

class BudsiDjangoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "budsi_django"
    
    def ready(self):
        # ✅ Código seguro que SÍ puede leer settings
        from django.conf import settings
        # Crear MEDIA_ROOT si no existe
        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            print(f"✅ Directorio MEDIA_ROOT creado: {settings.MEDIA_ROOT}")
