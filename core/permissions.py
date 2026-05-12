from rest_framework.permissions import BasePermission
from core.choices import Roles

class EsCliente(BasePermission):
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.rol == Roles.CLIENTE
        )

class EsAdministradorNegocio(BasePermission):
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.rol == Roles.ADMIN
        )

class EsRepartidor(BasePermission):
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.rol == Roles.REPARTIDOR
        )

class EsDueñoDelNegocio(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        # Si el objeto es un Negocio, verificamos el propietario
        if hasattr(obj, 'propietario'):
            return obj.propietario == request.user
        # Si el objeto es un Producto, verificamos el dueño del negocio al que pertenece
        elif hasattr(obj, 'negocio'):
            return obj.negocio.propietario == request.user
        return False