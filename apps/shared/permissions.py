"""
Permission classes de DRF basadas en rol.

La verificación de PROPIEDAD (que este negocio/repartidor sea dueño de
ESTE pedido) se hace en los servicios; aquí solo se filtra por rol, que es
la primera barrera. Un superusuario pasa todos los filtros.
"""
from rest_framework.permissions import BasePermission


class _RolPermission(BasePermission):
    rol = None

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and (u.is_superuser or u.rol == self.rol)
        )


class IsCliente(_RolPermission):
    rol = "CLIENTE"


class IsNegocio(_RolPermission):
    rol = "NEGOCIO"


class IsRepartidor(_RolPermission):
    rol = "REPARTIDOR"


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "es_admin", False))