"""
Capa de aplicación de pedidos.

- carrito en sesión y creación de pedidos.
- máquina de estados y tracking.
- consultas públicas que consumen las views web y API.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Avg
from django.utils import timezone

from apps.businesses.application.services import (
    NegocioService,
    TarifaEnvioService,
)
from apps.businesses.models import Negocio
from apps.catalog.application.services import ProductoService
from apps.catalog.models import Producto
from apps.orders.domain.policies import (
    CLIENTE,
    NEGOCIO,
    REPARTIDOR_ASIGNADO,
    actores_permitidos,
)
from apps.orders.domain.states import Estado, transicion_valida
from apps.orders.models import (
    Calificacion,
    DetallePedido,
    HistorialEstadoPedido,
    Pedido,
)
from apps.realtime import notifiers
from apps.shared.domain.exceptions import (
    CalificacionDuplicadaException,
    DomainException,
    PedidoNoCancelableException,
    PedidoNoEntregadoException,
    PermisoDominioException,
    TransicionEstadoInvalidaException,
)

SESSION_KEY = "carrito"


class PedidoService:

    # =========================================================
    # Carrito en sesión
    # =========================================================
    @staticmethod
    def obtener_carrito(session):
        data = session.get(SESSION_KEY)
        if not data:
            data = {"negocio_id": None, "items": {}}
            session[SESSION_KEY] = data
        return data

    @staticmethod
    def agregar_al_carrito(session, producto_id, cantidad=1):
        try:
            producto = Producto.objects.select_related("negocio").get(
                pk=producto_id, activo=True
            )
        except Producto.DoesNotExist:
            raise DomainException("El producto no está disponible.")

        NegocioService.validar_abierto(producto.negocio)

        data = PedidoService.obtener_carrito(session)
        if data["negocio_id"] not in (None, producto.negocio_id):
            data = {"negocio_id": None, "items": {}}
        data["negocio_id"] = producto.negocio_id

        pid = str(producto.id)
        data["items"][pid] = data["items"].get(pid, 0) + cantidad
        PedidoService._guardar_carrito(session, data)
        return producto

    @staticmethod
    def actualizar_carrito(session, producto_id, cantidad):
        data = PedidoService.obtener_carrito(session)
        pid = str(producto_id)
        if cantidad <= 0:
            return PedidoService.remover_del_carrito(session, producto_id)
        if pid in data["items"]:
            data["items"][pid] = cantidad
            PedidoService._guardar_carrito(session, data)
        return data

    @staticmethod
    def remover_del_carrito(session, producto_id):
        data = PedidoService.obtener_carrito(session)
        data["items"].pop(str(producto_id), None)
        if not data["items"]:
            data["negocio_id"] = None
        PedidoService._guardar_carrito(session, data)
        return data

    @staticmethod
    def limpiar_carrito(session):
        data = {"negocio_id": None, "items": {}}
        PedidoService._guardar_carrito(session, data)
        return data

    @staticmethod
    def lineas_carrito(session):
        data = PedidoService.obtener_carrito(session)
        ids = [int(pid) for pid in data["items"].keys()]
        productos = {
            p.id: p
            for p in Producto.objects.filter(id__in=ids, activo=True)
        }
        lineas = []
        for pid, cantidad in data["items"].items():
            producto = productos.get(int(pid))
            if producto:
                lineas.append({
                    "producto": producto,
                    "cantidad": cantidad,
                    "subtotal": producto.precio * cantidad,
                })
        return lineas

    @staticmethod
    def items_para_crear_pedido(session):
        data = PedidoService.obtener_carrito(session)
        return [
            {"producto_id": int(pid), "cantidad": cantidad}
            for pid, cantidad in data["items"].items()
        ]

    @staticmethod
    def resumen_carrito(session):
        data = PedidoService.obtener_carrito(session)
        lineas = PedidoService.lineas_carrito(session)
        subtotal = sum((linea["subtotal"] for linea in lineas), Decimal("0"))
        zonas = []
        if data["negocio_id"]:
            zonas = TarifaEnvioService.listar_por_negocio(data["negocio_id"])
        return {
            "negocio_id": data["negocio_id"],
            "items": data["items"],
            "lineas": lineas,
            "subtotal": subtotal,
            "vacio": not data["items"],
            "zonas": zonas,
        }

    @staticmethod
    def crear_pedido_desde_carrito(
        cliente, session, direccion_entrega, zona_entrega_id, metodo_pago
    ):
        resumen = PedidoService.resumen_carrito(session)
        if resumen["vacio"]:
            raise DomainException("Tu carrito está vacío.")

        pedido = PedidoService.crear_pedido(
            cliente=cliente,
            negocio_id=resumen["negocio_id"],
            items=PedidoService.items_para_crear_pedido(session),
            direccion_entrega=direccion_entrega,
            zona_entrega_id=zona_entrega_id,
            metodo_pago=metodo_pago,
        )
        PedidoService.limpiar_carrito(session)
        return pedido

    # =========================================================
    # Creación
    # =========================================================
    @staticmethod
    @transaction.atomic
    def crear_pedido(cliente, negocio_id, items, direccion_entrega,
                     zona_entrega_id, metodo_pago):
        if not items:
            raise DomainException("El pedido no tiene productos.")

        direccion_entrega = (direccion_entrega or "").strip()
        if not direccion_entrega:
            raise DomainException(
                "Debes indicar una dirección de entrega para el pedido."
            )

        try:
            negocio = Negocio.objects.get(pk=negocio_id, activo=True, aprobado=True)
        except Negocio.DoesNotExist:
            raise DomainException("El negocio no está disponible.")
        NegocioService.validar_abierto(negocio)

        TarifaEnvioService.validar_zona_cubierta(negocio_id, zona_entrega_id)
        costo_envio = TarifaEnvioService.calcular_costo_envio(
            negocio_id, zona_entrega_id
        )

        producto_ids = [item["producto_id"] for item in items]
        productos = {
            p.id: p
            for p in Producto.objects.select_for_update().filter(
                id__in=producto_ids, activo=True
            )
        }

        subtotal = Decimal("0")
        for item in items:
            producto = productos.get(item["producto_id"])
            if producto is None or producto.negocio_id != negocio.id:
                raise DomainException(
                    "Un producto no existe o no pertenece al negocio."
                )
            cantidad = item["cantidad"]
            ProductoService.validar_stock(producto, cantidad)
            subtotal += producto.precio * cantidad

        total = subtotal + costo_envio

        pedido = Pedido.objects.create(
            cliente=cliente,
            negocio=negocio,
            estado=Estado.RECIBIDO,
            subtotal=subtotal,
            costo_envio=costo_envio,
            total=total,
            direccion_entrega=direccion_entrega,
            zona_entrega_id=zona_entrega_id,
            metodo_pago=metodo_pago,
        )

        detalles = []
        for item in items:
            producto = productos[item["producto_id"]]
            cantidad = item["cantidad"]
            ProductoService.descontar_stock(producto, cantidad)
            detalles.append(DetallePedido(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=producto.precio * cantidad,
            ))
        DetallePedido.objects.bulk_create(detalles)

        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            estado_anterior=None,
            estado_nuevo=Estado.RECIBIDO,
            actor=cliente,
        )
        transaction.on_commit(lambda: notifiers.notificar_pedido_creado(pedido))
        return pedido

    # =========================================================
    # Máquina de estados
    # =========================================================
    @staticmethod
    @transaction.atomic
    def cambiar_estado(pedido_id, nuevo_estado, actor, comentario=""):
        pedido = (
            Pedido.objects.select_for_update()
            .select_related("negocio")
            .get(pk=pedido_id)
        )
        PedidoService._transicionar(pedido, nuevo_estado, actor, comentario)
        return pedido

    @staticmethod
    def confirmar_pedido(pedido_id, usuario_negocio):
        return PedidoService.cambiar_estado(
            pedido_id, Estado.CONFIRMADO, usuario_negocio
        )

    @staticmethod
    def marcar_en_preparacion(pedido_id, usuario_negocio):
        return PedidoService.cambiar_estado(
            pedido_id, Estado.EN_PREPARACION, usuario_negocio
        )

    @staticmethod
    @transaction.atomic
    def marcar_listo_para_recojo(pedido_id, usuario_negocio):
        from apps.delivery.application.services import RepartidorService

        pedido = PedidoService.cambiar_estado(
            pedido_id, Estado.LISTO_PARA_RECOJO, usuario_negocio
        )
        RepartidorService.asignar_a_pedido(pedido)
        return pedido

    @staticmethod
    def marcar_en_camino(pedido_id, usuario_repartidor):
        return PedidoService.cambiar_estado(
            pedido_id, Estado.EN_CAMINO, usuario_repartidor
        )

    @staticmethod
    @transaction.atomic
    def marcar_entregado(pedido_id, usuario_repartidor):
        from apps.delivery.application.services import RepartidorService

        pedido = (
            Pedido.objects.select_for_update()
            .select_related("negocio")
            .get(pk=pedido_id)
        )
        PedidoService._transicionar(pedido, Estado.ENTREGADO, usuario_repartidor, "")
        pedido.entregado_en = timezone.now()
        pedido.save(update_fields=["entregado_en", "actualizado_en"])
        RepartidorService.reintentar_asignaciones_en_zona(pedido.zona_entrega.zona_id)
        return pedido

    @staticmethod
    @transaction.atomic
    def cancelar_pedido(pedido_id, actor, motivo=""):
        pedido = (
            Pedido.objects.select_for_update()
            .select_related("negocio")
            .get(pk=pedido_id)
        )

        if pedido.estado not in (Estado.RECIBIDO, Estado.CONFIRMADO):
            raise PedidoNoCancelableException()

        categorias = actores_permitidos(pedido.estado, Estado.CANCELADO)
        if not PedidoService._actor_autorizado(pedido, actor, categorias):
            raise PermisoDominioException("No puedes cancelar este pedido.")

        es_dueno_negocio = (
            not getattr(actor, "is_superuser", False)
            and pedido.negocio.usuario_dueno_id == actor.id
        )
        cancelado_por = (
            Pedido.CanceladoPor.NEGOCIO
            if es_dueno_negocio else Pedido.CanceladoPor.CLIENTE
        )

        PedidoService._restaurar_stock(pedido)

        anterior = pedido.estado
        pedido.estado = Estado.CANCELADO
        pedido.cancelado_por = cancelado_por
        pedido.motivo_cancelacion = motivo
        pedido.fecha_cancelacion = timezone.now()
        pedido.save(update_fields=[
            "estado", "cancelado_por", "motivo_cancelacion",
            "fecha_cancelacion", "actualizado_en",
        ])

        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            estado_anterior=anterior,
            estado_nuevo=Estado.CANCELADO,
            actor=actor,
            comentario=motivo or "",
        )
        transaction.on_commit(lambda: notifiers.notificar_estado(pedido))
        return pedido

    @staticmethod
    def rechazar_pedido(pedido_id, usuario_negocio, motivo=""):
        return PedidoService.cancelar_pedido(pedido_id, usuario_negocio, motivo)

    # =========================================================
    # Consultas
    # =========================================================
    @staticmethod
    def obtener_tracking(pedido_id, usuario):
        from apps.delivery.application.services import SeguimientoEntregaService

        pedido = (
            Pedido.objects
            .select_related("negocio", "repartidor__usuario", "zona_entrega")
            .prefetch_related("historial")
            .get(pk=pedido_id)
        )
        if not PedidoService.usuario_puede_ver_tracking(pedido, usuario):
            raise PermisoDominioException("No tienes acceso a este pedido.")

        etiquetas = dict(Estado.CHOICES)
        timeline = [
            {
                "estado": h.estado_nuevo,
                "estado_display": etiquetas.get(h.estado_nuevo, h.estado_nuevo),
                "timestamp": h.creado_en.isoformat(),
            }
            for h in pedido.historial.all()
        ]

        repartidor_data = None
        if pedido.repartidor_id:
            repartidor = pedido.repartidor
            repartidor_data = {
                "id": repartidor.id,
                "nombre": (
                    repartidor.usuario.get_full_name()
                    or repartidor.usuario.username
                ),
                "vehiculo": repartidor.get_vehiculo_display(),
            }

        ultima = SeguimientoEntregaService.ultima_ubicacion(pedido)
        ubicacion_data = None
        if ultima:
            ubicacion_data = {
                "latitud": float(ultima.latitud),
                "longitud": float(ultima.longitud),
                "timestamp": ultima.timestamp.isoformat(),
            }

        return {
            "pedido_id": pedido.id,
            "estado_actual": pedido.estado,
            "estado_display": pedido.get_estado_display(),
            "repartidor": repartidor_data,
            "timeline": timeline,
            "ultima_ubicacion": ubicacion_data,
        }

    @staticmethod
    def listar_mis_pedidos(cliente):
        return (
            Pedido.objects.filter(cliente=cliente)
            .select_related("negocio", "repartidor__usuario", "calificacion")
            .order_by("-creado_en")
        )

    @staticmethod
    def listar_pedidos_negocio(negocio, solo_activos=True):
        qs = (
            Pedido.objects.filter(negocio=negocio)
            .select_related("cliente")
            .prefetch_related("detalles__producto")
            .order_by("-creado_en")
        )
        if solo_activos:
            qs = qs.filter(estado__in=[
                Estado.RECIBIDO,
                Estado.CONFIRMADO,
                Estado.EN_PREPARACION,
                Estado.LISTO_PARA_RECOJO,
            ])
        return qs

    @staticmethod
    def listar_para_usuario(usuario):
        if usuario.rol == "CLIENTE":
            return PedidoService.listar_mis_pedidos(usuario)
        if usuario.rol == "NEGOCIO":
            negocio = NegocioService.obtener_negocio_de_usuario(usuario)
            if negocio is None:
                return []
            return PedidoService.listar_pedidos_negocio(negocio, solo_activos=False)
        if getattr(usuario, "is_superuser", False):
            return (
                Pedido.objects.all()
                .select_related("negocio")
                .order_by("-creado_en")
            )
        return []

    @staticmethod
    def obtener_detalle_para_usuario(pedido_id, usuario):
        pedido = (
            Pedido.objects
            .select_related("negocio", "repartidor__usuario", "calificacion")
            .prefetch_related("detalles__producto")
            .get(pk=pedido_id)
        )
        if not PedidoService.usuario_puede_ver_tracking(pedido, usuario):
            raise PermisoDominioException("No tienes acceso a este pedido.")
        return pedido

    # =========================================================
    # Helpers privados
    # =========================================================
    @staticmethod
    def _guardar_carrito(session, data):
        session[SESSION_KEY] = data
        if hasattr(session, "modified"):
            session.modified = True

    @staticmethod
    def _transicionar(pedido, nuevo_estado, actor, comentario):
        if not transicion_valida(pedido.estado, nuevo_estado):
            raise TransicionEstadoInvalidaException(
                f"No se puede pasar de {pedido.estado} a {nuevo_estado}."
            )
        categorias = actores_permitidos(pedido.estado, nuevo_estado)
        if not PedidoService._actor_autorizado(pedido, actor, categorias):
            raise PermisoDominioException(
                "No tienes permiso para este cambio de estado."
            )

        anterior = pedido.estado
        pedido.estado = nuevo_estado
        pedido.save(update_fields=["estado", "actualizado_en"])

        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            estado_anterior=anterior,
            estado_nuevo=nuevo_estado,
            actor=actor,
            comentario=comentario or "",
        )
        transaction.on_commit(lambda: notifiers.notificar_estado(pedido))

    @staticmethod
    def usuario_puede_ver_tracking(pedido, usuario):
        if getattr(usuario, "is_superuser", False):
            return True
        if pedido.cliente_id == usuario.id:
            return True
        if pedido.negocio.usuario_dueno_id == usuario.id:
            return True
        repartidor = getattr(usuario, "repartidor", None)
        return repartidor is not None and pedido.repartidor_id == repartidor.id

    @staticmethod
    def _actor_autorizado(pedido, actor, categorias):
        if getattr(actor, "is_superuser", False):
            return True
        if NEGOCIO in categorias and pedido.negocio.usuario_dueno_id == actor.id:
            return True
        if CLIENTE in categorias and pedido.cliente_id == actor.id:
            return True
        if REPARTIDOR_ASIGNADO in categorias:
            rep_id = getattr(pedido, "repartidor_id", None)
            rep_actor = getattr(getattr(actor, "repartidor", None), "id", None)
            if rep_id is not None and rep_id == rep_actor:
                return True
        return False

    @staticmethod
    def _restaurar_stock(pedido):
        detalles = list(pedido.detalles.all())
        ids = [detalle.producto_id for detalle in detalles]
        productos = {
            producto.id: producto
            for producto in Producto.objects.select_for_update().filter(id__in=ids)
        }
        for detalle in detalles:
            producto = productos.get(detalle.producto_id)
            if producto:
                ProductoService.restaurar_stock(producto, detalle.cantidad)


class CalificacionService:
    """Calificación de un pedido entregado."""

    _CUANTIA = Decimal("0.01")

    @staticmethod
    @transaction.atomic
    def calificar_pedido(cliente, pedido_id, *, puntaje_negocio,
                         puntaje_repartidor=None, comentario_negocio="",
                         comentario_repartidor=""):
        pedido = Pedido.objects.select_for_update().get(pk=pedido_id)

        es_dueno = (
            not getattr(cliente, "is_superuser", False)
            and pedido.cliente_id == cliente.id
        )
        if not (getattr(cliente, "is_superuser", False) or es_dueno):
            raise PermisoDominioException("No puedes calificar este pedido.")

        if pedido.estado != Estado.ENTREGADO:
            raise PedidoNoEntregadoException()

        if Calificacion.objects.filter(pedido=pedido).exists():
            raise CalificacionDuplicadaException()

        CalificacionService._validar_puntaje(puntaje_negocio, obligatorio=True)
        if pedido.repartidor_id is None:
            puntaje_repartidor = None
        CalificacionService._validar_puntaje(puntaje_repartidor, obligatorio=False)

        calificacion = Calificacion.objects.create(
            pedido=pedido,
            cliente=pedido.cliente,
            negocio=pedido.negocio,
            repartidor=pedido.repartidor,
            puntaje_negocio=puntaje_negocio,
            puntaje_repartidor=puntaje_repartidor,
            comentario_negocio=(comentario_negocio or "").strip(),
            comentario_repartidor=(comentario_repartidor or "").strip(),
            creado_por=cliente,
        )

        CalificacionService._recalcular_promedio_negocio(pedido.negocio_id)
        if pedido.repartidor_id and puntaje_repartidor is not None:
            CalificacionService._recalcular_promedio_repartidor(pedido.repartidor_id)

        return calificacion

    @staticmethod
    def _validar_puntaje(puntaje, *, obligatorio):
        if puntaje is None:
            if obligatorio:
                raise DomainException("Debes indicar una calificación.")
            return
        if not isinstance(puntaje, int) or not (
            Calificacion.PUNTAJE_MIN <= puntaje <= Calificacion.PUNTAJE_MAX
        ):
            raise DomainException(
                f"La calificación debe estar entre {Calificacion.PUNTAJE_MIN} "
                f"y {Calificacion.PUNTAJE_MAX} estrellas."
            )

    @staticmethod
    def _promedio(valor) -> Decimal:
        if valor is None:
            return Decimal("0.00")
        return Decimal(str(valor)).quantize(
            CalificacionService._CUANTIA,
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _recalcular_promedio_negocio(negocio_id):
        agregado = (
            Calificacion.objects.filter(
                negocio_id=negocio_id,
                pedido__estado=Estado.ENTREGADO,
            ).aggregate(promedio=Avg("puntaje_negocio"))
        )
        Negocio.objects.filter(pk=negocio_id).update(
            calificacion_promedio=CalificacionService._promedio(
                agregado["promedio"]
            )
        )

    @staticmethod
    def _recalcular_promedio_repartidor(repartidor_id):
        from apps.delivery.models import Repartidor

        agregado = (
            Calificacion.objects.filter(
                repartidor_id=repartidor_id,
                pedido__estado=Estado.ENTREGADO,
                puntaje_repartidor__isnull=False,
            ).aggregate(promedio=Avg("puntaje_repartidor"))
        )
        Repartidor.objects.filter(pk=repartidor_id).update(
            calificacion_promedio=CalificacionService._promedio(
                agregado["promedio"]
            )
        )
