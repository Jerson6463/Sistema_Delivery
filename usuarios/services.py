from django.db import transaction
from .models import Usuario, Cliente, Repartidor
from catalogo.models import Negocio
from core.choices import Roles

def registrar_nuevo_cliente(datos_usuario: dict, direccion: str, telefono: str) -> Usuario:
    """Servicio para registrar un usuario y su perfil de cliente de forma atómica."""
    with transaction.atomic():
        usuario = Usuario.objects.create_user(
            rol=Roles.CLIENTE,
            **datos_usuario
        )
        Cliente.objects.create(
            usuario=usuario,
            direccion_principal=direccion,
            telefono=telefono
        )
        return usuario

def registrar_nueva_empresa(datos_usuario: dict, nombre: str, categoria: str, direccion: str) -> Usuario:
    """Servicio para registrar un dueño y su negocio de forma atómica."""
    with transaction.atomic():
        usuario = Usuario.objects.create_user(
            rol=Roles.ADMIN,
            **datos_usuario
        )
        Negocio.objects.create(
            propietario=usuario, 
            nombre=nombre, 
            categoria=categoria, 
            direccion=direccion
        )
        return usuario
    
def registrar_repartidor(datos_usuario: dict, vehiculo_id: int, zona_id: int) -> Usuario:
    """
    Maneja la lógica de negocio para registrar un repartidor 
    junto con su perfil logístico de forma atómica.
    """
    with transaction.atomic():
        # 1. Crear el usuario base con rol REPARTIDOR
        usuario = Usuario.objects.create_user(
            rol=Roles.REPARTIDOR, 
            **datos_usuario
        )
        
        # 2. Crear el perfil de Repartidor vinculado
        Repartidor.objects.create(
            usuario=usuario,
            tipo_vehiculo_id=vehiculo_id,
            zona_cobertura_id=zona_id
        )
        
        return usuario
    