import os
from django.core.wsgi import get_wsgi_application

# Ajusta la ruta del settings a tu proyecto real
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budsi_django.settings')

application = get_wsgi_application()
