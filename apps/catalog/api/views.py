from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.businesses.application.services import NegocioService
from apps.catalog.api.serializers import ProductoSerializer, ProductoWriteSerializer
from apps.catalog.application.services import ProductoService
from apps.shared.domain.exceptions import DomainException
from apps.shared.permissions import IsNegocio


@api_view(["POST"])
@permission_classes([IsNegocio])
def crear_producto(request):
    negocio = NegocioService.obtener_negocio_de_usuario(request.user)
    if negocio is None:
        return Response({"error": "SIN_NEGOCIO"}, status=400)
    ser = ProductoWriteSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    producto = ProductoService.crear_producto(negocio=negocio, **ser.validated_data)
    return Response(ProductoSerializer(producto).data, status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsNegocio])
def producto_detalle(request, producto_id):
    if request.method == "DELETE":
        try:
            ProductoService.desactivar_producto(producto_id, request.user)
        except DomainException as e:
            return Response({"error": e.codigo, "detail": str(e)}, status=403)
        return Response(status=204)

    ser = ProductoWriteSerializer(data=request.data, partial=True)
    ser.is_valid(raise_exception=True)
    try:
        producto = ProductoService.actualizar_producto(
            producto_id, request.user, **ser.validated_data
        )
    except DomainException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=403)
    return Response(ProductoSerializer(producto).data)
