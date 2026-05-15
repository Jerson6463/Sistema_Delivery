from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .serializers import SeguimientoEntregaSerializer
from pedidos.models import Pedido
from core.choices import Roles, Estados

class ActualizarUbicacionView(APIView):
    """
    El repartidor envía un nuevo punto GPS. 
    Se crea un nuevo registro en el historial.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pedido_id):
        usuario = request.user
        pedido = get_object_or_404(Pedido, id=pedido_id)

        # Validaciones de seguridad
        if usuario.rol != Roles.REPARTIDOR or pedido.repartidor != usuario.perfil_repartidor:
            return Response({"error": "No autorizado para este pedido."}, status=status.HTTP_403_FORBIDDEN)
        
        if pedido.estado != Estados.EN_CAMINO:
            return Response({"error": "El pedido no está 'EN CAMINO'."}, status=status.HTTP_400_BAD_REQUEST)

        # Creamos un nuevo registro de ubicación (Historial)
        serializer = SeguimientoEntregaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(pedido=pedido)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ObtenerUltimaUbicacionView(APIView):
    """
    El cliente obtiene el ÚLTIMO punto registrado para mover el icono en su mapa.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pedido_id):
        pedido = get_object_or_404(Pedido, id=pedido_id)

        if pedido.cliente.usuario != request.user:
            return Response({"error": "No tienes permiso para rastrear este pedido."}, status=status.HTTP_403_FORBIDDEN)

        # Gracias a ordering = ['-timestamp'] en tu Meta, .first() nos da la más reciente
        ultima_ubicacion = pedido.historial_ubicaciones.first()
        
        if not ultima_ubicacion:
            return Response({"error": "Aún no hay coordenadas registradas."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SeguimientoEntregaSerializer(ultima_ubicacion)
        return Response(serializer.data)