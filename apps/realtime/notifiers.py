"""
Notificador central de WebSocket.

Regla de oro: NADIE emite eventos directamente desde una vista. Los
servicios llaman a estas funciones DESPUÉS de persistir (con
transaction.on_commit), para que el cliente nunca reciba un evento de
algo que aún no está en la base de datos.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _send(group: str, data: dict):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(group, {"type": "broadcast", "data": data})


def notificar_pedido_creado(pedido):
    """Nuevo pedido -> panel del negocio y métricas del admin."""
    _send(f"negocio_{pedido.negocio_id}", {
        "type": "pedido_creado",
        "pedido_id": pedido.id,
        "estado": pedido.estado,
        "total": str(pedido.total),
    })
    _send("admin_dashboard", {"type": "metricas_actualizadas"})


def notificar_estado(pedido):
    """Cambio de estado -> tracking del cliente y panel del negocio."""
    data = {
        "type": "pedido_estado_actualizado",
        "pedido_id": pedido.id,
        "estado": pedido.estado,
        "estado_display": pedido.get_estado_display(),
    }
    _send(f"pedido_{pedido.id}", data)
    _send(f"negocio_{pedido.negocio_id}", data)
    _send("admin_dashboard", {"type": "metricas_actualizadas"})


def notificar_asignacion(pedido):
    """Asignación -> repartidor."""
    if pedido.repartidor_id:
        _send(f"repartidor_{pedido.repartidor_id}", {
            "type": "pedido_asignado",
            "pedido_id": pedido.id,
            "estado": pedido.estado,
        })


def notificar_ubicacion(pedido, latitud, longitud):
    """Nueva ubicación GPS -> tracking del cliente."""
    _send(f"pedido_{pedido.id}", {
        "type": "ubicacion_actualizada",
        "pedido_id": pedido.id,
        "latitud": float(latitud),
        "longitud": float(longitud),
    })