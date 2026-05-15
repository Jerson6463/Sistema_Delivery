from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Pedido
from .serializers import PedidoSerializer
from .services import MaquinaEstadosPedido
from core.choices import Roles

class PedidoListCreateView(generics.ListCreateAPIView):
    """
    Vista dual:
    - POST: El Cliente crea un pedido.
    - GET: Lista los pedidos filtrados por el rol del usuario (Seguridad total).
    """
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Filtramos para que cada uno vea solo lo que le corresponde
        if user.rol == Roles.CLIENTE:
            return Pedido.objects.filter(cliente__usuario=user).order_by('-creado_en')
        elif user.rol == Roles.ADMIN: # Dueño de Negocio
            return Pedido.objects.filter(negocio__propietario=user).order_by('-creado_en')
        elif user.rol == Roles.REPARTIDOR:
            return Pedido.objects.filter(repartidor__usuario=user).order_by('-creado_en')
        return Pedido.objects.none()

    def perform_create(self, serializer):
        # Al crear, asignamos automáticamente al cliente autenticado
        # Esto evita que alguien cree un pedido a nombre de otro
        serializer.save(cliente=self.request.user.cliente)


class ActualizarEstadoPedidoView(APIView):
    """
    Endpoint para mover el flujo del pedido (Máquina de Estados).
    Utilizado por Negocios y Repartidores.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            pedido = Pedido.objects.get(pk=pk)
        except Pedido.DoesNotExist:
            return Response({"error": "Pedido no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        nuevo_estado = request.data.get('nuevo_estado')
        if not nuevo_estado:
            return Response({"error": "Debe proporcionar el 'nuevo_estado'"}, status=status.HTTP_400_BAD_REQUEST)

        # Invocamos tu lógica de Maquina de Estados
        try:
            maquina = MaquinaEstadosPedido(pedido, request.user)
            maquina.transicionar_a(nuevo_estado)
            
            return Response({
                "mensaje": f"Pedido actualizado a '{nuevo_estado}' con éxito.",
                "id": pedido.id,
                "nuevo_estado": pedido.estado
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Aquí capturamos los ValidationError y PermissionDenied de tu máquina
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)