from django.urls import path

from apps.orders.api import views

urlpatterns = [
    path("", views.pedidos, name="api_pedidos"),
    path("<int:pedido_id>/", views.detalle_pedido, name="api_pedido_detalle"),
    path("<int:pedido_id>/estado/", views.cambiar_estado, name="api_cambiar_estado"),
    path("<int:pedido_id>/tracking/", views.tracking, name="api_tracking"),
]