from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.delivery.api.serializers import UbicacionSerializer
from apps.delivery.application.services import SeguimientoEntregaService
from apps.shared.domain.exceptions import DomainException, PermisoDominioException


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def actualizar_ubicacion(request, repartidor_id):
    serializer = UbicacionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        seg = SeguimientoEntregaService.actualizar_ubicacion(
            usuario=request.user,
            repartidor_id=repartidor_id,
            latitud=serializer.validated_data["latitud"],
            longitud=serializer.validated_data["longitud"],
        )
    except PermisoDominioException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=403)
    except DomainException as e:
        return Response({"error": e.codigo, "detail": str(e)}, status=400)
    return Response(
        {"ok": True, "pedido_id": seg.pedido_id, "timestamp": seg.timestamp.isoformat()},
        status=201,
    )