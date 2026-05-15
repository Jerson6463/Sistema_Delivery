from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Negocio, Producto, Zona, TipoVehiculo
from .serializers import (
    NegocioListSerializer, 
    NegocioDetailSerializer, 
    ProductoSerializer,
    ZonaSerializer,
    TipoVehiculoSerializer
)

# ==========================================
# VISTAS PÚBLICAS (Para la App del Cliente)
# ==========================================

class NegocioListView(generics.ListAPIView):
    """Lista todos los negocios activos sin cargar sus productos (Ligero)"""
    queryset = Negocio.objects.filter(activo=True)
    serializer_class = NegocioListSerializer
    permission_classes = [AllowAny]

class NegocioDetailView(generics.RetrieveAPIView):
    """Muestra un negocio específico con todo su menú de productos anidado"""
    queryset = Negocio.objects.filter(activo=True)
    serializer_class = NegocioDetailSerializer
    permission_classes = [AllowAny]


# ==========================================
# VISTAS MAESTRAS (Para el registro en Vue.js)
# ==========================================

class ZonaListView(generics.ListAPIView):
    """Lista las zonas para que el Repartidor elija al registrarse"""
    queryset = Zona.objects.all()
    serializer_class = ZonaSerializer
    permission_classes = [AllowAny]

class TipoVehiculoListView(generics.ListAPIView):
    """Lista los vehículos para que el Repartidor elija al registrarse"""
    queryset = TipoVehiculo.objects.filter(activo=True)
    serializer_class = TipoVehiculoSerializer
    permission_classes = [AllowAny]


# ==========================================
# VISTAS PROTEGIDAS (Para el Dueño del Negocio)
# ==========================================

class ProductoListCreateView(generics.ListCreateAPIView):
    """Permite al dueño del negocio ver sus propios platos y crear nuevos"""
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios con Token JWT

    def get_queryset(self):
        # Filtra para que el dueño solo vea los productos de SU restaurante
        return Producto.objects.filter(negocio__propietario=self.request.user)

    def perform_create(self, serializer):
        # Cuando el dueño crea un producto, Django le asigna su negocio automáticamente
        # Evita que un dueño cree productos para la competencia
        negocio_del_usuario = self.request.user.negocio 
        serializer.save(negocio=negocio_del_usuario)