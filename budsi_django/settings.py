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

# SECURITY
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "your-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Apps del proyecto
    "budsi_database",
    "budsi_django",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "budsi_django.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "budsi_django.wsgi.application"
ASGI_APPLICATION = "budsi_django.asgi.application"

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

# STATIC & MEDIA
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Configuración de autenticación
LOGIN_URL = 'login'  # Nombre de la URL de login
LOGIN_REDIRECT_URL = 'dashboard'  # A dónde redirigir después del login
LOGOUT_REDIRECT_URL = 'login'  # A dónde redirigir después del logout

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"