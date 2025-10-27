from django.conf import settings
import os

# Crear directorio media al iniciar la aplicación (solo en producción)
if hasattr(settings, 'MEDIA_ROOT') and not os.path.exists(settings.MEDIA_ROOT):
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    print(f"✅ Directorio MEDIA_ROOT creado: {settings.MEDIA_ROOT}")