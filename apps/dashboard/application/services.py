"""
Capa de aplicación del panel de administración.

Concentra las métricas del dashboard y las acciones de aprobación /
rechazo de negocios y repartidores. Aprobar un negocio activa TANTO la
visibilidad del negocio (Negocio.aprobado) COMO el acceso del dueño
(User.aprobado), que es la unión de los dos flags que veníamos arrastrando.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.businesses.application.services import TarifaEnvioService
from apps.businesses.models import Negocio
from apps.delivery.models import Repartidor
from apps.orders.domain.states import Estado
from apps.orders.models import Pedido
from apps.shared.domain.exceptions import DomainException, PermisoDominioException


class AdminPanelService:

    # =========================================================
    # Métricas del dashboard
    # =========================================================
    @staticmethod
    def metricas():
        hoy = timezone.localdate()
        pedidos_hoy = Pedido.objects.filter(creado_en__date=hoy)
        entregados_hoy = Pedido.objects.filter(
            estado=Estado.ENTREGADO, entregado_en__date=hoy
        )
        total_vendido = entregados_hoy.aggregate(s=Sum("total"))["s"] or Decimal("0")

        return {
            "pedidos_hoy": pedidos_hoy.count(),
            "entregados_hoy": entregados_hoy.count(),
            "cancelados_hoy": Pedido.objects.filter(
                estado=Estado.CANCELADO, fecha_cancelacion__date=hoy
            ).count(),
            "total_vendido": total_vendido,
            "negocios_activos": Negocio.objects.filter(
                activo=True, aprobado=True
            ).count(),
            "repartidores_disponibles": Repartidor.objects.filter(
                activo=True, disponible=True, usuario__aprobado=True
            ).count(),
            "pendientes_repartidor": Pedido.objects.filter(
                estado=Estado.LISTO_PARA_RECOJO, repartidor__isnull=True
            ).count(),
        }

    # =========================================================
    # Listas operativas
    # =========================================================
    @staticmethod
    def negocios_pendientes():
        return Negocio.objects.filter(aprobado=False, activo=True).select_related(
            "usuario_dueno"
        )

    @staticmethod
    def repartidores_pendientes():
        return Repartidor.objects.filter(
            usuario__aprobado=False, activo=True
        ).select_related("usuario", "zona_cobertura")

    @staticmethod
    def pedidos_del_dia():
        hoy = timezone.localdate()
        return (
            Pedido.objects.filter(creado_en__date=hoy)
            .select_related("cliente", "negocio")
            .order_by("-creado_en")
        )

    @staticmethod
    def negocios_activos():
        return Negocio.objects.filter(activo=True, aprobado=True).order_by("nombre")

    @staticmethod
    def repartidores_disponibles():
        return Repartidor.objects.filter(
            activo=True, disponible=True, usuario__aprobado=True
        ).select_related("usuario", "zona_cobertura")

    # =========================================================
    # Aprobación / rechazo
    # =========================================================
    @staticmethod
    @transaction.atomic
    def aprobar_negocio(negocio_id, actor):
        AdminPanelService._exigir_admin(actor)
        if not TarifaEnvioService.negocio_tiene_tarifas(negocio_id):
            raise DomainException(
                "Configura al menos una zona de envío con su costo antes de "
                "activar el negocio."
            )
        negocio = Negocio.objects.select_related("usuario_dueno").get(pk=negocio_id)
        negocio.aprobado = True
        negocio.save(update_fields=["aprobado", "actualizado_en"])
        u = negocio.usuario_dueno
        u.aprobado = True
        u.is_active = True
        u.save(update_fields=["aprobado", "is_active"])
        return negocio

    @staticmethod
    @transaction.atomic
    def aprobar_repartidor(repartidor_id, actor):
        AdminPanelService._exigir_admin(actor)
        rep = Repartidor.objects.select_related("usuario").get(pk=repartidor_id)
        u = rep.usuario
        u.aprobado = True
        u.is_active = True
        u.save(update_fields=["aprobado", "is_active"])
        return rep

    @staticmethod
    @transaction.atomic
    def rechazar_negocio(negocio_id, actor):
        AdminPanelService._exigir_admin(actor)
        negocio = Negocio.objects.select_related("usuario_dueno").get(pk=negocio_id)
        u = negocio.usuario_dueno
        u.aprobado = False
        u.is_active = False
        u.save(update_fields=["aprobado", "is_active"])
        return negocio

    @staticmethod
    @transaction.atomic
    def rechazar_repartidor(repartidor_id, actor):
        AdminPanelService._exigir_admin(actor)
        rep = Repartidor.objects.select_related("usuario").get(pk=repartidor_id)
        u = rep.usuario
        u.aprobado = False
        u.is_active = False
        u.save(update_fields=["aprobado", "is_active"])
        return rep

    @staticmethod
    def _exigir_admin(actor):
        if not getattr(actor, "es_admin", False):
            raise PermisoDominioException(
                "Solo un administrador puede realizar esta acción."
            )