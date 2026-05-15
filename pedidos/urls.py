from django.urls import path
from .views import PedidoListCreateView, ActualizarEstadoPedidoView

urlpatterns = [
    # Historial y Creación
    path('', PedidoListCreateView.as_view(), name='pedidos_historial_crear'),
    
    # Cambio de estados: /api/pedidos/5/transicion/
    path('<int:pk>/transicion/', ActualizarEstadoPedidoView.as_view(), name='pedido_transicion'),
]