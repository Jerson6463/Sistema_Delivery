from django.urls import path

from apps.orders.web import views

urlpatterns = [
    # Cliente: carrito y pedidos
    path("carrito/", views.ver_carrito, name="ver_carrito"),
    path("carrito/agregar/<int:producto_id>/", views.agregar_al_carrito, name="agregar_al_carrito"),
    path("carrito/actualizar/<int:producto_id>/", views.actualizar_carrito, name="actualizar_carrito"),
    path("carrito/remover/<int:producto_id>/", views.remover_del_carrito, name="remover_del_carrito"),
    path("carrito/confirmar/", views.confirmar_pedido, name="confirmar_pedido"),
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),
    path("pedidos/<int:pedido_id>/tracking/", views.tracking_pedido, name="tracking_pedido"),
    path("mis-pedidos/<int:pedido_id>/cancelar/", views.cancelar_pedido_cliente, name="cancelar_pedido_cliente"),
    path("mis-pedidos/<int:pedido_id>/calificar/", views.calificar_pedido, name="calificar_pedido"),

    # Negocio: panel de pedidos y acciones de estado
    path("panel/negocio/pedidos/", views.panel_negocio_pedidos, name="panel_negocio_pedidos"),
    path("panel/negocio/pedidos/<int:pedido_id>/<str:accion>/", views.accion_negocio, name="accion_negocio"),
]