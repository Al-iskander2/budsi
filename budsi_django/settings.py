import os
from pathlib import Path
from dotenv import load_dotenv

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables del .env
load_dotenv(BASE_DIR / ".env")

# VERIFICACIÓN TEMPORAL - eliminar después de probar
print("=== VARIABLES DE ENTORNO ===")
print("STRIPE_SECRET_KEY:", "CARGADA" if os.getenv("STRIPE_SECRET_KEY") else "NO CARGADA")
print("POSTGRES_DB:", os.getenv("POSTGRES_DB"))
print("POSTGRES_USER:", os.getenv("POSTGRES_USER"))
print("POSTGRES_PASSWORD:", "CARGADA" if os.getenv("POSTGRES_PASSWORD") else "NO CARGADA")
print("POSTGRES_HOST:", os.getenv("POSTGRES_HOST"))
print("POSTGRES_PORT:", os.getenv("POSTGRES_PORT"))
print("============================")

# SECURITY - CAMBIOS IMPORTANTES
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "your-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"  # True por defecto para desarrollo

# ALLOWED_HOSTS para desarrollo

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# Solo añadir Render en producción
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and not DEBUG:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.humanize',

    # Apps del proyecto
    "budsi_database",
    "budsi_django",
]

# MIDDLEWARE - SOLO whitenoise en producción
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise solo en producción
    "whitenoise.middleware.WhiteNoiseMiddleware" if not DEBUG else "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Limpiar middleware None (si DEBUG=True, whitenoise se convierte en None)
MIDDLEWARE = [mw for mw in MIDDLEWARE if mw is not None]

ROOT_URLCONF = "budsi_django.urls"

# TEMPLATES - CON MEDIA CONTEXT PROCESSOR
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",  # Añadir este también
            ],
        },
    },
]

WSGI_APPLICATION = "budsi_django.wsgi.application"

# VARIABLES API / Secrets
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

# DATABASE
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "budsi"),
        "USER": os.getenv("POSTGRES_USER", "email"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "9"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# AUTH
AUTH_USER_MODEL = "budsi_database.User"
AUTHENTICATION_BACKENDS = [
    "budsi_django.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# INTERNACIONALIZACIÓN
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Dublin"
USE_I18N = True
USE_TZ = True

# STATIC & MEDIA - CONFIGURACIÓN MEJORADA
STATIC_URL = "/static/"

# En desarrollo: usar STATICFILES_DIRS directamente
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# En producción: STATIC_ROOT para collectstatic
STATIC_ROOT = BASE_DIR / "staticfiles"

# Configuración de WhiteNoise SOLO en producción
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
else:
    # En desarrollo, servir estáticos directamente desde STATICFILES_DIRS
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Configuración de autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración adicional para desarrollo
if DEBUG:
    # En desarrollo, mostrar logs de static files
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    }