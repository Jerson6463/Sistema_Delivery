from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.api.serializers import (
    CambiarEstadoSerializer, CrearPedidoSerializer, PedidoSerializer,
)
from apps.orders.application.services import PedidoService
from apps.orders.domain.states import Estado
from apps.orders.models import Pedido
from apps.shared.domain.exceptions import DomainException, PermisoDominioException


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def pedidos(request):
    if request.method == "POST":
        return _crear_pedido(request)
    return _listar_pedidos(request)


def _crear_pedido(request):
    if not (request.user.is_superuser or request.user.rol == "CLIENTE"):
        return Response({"error": "SOLO_CLIENTE"}, status=403)
    ser = CrearPedidoSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    try:
        pedido = PedidoService.crear_pedido(
            cliente=request.user,
            negocio_id=data["negocio_id"],
            items=[dict(itema) for itema in data["items"]],
            direccion_entrega=data["direccion_entrega"].strip() or request.user.direccion,
            zona_entrega_id=data["zona_entrega_id"],
            metodo_pago=data["metodo_pago"],
        )
    except DomainException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=400)
    return Response(PedidoSerializer(pedido).data, status=201)


def _listar_pedidos(request):
    qs = PedidoService.listar_para_usuario(request.user)
    return Response(PedidoSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detalle_pedido(request, pedido_id):
    try:
        pedido = PedidoService.obtener_detalle_para_usuario(pedido_id, request.user)
    except Pedido.DoesNotExist:
        return Response({"error": "NO_ENCONTRADO"}, status=404)
    except PermisoDominioException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=403)
    return Response(PedidoSerializer(pedido).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cambiar_estado(request, pedido_id):
    ser = CambiarEstadoSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    nuevo = ser.validated_data["estado"]
    motivo = ser.validated_data.get("motivo", "")
    try:
        if nuevo == Estado.CANCELADO:
            pedido = PedidoService.cancelar_pedido(pedido_id, request.user, motivo)
        else:
            pedido = PedidoService.cambiar_estado(pedido_id, nuevo, request.user, motivo)
    except Pedido.DoesNotExist:
        return Response({"error": "NO_ENCONTRADO"}, status=404)
    except PermisoDominioException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=403)
    except DomainException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=400)
    return Response(PedidoSerializer(pedido).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tracking(request, pedido_id):
    try:
        data = PedidoService.obtener_tracking(pedido_id, request.user)
    except Pedido.DoesNotExist:
        return Response({"error": "NO_ENCONTRADO"}, status=404)
    except PermisoDominioException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=403)
    except DomainException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=400)
    return Response(data)
