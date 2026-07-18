"""
Consumers de WebSocket.

Cada consumer une la conexión a un grupo y valida que el usuario tenga
derecho a escuchar ese grupo. Los eventos llegan con type="broadcast" y
se reenvían tal cual al cliente como JSON.

La autenticación viene de AuthMiddlewareStack (asgi.py): la cookie de
sesión del login web identifica al usuario en scope["user"].
"""
from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer


class _GrupoConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        self.kwargs = self.scope["url_route"]["kwargs"]
        if not self.user.is_authenticated or not self.autorizado():
            self.close()
            return
        self.group_name = self.nombre_grupo()
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        if getattr(self, "group_name", None):
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )

    def broadcast(self, event):
        """Handler del evento enviado por notifiers._send()."""
        self.send_json(event["data"])

    # --- A implementar por cada consumer ---
    def nombre_grupo(self):
        raise NotImplementedError

    def autorizado(self):
        return True


class TrackingConsumer(_GrupoConsumer):
    """ws/pedidos/{pedido_id}/tracking/ — estado y ubicación en vivo."""

    def nombre_grupo(self):
        return f"pedido_{self.kwargs['pedido_id']}"

    def autorizado(self):
        from apps.orders.application.services import PedidoService
        from apps.orders.models import Pedido
        try:
            pedido = Pedido.objects.select_related("negocio").get(
                pk=self.kwargs["pedido_id"]
            )
        except Pedido.DoesNotExist:
            return False
        return PedidoService.usuario_puede_ver_tracking(pedido, self.user)


class NegocioPedidosConsumer(_GrupoConsumer):
    """ws/negocios/{negocio_id}/pedidos/ — pedidos entrantes del negocio."""

    def nombre_grupo(self):
        return f"negocio_{self.kwargs['negocio_id']}"

    def autorizado(self):
        from apps.businesses.models import Negocio
        if self.user.is_superuser:
            return True
        return Negocio.objects.filter(
            pk=self.kwargs["negocio_id"], usuario_dueno=self.user
        ).exists()


class RepartidorConsumer(_GrupoConsumer):
    """ws/repartidores/{repartidor_id}/pedido-activo/ — asignaciones."""

    def nombre_grupo(self):
        return f"repartidor_{self.kwargs['repartidor_id']}"

    def autorizado(self):
        from apps.delivery.models import Repartidor
        if self.user.is_superuser:
            return True
        return Repartidor.objects.filter(
            pk=self.kwargs["repartidor_id"], usuario=self.user
        ).exists()


class AdminDashboardConsumer(_GrupoConsumer):
    """ws/admin/dashboard/ — métricas del panel admin (Fase 10)."""

    def nombre_grupo(self):
        return "admin_dashboard"

    def autorizado(self):
        return self.user.is_superuser or getattr(self.user, "es_admin", False)
