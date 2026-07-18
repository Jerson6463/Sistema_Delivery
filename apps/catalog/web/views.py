from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.businesses.application.services import NegocioService
from apps.catalog.application.services import (
    CategoriaProductoService,
    ProductoService,
)
from apps.catalog.models import Producto
from apps.catalog.web.forms import ProductoForm
from apps.shared.roles import rol_requerido


def _negocio_del_usuario(user):
    """Devuelve el Negocio del usuario logueado, o None si aún no está creado."""
    return NegocioService.obtener_negocio_de_usuario(user)


@rol_requerido("NEGOCIO")
def panel_productos(request):
    negocio = _negocio_del_usuario(request.user)
    if negocio is None:
        return render(request, "catalog/sin_negocio.html")

    productos = ProductoService.listar_por_negocio(negocio.id, solo_activos=False)
    return render(
        request,
        "catalog/panel_productos.html",
        {"negocio": negocio, "productos": productos},
    )


@rol_requerido("NEGOCIO")
def crear_producto(request):
    negocio = _negocio_del_usuario(request.user)
    if negocio is None:
        return render(request, "catalog/sin_negocio.html")

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            ProductoService.crear_producto(negocio=negocio, **form.cleaned_data)
            messages.success(request, "Producto creado.")
            return redirect("panel_productos")
    else:
        form = ProductoForm()
    return render(
        request,
        "catalog/form_producto.html",
        {
            "form": form,
            "modo": "Crear",
            "categorias": CategoriaProductoService.listar_nombres(negocio.id),
        },
    )


@rol_requerido("NEGOCIO")
def editar_producto(request, producto_id):
    # La propiedad se valida en el servicio; aquí solo cargamos el objeto.
    # `activo=True`: un producto desactivado no se puede editar por URL directa;
    # primero hay que reactivarlo desde el panel.
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            ProductoService.actualizar_producto(
                producto.id, request.user, **form.cleaned_data
            )
            messages.success(request, "Producto actualizado.")
            return redirect("panel_productos")
    else:
        form = ProductoForm(instance=producto)
    return render(
        request,
        "catalog/form_producto.html",
        {
            "form": form,
            "modo": "Editar",
            "categorias": CategoriaProductoService.listar_nombres(producto.negocio_id),
        },
    )


@rol_requerido("NEGOCIO")
def desactivar_producto(request, producto_id):
    if request.method == "POST":
        ProductoService.desactivar_producto(producto_id, request.user)
        messages.info(request, "Producto desactivado.")
    return redirect("panel_productos")


@rol_requerido("NEGOCIO")
def activar_producto(request, producto_id):
    if request.method == "POST":
        ProductoService.activar_producto(producto_id, request.user)
        messages.success(request, "Producto activado.")
    return redirect("panel_productos")
