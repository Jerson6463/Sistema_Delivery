from django.urls import path

from apps.delivery.web import views

urlpatterns = [
    path("mi-pedido/", views.mi_pedido, name="mi_pedido"),
    path("mi-pedido/estado/", views.estado_pedido_activo, name="estado_pedido_activo"),
    path("disponibilidad/", views.toggle_disponibilidad, name="toggle_disponibilidad"),
    path("mi-pedido/recogido/", views.marcar_recogido, name="marcar_recogido"),
    path("mi-pedido/entregado/", views.marcar_entregado, name="marcar_entregado"),
]