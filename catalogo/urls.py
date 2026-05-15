from django.urls import path
from .views import (
    NegocioListView, NegocioDetailView, 
    ZonaListView, TipoVehiculoListView,
    ProductoListCreateView
)

urlpatterns = [
    # Rutas del cliente
    path('negocios/', NegocioListView.as_view(), name='lista_negocios'),
    path('negocios/<int:pk>/', NegocioDetailView.as_view(), name='detalle_negocio'),
    
    # Rutas para llenar los selectores en el Frontend
    path('zonas/', ZonaListView.as_view(), name='lista_zonas'),
    path('vehiculos/', TipoVehiculoListView.as_view(), name='lista_vehiculos'),
    
    # Rutas protegidas de la Empresa
    path('mis-productos/', ProductoListCreateView.as_view(), name='mis_productos'),
]