import os
from pathlib import Path
from dotenv import load_dotenv

# BASE DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables del .env SOLO en desarrollo
load_dotenv(BASE_DIR / ".env")

# VERIFICACIÓN TEMPORAL (solo en desarrollo)
if os.getenv("DJANGO_DEBUG") == "True":
    print("=== VARIABLES DE ENTORNO ===")
    print("DJANGO_SECRET_KEY:", "CARGADA" if os.getenv("DJANGO_SECRET_KEY") else "NO CARGADA")
    print("DJANGO_DEBUG:", os.getenv("DJANGO_DEBUG", "No configurado"))
    print("POSTGRES_DB:", os.getenv("POSTGRES_DB"))
    print("RENDER:", "SÍ" if os.getenv('RENDER') else "NO")
    print("============================")

# SECURITY - MANEJO SEGURO DE SECRET_KEY
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# SECRET_KEY con fallbacks diferentes para desarrollo/producción
if DEBUG:
    # En desarrollo: clave simple (puede estar en .env o no)
    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "clave-simple-para-desarrollo-solo")
else:
    # En producción: EXIGIR clave segura
    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("DJANGO_SECRET_KEY debe estar configurada en producción")

# ALLOWED_HOSTS
ALLOWED_HOSTS = [
    'localhost', '127.0.0.1', '0.0.0.0', 'testserver',
    'budsidesk.com', 'www.budsidesk.com', 
    'budsi.onrender.com', '.onrender.com',
]

# Render external hostname
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# CSRF TRUSTED ORIGINS
CSRF_TRUSTED_ORIGINS = [
    'https://budsidesk.com',
    'https://www.budsidesk.com', 
    'https://budsi.onrender.com',
    'https://*.onrender.com',
]

# SSL para producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

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

# MIDDLEWARE - WHITENOISE SIEMPRE PRESENTE
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
                "django.template.context_processors.static",
            ],
        },
    },
]

WSGI_APPLICATION = "budsi_django.wsgi.application"

# VARIABLES API / Secrets
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

# DATABASE - Configuración mejorada para Render
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "budsi"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        # Configuraciones adicionales para mejor rendimiento
        "CONN_MAX_AGE": 600,  # 10 minutos de conexión persistente
        "OPTIONS": {
            "connect_timeout": 10,
        }
    }
}

# AUTH
AUTH_USER_MODEL = "budsi_database.User"
AUTHENTICATION_BACKENDS = [
    "budsi_django.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# INTERNACIONALIZACIÓN
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Dublin"
USE_I18N = True
USE_TZ = True

# STATIC & MEDIA - CONFIGURACIÓN MEJORADA PARA PRODUCCIÓN
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration - OPTIMIZADO
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MAX_AGE = 31536000  # 1 year for cache

MEDIA_URL = "/media/"
# En Render, usar disco persistente si está configurado
MEDIA_ROOT = os.getenv("MEDIA_ROOT", BASE_DIR / "media")

# Límites para upload de archivos
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
MAX_UPLOAD_SIZE = 10  # MB

# Configuración de autenticación
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración de logging MEJORADA
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' if DEBUG else 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'budsi_django': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'logic': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Configuración de sesiones (mejor seguridad)
SESSION_COOKIE_AGE = 1209600  # 2 semanas en segundos
SESSION_SAVE_EVERY_REQUEST = True

# Configuración de correo (para futuras notificaciones)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'

# Configuración de cache (simple para empezar)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuración adicional para seguridad
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# Timeout para requests largos (especialmente para OCR)
REQUEST_TIMEOUT = 30  # segundos