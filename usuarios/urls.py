from django.urls import path
from .views import RegistroClienteView, RegistroEmpresaView, PerfilUsuarioView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # 1. Rutas de Registro
    path('registro/cliente/', RegistroClienteView.as_view(), name='registro_cliente'),
    path('registro/empresa/', RegistroEmpresaView.as_view(), name='registro_empresa'),
    
    # 2. Rutas de Autenticación JWT (El Login)
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='login_refresh'),

    # 3. Ruta de Perfil
    path('me/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
]