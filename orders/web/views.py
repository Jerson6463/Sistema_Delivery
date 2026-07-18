from django.contrib import messages
from django.shortcuts import redirect, render

from apps.businesses.application.services import NegocioService
from apps.orders.application.services import CalificacionService, PedidoService
from apps.orders.domain.states import Estado, es_estado_final
from apps.orders.models import Pedido
from apps.shared.domain.exceptions import DomainException
from apps.shared.roles import rol_requerido


@rol_requerido("CLIENTE")
def agregar_al_carrito(request, producto_id):
    if request.method == "POST":
        try:
            producto = PedidoService.agregar_al_carrito(request.session, producto_id)
        except DomainException as e:
            messages.error(request, str(e))
            return redirect("lista_negocios")
        messages.success(request, f"'{producto.nombre}' agregado al carrito.")
        return redirect("detalle_negocio", negocio_id=producto.negocio_id)
    return redirect("lista_negocios")


@rol_requerido("CLIENTE")
def ver_carrito(request):
    resumen = PedidoService.resumen_carrito(request.session)
    return render(
        request,
        "orders/carrito.html",
        {
            "carrito": resumen,
            "lineas": resumen["lineas"],
            "subtotal": resumen["subtotal"],
            "zonas": resumen["zonas"],
            "metodos_pago": Pedido.MetodoPago.choices,
            "direccion_cliente": request.user.direccion,
        },
    )


@rol_requerido("CLIENTE")
def actualizar_carrito(request, producto_id):
    if request.method == "POST":
        cantidad = int(request.POST.get("cantidad", 0))
        PedidoService.actualizar_carrito(request.session, producto_id, cantidad)
    return redirect("ver_carrito")


@rol_requerido("CLIENTE")
def remover_del_carrito(request, producto_id):
    if request.method == "POST":
        PedidoService.remover_del_carrito(request.session, producto_id)
    return redirect("ver_carrito")


@rol_requerido("CLIENTE")
def confirmar_pedido(request):
    if request.method != "POST":
        return redirect("ver_carrito")

    direccion_entrega = (
        request.POST.get("direccion_entrega", "").strip() or request.user.direccion
    )

    try:
        pedido = PedidoService.crear_pedido_desde_carrito(
            cliente=request.user,
            session=request.session,
            direccion_entrega=direccion_entrega,
            zona_entrega_id=int(request.POST.get("zona_entrega_id")),
            metodo_pago=request.POST.get("metodo_pago"),
        )
    except DomainException as e:
        messages.error(request, str(e))
        return redirect("ver_carrito")

    messages.success(request, f"¡Pedido #{pedido.id} creado con éxito!")
    return redirect("mis_pedidos")


@rol_requerido("CLIENTE")
def mis_pedidos(request):
    pedidos = PedidoService.listar_mis_pedidos(request.user)
    return render(request, "orders/mis_pedidos.html", {"pedidos": pedidos})


_ACCIONES_NEGOCIO = {
    "confirmar": PedidoService.confirmar_pedido,
    "preparar": PedidoService.marcar_en_preparacion,
    "listo": PedidoService.marcar_listo_para_recojo,
}


def _negocio_del_usuario(user):
    return NegocioService.obtener_negocio_de_usuario(user)


@rol_requerido("NEGOCIO")
def panel_negocio_pedidos(request):
    negocio = _negocio_del_usuario(request.user)
    if negocio is None:
        return render(request, "catalog/sin_negocio.html")

    pedidos = PedidoService.listar_pedidos_negocio(negocio, solo_activos=True)
    contexto = {"negocio": negocio, "pedidos": pedidos, "Estado": Estado}
    # Petición del panel en vivo: devuelve solo la lista ya renderizada para
    # refrescar la sección sin recargar toda la página.
    if request.headers.get("X-Requested-With") == "fetch":
        return render(request, "orders/_lista_pedidos.html", contexto)
    return render(request, "orders/panel_negocio.html", contexto)


@rol_requerido("NEGOCIO")
def accion_negocio(request, pedido_id, accion):
    if request.method != "POST":
        return redirect("panel_negocio_pedidos")

    if accion == "rechazar":
        motivo = request.POST.get("motivo", "").strip() or "Rechazado por el negocio"
        _ejecutar(request, PedidoService.rechazar_pedido, pedido_id, request.user, motivo)
    elif accion in _ACCIONES_NEGOCIO:
        _ejecutar(request, _ACCIONES_NEGOCIO[accion], pedido_id, request.user)
    else:
        messages.error(request, "Acción no válida.")

    return redirect("panel_negocio_pedidos")


@rol_requerido("CLIENTE")
def cancelar_pedido_cliente(request, pedido_id):
    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        _ejecutar(request, PedidoService.cancelar_pedido, pedido_id, request.user, motivo)
    return redirect("mis_pedidos")


@rol_requerido("CLIENTE")
def calificar_pedido(request, pedido_id):
    if request.method != "POST":
        return redirect("mis_pedidos")

    def _puntaje(nombre):
        valor = request.POST.get(nombre)
        try:
            return int(valor) if valor else None
        except (TypeError, ValueError):
            return None

    try:
        CalificacionService.calificar_pedido(
            request.user,
            pedido_id,
            puntaje_negocio=_puntaje("puntaje_negocio"),
            puntaje_repartidor=_puntaje("puntaje_repartidor"),
            comentario_negocio=request.POST.get("comentario_negocio", ""),
            comentario_repartidor=request.POST.get("comentario_repartidor", ""),
        )
        messages.success(request, "¡Gracias por tu calificación!")
    except Pedido.DoesNotExist:
        raise Http404("Pedido no encontrado")
    except DomainException as e:
        messages.error(request, str(e))
    return redirect("mis_pedidos")


def _ejecutar(request, metodo, *args):
    try:
        metodo(*args)
        messages.success(request, "Pedido actualizado.")
    except DomainException as e:
        messages.error(request, str(e))


from django.contrib.auth.decorators import login_required  # noqa: E402
from django.http import Http404  # noqa: E402
from apps.shared.domain.exceptions import PermisoDominioException  # noqa: E402


@login_required
def tracking_pedido(request, pedido_id):
    try:
        data = PedidoService.obtener_tracking(pedido_id, request.user)
    except Pedido.DoesNotExist:
        raise Http404("Pedido no encontrado")
    except PermisoDominioException:
        messages.error(request, "No tienes acceso a ese pedido.")
        return redirect("mis_pedidos")

    es_cliente = getattr(request.user, "es_cliente", False)
    if es_cliente and es_estado_final(data["estado_actual"]):
        return redirect("mis_pedidos")

    return render(
        request,
        "orders/tracking.html",
        {"data": data, "pedido_id": pedido_id, "es_cliente": es_cliente},
    )
