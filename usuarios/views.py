# usuarios/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import RegistroClienteSerializer, RegistroEmpresaSerializer, PerfilUsuarioSerializer

class RegistroClienteView(generics.CreateAPIView):
    serializer_class = RegistroClienteSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(
            {"mensaje": f"Cliente {usuario.username} registrado exitosamente."},
            status=status.HTTP_201_CREATED
        )

class RegistroEmpresaView(generics.CreateAPIView):
    serializer_class = RegistroEmpresaSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(
            {"mensaje": f"Empresa {usuario.username} registrada exitosamente."},
            status=status.HTTP_201_CREATED
        )
    
class PerfilUsuarioView(APIView):
    # CRÍTICO: Esta vista requiere que el usuario tenga un token válido
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user contiene mágicamente al usuario dueño del token
        serializer = PerfilUsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)