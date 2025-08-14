# logic/access_control.py o budgidesk_app/utils.py

from functools import wraps
from django.shortcuts import redirect

PLAN_TIERS = {
    'lite': 0,
    'smart': 1,
    'elite': 2,
    'admin': 3,
}

def require_plan(required_plan):
    """
    Decorador para proteger vistas según el plan del usuario.
    Ej: @require_plan("smart") permite acceso a smart, elite, admin.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_plan = getattr(request.user, 'plan', 'lite')
            user_level = PLAN_TIERS.get(user_plan, 0)
            required_level = PLAN_TIERS.get(required_plan, 1)

            if user_level < required_level:
                return redirect('pricing')  # Redirige a la pantalla de upgrade

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
