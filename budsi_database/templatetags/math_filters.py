from django import template  # ← AÑADE ESTA LÍNEA

register = template.Library()

@register.filter
def div(value, arg):
    """Divide el valor por el argumento"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0