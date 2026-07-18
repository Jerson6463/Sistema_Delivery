from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.businesses.api.serializers import NegocioSerializer
from apps.businesses.application.services import NegocioService
from apps.businesses.models import Negocio
from apps.catalog.api.serializers import ProductoSerializer
from apps.catalog.application.services import ProductoService


@api_view(["GET"])
@permission_classes([AllowAny])
def listar_negocios(request):
    categoria = request.query_params.get("categoria") or None
    solo_abiertos = request.query_params.get("disponible") == "true"
    zona = None
    if request.user.is_authenticated and request.user.es_cliente:
        if request.user.zona_entrega_id is None:
            return Response({"error": "SIN_DISTRITO", "negocios": []}, status=409)
        zona = request.user.zona_general
    negocios = NegocioService.listar_negocios_disponibles(
        categoria, solo_abiertos, zona=zona
    )
    return Response(NegocioSerializer(negocios, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def detalle_negocio(request, negocio_id):
    try:
        detalle = NegocioService.obtener_detalle_publico(negocio_id)
    except Negocio.DoesNotExist:
        return Response({"error": "NO_ENCONTRADO"}, status=404)
    data = NegocioSerializer(detalle["negocio"]).data
    data["productos"] = ProductoSerializer(detalle["productos"], many=True).data
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def productos_negocio(request, negocio_id):
    productos = ProductoService.listar_por_negocio(negocio_id, solo_activos=True)
    return Response(ProductoSerializer(productos, many=True).data)
