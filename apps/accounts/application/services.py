"""
Capa de aplicación (casos de uso) de cuentas.
"""
from django.db import transaction

from apps.accounts.domain.policies import aprobacion_por_defecto
from apps.accounts.models import User
from apps.businesses.models import Negocio, Zona, ZonaEntrega
from apps.delivery.models import Repartidor
from apps.shared.domain.exceptions import PermisoDominioException


class AccountService:

    @staticmethod
    def registrar_cliente(username, email, password, **extra):
        return AccountService._crear_usuario(
            username, email, password, User.Rol.CLIENTE, **extra
        )

    @staticmethod
    @transaction.atomic
    def registrar_negocio(
        username, email, password, first_name, last_name,
        nombre, categoria, direccion, zona,
    ):
        user = AccountService._crear_usuario(
            username, email, password, User.Rol.NEGOCIO,
            first_name=first_name, last_name=last_name,
        )
        Negocio.objects.create(
            usuario_dueno=user, nombre=nombre, categoria=categoria,
            direccion=direccion, zona=zona,
        )
        return user

    @staticmethod
    @transaction.atomic
    def registrar_repartidor(
        username, email, password, first_name, last_name,
        vehiculo, zona_cobertura,
    ):
        user = AccountService._crear_usuario(
            username, email, password, User.Rol.REPARTIDOR,
            first_name=first_name, last_name=last_name,
        )
        Repartidor.objects.create(
            usuario=user, vehiculo=vehiculo, zona_cobertura=zona_cobertura
        )
        return user

    @staticmethod
    @transaction.atomic
    def actualizar_perfil(user, first_name, last_name, direccion=None,
                          zona_entrega=None, **perfil_data):
        user.first_name = first_name
        user.last_name = last_name
        campos_usuario = ["first_name", "last_name"]
        if direccion is not None:
            user.direccion = direccion
            campos_usuario.append("direccion")
        if zona_entrega is not None:
            user.zona_entrega = zona_entrega
            campos_usuario.append("zona_entrega")
        user.save(update_fields=campos_usuario)

        if user.es_negocio:
            perfil = user.negocio
            campos = ("nombre", "categoria", "direccion", "zona")
        elif user.es_repartidor:
            perfil = user.repartidor
            campos = ("vehiculo", "zona_cobertura")
        else:
            return user

        for campo in campos:
            if campo in perfil_data:
                setattr(perfil, campo, perfil_data[campo])
        perfil.save()
        return user

    @staticmethod
    def opciones_registro():
        distritos = (
            ZonaEntrega.objects.filter(activo=True)
            .select_related("zona")
            .order_by("zona__nombre", "distrito")
        )
        zonas = Zona.objects.filter(activo=True).order_by("nombre")
        return {
            "distritos": [
                {"id": distrito.pk, "distrito": distrito.distrito, "zona": distrito.zona.nombre}
                for distrito in distritos
            ],
            "zonas": [
                {"id": zona.pk, "nombre": zona.nombre}
                for zona in zonas
            ],
            "categorias_negocio": [
                {"value": value, "label": label}
                for value, label in Negocio.Categoria.choices
            ],
            "tipos_vehiculo": [
                {"value": value, "label": label}
                for value, label in Repartidor.Vehiculo.choices
            ],
        }

    @staticmethod
    @transaction.atomic
    def _crear_usuario(username, email, password, rol, **extra):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            rol=rol,
            aprobado=aprobacion_por_defecto(rol),
            **extra,
        )

    @staticmethod
    @transaction.atomic
    def aprobar_usuario(user_id, actor):
        AccountService._exigir_admin(actor)
        user = User.objects.get(pk=user_id)
        user.aprobado = True
        user.save(update_fields=["aprobado"])
        return user

    @staticmethod
    @transaction.atomic
    def rechazar_usuario(user_id, actor):
        AccountService._exigir_admin(actor)
        user = User.objects.get(pk=user_id)
        user.aprobado = False
        user.is_active = False
        user.save(update_fields=["aprobado", "is_active"])
        return user

    @staticmethod
    def _exigir_admin(actor):
        if actor is None or not getattr(actor, "es_admin", False):
            raise PermisoDominioException(
                "Solo un administrador puede aprobar o rechazar cuentas."
            )
