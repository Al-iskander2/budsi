# logic/debugger.py
import os
import logging
from django.conf import settings
from django.urls import resolve, Resolver404
from django.db import connection, OperationalError

# Logger nombrado por módulo
logger = logging.getLogger(__name__)

# Controla si los debug están activos
DEBUG_MODE = getattr(settings, "DEBUG", False)

def debug(message, level='info'):
    """
    Registro de mensajes de depuración en consola y logger, según nivel.
    """
    if not DEBUG_MODE:
        return

    prefix = "🛠️ DEBUG"
    text = f"{prefix} | {message}"

    # Siempre imprime en consola para desarrollo rápido
    print(text)

    # Registra en logger según nivel
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    else:
        logger.debug(message)

# Validación de plantilla
def check_template_exists(template_relative_path):
    path = os.path.join(settings.BASE_DIR, "templates", template_relative_path)
    if os.path.exists(path):
        debug(f"Template encontrado: {template_relative_path}")
    else:
        debug(f"Template no encontrado: {template_relative_path}", level='warning')

# Resolución de URL
def check_url_resolves(url_path):
    try:
        match = resolve(url_path)
        debug(f"URL resuelta: {url_path} → view '{match.view_name}'")
    except Resolver404:
        debug(f"URL no resuelta: {url_path}", level='warning')

# Comprobar conexión a base de datos
def check_db_connection():
    try:
        connection.ensure_connection()
        debug("Conexión a base de datos OK")
    except OperationalError as e:
        debug(f"Fallo en la base de datos: {e}", level='error')

# Verificar que existe una tabla
def check_table_exists(table_name):
    tables = connection.introspection.table_names()
    if table_name in tables:
        debug(f"Tabla encontrada: {table_name}")
    else:
        debug(f"Tabla no existe: {table_name}", level='warning')

# Verificar que existe un archivo estático
def check_static_file(relative_path):
    static_path = os.path.join(settings.BASE_DIR, "static", relative_path)
    if os.path.exists(static_path):
        debug(f"Static file existe: {relative_path}")
    else:
        debug(f"Static file faltante: {relative_path}", level='warning')

# Verificar variables de entorno
def check_env_var(var_name):
    val = os.getenv(var_name)
    if val is not None:
        debug(f"ENV '{var_name}' = '{val}'")
    else:
        debug(f"ENV variable '{var_name}' no está definida", level='warning')

# Validar plan en parámetros
def check_plan_parameters(plan, allowed_plans):
    if plan in allowed_plans:
        debug(f"Plan válido recibido: '{plan}'")
    else:
        debug(f"Plan inválido: '{plan}'", level='warning')

# Validar campos del formulario de pago
def validate_payment_form_data(data):
    required_fields = ['name', 'email', 'card_number', 'exp_month', 'cvc']
    for field in required_fields:
        value = data.get(field, '').strip()
        if not value:
            debug(f"Campo faltante o vacío: '{field}'", level='error')
        else:
            debug(f"Campo OK: {field}")

# Simulación de validación de tarjeta
def simulate_card_validation(card_number):
    clean = card_number.replace(" ", "")
    if len(clean) >= 13 and clean.isdigit():
        debug(f"Número de tarjeta parece válido ({len(clean)} dígitos)")
    else:
        debug(f"Número de tarjeta inválido: '{card_number}'", level='error')

# Verificar método HTTP
def check_request_method(request, expected_method='POST'):
    if request.method != expected_method:
        debug(f"Método HTTP inesperado: {request.method}. Se esperaba {expected_method}", level='error')
    else:
        debug(f"Método HTTP correcto: {request.method}")
