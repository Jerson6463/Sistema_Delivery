from django.urls import re_path

from apps.realtime import consumers

websocket_urlpatterns = [
    re_path(r"ws/pedidos/(?P<pedido_id>\d+)/tracking/$", consumers.TrackingConsumer.as_asgi()),
    re_path(r"ws/negocios/(?P<negocio_id>\d+)/pedidos/$", consumers.NegocioPedidosConsumer.as_asgi()),
    re_path(r"ws/repartidores/(?P<repartidor_id>\d+)/pedido-activo/$", consumers.RepartidorConsumer.as_asgi()),
    re_path(r"ws/admin/dashboard/$", consumers.AdminDashboardConsumer.as_asgi()),
]