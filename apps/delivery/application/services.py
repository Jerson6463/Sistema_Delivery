"""
Capa de aplicación de repartidores.

Asignación automática: cuando un pedido pasa a LISTO_PARA_RECOJO, se busca
un repartidor de la zona, libre y disponible. Si no hay, el pedido se queda
esperando. Cuando un repartidor se libera (entrega un pedido o vuelve a
estar disponible), se reintenta asignar los pedidos que esperan en su zona.

El bloqueo con select_for_update(skip_locked=True) evita que dos procesos
asignen el mismo repartidor a la vez; el UniqueConstraint del Pedido es la
red de seguridad final en la base de datos.
"""
from django.db import transaction

from apps.delivery.models import Repartidor
from apps.orders.domain.states import Estado


class RepartidorService:

    @staticmethod
    def obtener_repartidor_de_usuario(usuario):
        return Repartidor.objects.filter(usuario=usuario).first()

    @staticmethod
    def buscar_disponible_por_zona(zona_id):
        """
        Repartidor de la zona GENERAL (`zona_id` es el id de una Zona),
        aprobado, activo, disponible y SIN pedido activo asignado. Debe
        llamarse dentro de una transacción.
        """
        return (
            Repartidor.objects
            .select_for_update(skip_locked=True)
            .filter(
                activo=True,
                disponible=True,
                usuario__aprobado=True,
                zona_cobertura_id=zona_id,
            )
            .exclude(
                pedidos__estado__in=[Estado.LISTO_PARA_RECOJO, Estado.EN_CAMINO]
            )
            .first()
        )

    @staticmethod
    def asignar_a_pedido(pedido):
        """
        Intenta asignar un repartidor al pedido. Devuelve el repartidor
        asignado o None si no hay ninguno disponible (el pedido se queda
        en LISTO_PARA_RECOJO sin repartidor).
        """
        if pedido.repartidor_id:
            return pedido.repartidor

        # El repartidor cubre una zona GENERAL; el pedido se entrega a un
        # distrito (ZonaEntrega) que pertenece a esa zona.
        zona_general_id = pedido.zona_entrega.zona_id
        repartidor = RepartidorService.buscar_disponible_por_zona(zona_general_id)
        if repartidor is None:
            return None

        pedido.repartidor = repartidor
        pedido.save(update_fields=["repartidor", "actualizado_en"])
        # Notificar al repartidor DESPUÉS del commit.
        from apps.realtime import notifiers
        transaction.on_commit(lambda: notifiers.notificar_asignacion(pedido))
        return repartidor

    @staticmethod
    @transaction.atomic
    def actualizar_disponibilidad(repartidor_id, disponible):
        repartidor = Repartidor.objects.select_for_update().get(pk=repartidor_id)
        repartidor.disponible = disponible
        repartidor.save(update_fields=["disponible", "actualizado_en"])
        if disponible:
            RepartidorService.reintentar_asignaciones_en_zona(repartidor.zona_cobertura_id)
        return repartidor

    @staticmethod
    def reintentar_asignaciones_en_zona(zona_id):
        """
        Asigna pedidos que esperan en la zona general (`zona_id` es el id de
        una Zona), mientras haya repartidores. Los pedidos se filtran por el
        distrito de entrega cuya zona coincide.
        """
        from apps.orders.models import Pedido  # import diferido (evita ciclo)

        pendientes = (
            Pedido.objects.select_for_update()
            .filter(
                estado=Estado.LISTO_PARA_RECOJO,
                repartidor__isnull=True,
                zona_entrega__zona_id=zona_id,
            )
            .order_by("creado_en")
        )
        for pedido in pendientes:
            if RepartidorService.asignar_a_pedido(pedido) is None:
                break  # ya no hay repartidores libres

    @staticmethod
    def obtener_pedido_activo(repartidor):
        from apps.orders.models import Pedido

        return (
            Pedido.objects
            .filter(
                repartidor=repartidor,
                estado__in=[Estado.LISTO_PARA_RECOJO, Estado.EN_CAMINO],
            )
            .select_related("negocio", "zona_entrega", "cliente")
            .first()
        )

    @staticmethod
    def validar_repartidor_asignado(pedido, usuario):
        """Usado en la Fase 7 para EN_CAMINO / ENTREGADO."""
        rep = getattr(usuario, "repartidor", None)
        return rep is not None and pedido.repartidor_id == rep.id


class SeguimientoEntregaService:
    """Ubicación GPS del repartidor durante la entrega."""

    @staticmethod
    @transaction.atomic
    def actualizar_ubicacion(usuario, repartidor_id, latitud, longitud):
        """
        Valida (según el documento): rol repartidor, solo su propia ubicación,
        debe tener un pedido EN_CAMINO. Guarda un SeguimientoEntrega.
        """
        from apps.delivery.models import SeguimientoEntrega
        from apps.orders.models import Pedido
        from apps.shared.domain.exceptions import (
            DomainException, PermisoDominioException,
        )

        rep = getattr(usuario, "repartidor", None)
        if rep is None or rep.id != int(repartidor_id):
            raise PermisoDominioException(
                "Solo puedes actualizar tu propia ubicación."
            )

        pedido = (
            Pedido.objects.filter(repartidor=rep, estado=Estado.EN_CAMINO).first()
        )
        if pedido is None:
            raise DomainException(
                "No tienes un pedido EN_CAMINO para actualizar ubicación."
            )

        seguimiento = SeguimientoEntrega.objects.create(
            pedido=pedido, repartidor=rep, latitud=latitud, longitud=longitud
        )
        # Notificar al tracking DESPUÉS del commit.
        from apps.realtime import notifiers
        transaction.on_commit(
            lambda: notifiers.notificar_ubicacion(pedido, latitud, longitud)
        )
        return seguimiento

    @staticmethod
    def ultima_ubicacion(pedido):
        from apps.delivery.models import SeguimientoEntrega
        return (
            SeguimientoEntrega.objects.filter(pedido=pedido)
            .order_by("-timestamp")
            .first()
        )
