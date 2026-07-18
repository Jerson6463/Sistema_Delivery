"""
Control de acceso por rol para vistas WEB (no DRF).

- rol_requerido(): decorador para vistas basadas en función (FBV).
- RolRequeridoMixin: mixin para vistas basadas en clase (CBV).

Regla de oro: la seguridad se valida SIEMPRE en el backend. Ocultar un
botón en el template no protege nada.

(Las permission classes de DRF para la API se agregarán en la Fase 11.)
"""
from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    """
    Uso:
        @rol_requerido("CLIENTE")
        def crear_pedido(request): ...
    Un superusuario siempre pasa.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                raise PermissionDenied("Debes iniciar sesión.")
            if not (user.is_superuser or user.rol in roles):
                raise PermissionDenied("No tienes permiso para esta acción.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Uso:
        class PanelNegocio(RolRequeridoMixin, TemplateView):
            roles_permitidos = ("NEGOCIO",)
    """
    roles_permitidos: tuple = ()

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.rol in self.roles_permitidos