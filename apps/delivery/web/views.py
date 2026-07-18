from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from apps.delivery.application.services import RepartidorService
from apps.orders.application.services import PedidoService
from apps.shared.domain.exceptions import DomainException
from apps.shared.roles import rol_requerido


def _repartidor_del_usuario(user):
    return RepartidorService.obtener_repartidor_de_usuario(user)


@rol_requerido("REPARTIDOR")
def estado_pedido_activo(request):
    """
    Devuelve en JSON el pedido activo del repartidor autenticado (id y estado),
    o null si no tiene ninguno. Lo consume el panel para detectar asignaciones
    o cambios de estado sin recargar la página a mano.

    Seguridad: el alcance se resuelve SIEMPRE en backend a partir del usuario
    autenticado (nunca por un id que venga del cliente), así que jamás expone
    pedidos de otros repartidores. `rol_requerido` bloquea a quien no sea
    repartidor autenticado.
    """
    repartidor = _repartidor_del_usuario(request.user)
    pedido = (
        RepartidorService.obtener_pedido_activo(repartidor)
        if repartidor is not None
        else None
    )
    return JsonResponse({
        "pedido_id": pedido.id if pedido else None,
        "estado": pedido.estado if pedido else None,
    })


@rol_requerido("REPARTIDOR")
def mi_pedido(request):
    repartidor = _repartidor_del_usuario(request.user)
    if repartidor is None:
        return render(request, "delivery/sin_repartidor.html")

    pedido = RepartidorService.obtener_pedido_activo(repartidor)
    return render(
        request,
        "delivery/mi_pedido.html",
        {"repartidor": repartidor, "pedido": pedido},
    )


@rol_requerido("REPARTIDOR")
def toggle_disponibilidad(request):
    if request.method == "POST":
        repartidor = _repartidor_del_usuario(request.user)
        if repartidor is not None:
            RepartidorService.actualizar_disponibilidad(
                repartidor.id, not repartidor.disponible
            )
    return redirect("mi_pedido")


@rol_requerido("REPARTIDOR")
def marcar_recogido(request):
    """Marca el pedido activo como EN_CAMINO."""
    if request.method == "POST":
        _accion_pedido_activo(request, PedidoService.marcar_en_camino)
    return redirect("mi_pedido")


@rol_requerido("REPARTIDOR")
def marcar_entregado(request):
    """Marca el pedido activo como ENTREGADO."""
    if request.method == "POST":
        _accion_pedido_activo(request, PedidoService.marcar_entregado)
    return redirect("mi_pedido")


def _accion_pedido_activo(request, metodo):
    """Resuelve el pedido activo del repartidor y ejecuta la acción."""
    repartidor = _repartidor_del_usuario(request.user)
    if repartidor is None:
        return
    pedido = RepartidorService.obtener_pedido_activo(repartidor)
    if pedido is None:
        messages.warning(request, "No tienes un pedido activo.")
        return
    try:
        metodo(pedido.id, request.user)
        messages.success(request, "Pedido actualizado.")
    except DomainException as e:
        messages.error(request, str(e))
