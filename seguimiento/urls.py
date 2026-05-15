from django.urls import path
from .views import ActualizarUbicacionView, ObtenerUltimaUbicacionView

urlpatterns = [
    path('pedidos/<int:pedido_id>/actualizar/', ActualizarUbicacionView.as_view(), name='actualizar_ubicacion'),
    path('pedidos/<int:pedido_id>/rastrear/', ObtenerUltimaUbicacionView.as_view(), name='rastrear_pedido'),
]