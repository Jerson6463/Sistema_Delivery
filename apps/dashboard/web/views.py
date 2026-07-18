from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.businesses.application.services import (
    DistritoService,
    TarifaEnvioService,
    ZonaService,
)
from apps.businesses.models import Negocio
from apps.dashboard.application.services import AdminPanelService
from apps.dashboard.web.forms import DistritoForm, TarifaEnvioForm, ZonaForm
from apps.shared.domain.exceptions import DomainException
from apps.shared.roles import rol_requerido


@rol_requerido("ADMIN")
def dashboard(request):
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "m": AdminPanelService.metricas(),
            "negocios_pendientes": AdminPanelService.negocios_pendientes(),
            "repartidores_pendientes": AdminPanelService.repartidores_pendientes(),
            "pedidos_dia": AdminPanelService.pedidos_del_dia(),
            "negocios_activos": AdminPanelService.negocios_activos(),
            "repartidores_disponibles": AdminPanelService.repartidores_disponibles(),
        },
    )


def _ejecutar(request, metodo, *args):
    try:
        metodo(*args)
        messages.success(request, "Acción realizada.")
    except DomainException as e:
        messages.error(request, str(e))


@rol_requerido("ADMIN")
def aprobar_negocio(request, negocio_id):
    if request.method == "POST":
        _ejecutar(request, AdminPanelService.aprobar_negocio, negocio_id, request.user)
    return redirect("admin_dashboard")


@rol_requerido("ADMIN")
def rechazar_negocio(request, negocio_id):
    if request.method == "POST":
        _ejecutar(request, AdminPanelService.rechazar_negocio, negocio_id, request.user)
    return redirect("admin_dashboard")


@rol_requerido("ADMIN")
def configurar_tarifas(request, negocio_id):
    """
    Configura las tarifas de envío por zona de un negocio antes de activarlo.
    Solo accesible por administradores.
    """
    negocio = get_object_or_404(Negocio, pk=negocio_id)

    if request.method == "POST":
        # Edición en línea del precio de una tarifa existente: se identifica
        # por `tarifa_id` y NO pasa por TarifaEnvioForm (cuyo catálogo de
        # distritos restringido podría rechazar la fila y descartar el cambio
        # en silencio). Solo valida y guarda el monto.
        tarifa_id = request.POST.get("tarifa_id")
        if tarifa_id:
            try:
                TarifaEnvioService.actualizar_costo(
                    request.user,
                    negocio.id,
                    tarifa_id,
                    request.POST.get("costo"),
                )
                messages.success(request, "Precio actualizado.")
            except DomainException as e:
                messages.error(request, str(e))
            return redirect("configurar_tarifas", negocio_id=negocio.id)

        form = TarifaEnvioForm(request.POST, negocio=negocio)
        if form.is_valid():
            zona = form.cleaned_data["zona"]
            try:
                TarifaEnvioService.guardar_tarifa(
                    request.user,
                    negocio.id,
                    costo=form.cleaned_data["costo"],
                    zona_id=zona.id,
                )
                messages.success(request, "Tarifa de envío guardada.")
                return redirect("configurar_tarifas", negocio_id=negocio.id)
            except DomainException as e:
                messages.error(request, str(e))
    else:
        form = TarifaEnvioForm(negocio=negocio)

    tarifas = TarifaEnvioService.listar_por_negocio(negocio.id)
    return render(
        request,
        "dashboard/tarifas_negocio.html",
        {"negocio": negocio, "tarifas": tarifas, "form": form},
    )


@rol_requerido("ADMIN")
def eliminar_tarifa(request, negocio_id, tarifa_id):
    if request.method == "POST":
        try:
            TarifaEnvioService.eliminar_tarifa(request.user, tarifa_id)
            messages.info(request, "Tarifa eliminada.")
        except DomainException as e:
            messages.error(request, str(e))
    return redirect("configurar_tarifas", negocio_id=negocio_id)


# =========================================================
# Zonas y distritos
# =========================================================
@rol_requerido("ADMIN")
def gestionar_zonas(request):
    """Listado y formularios de alta para zonas y distritos."""
    return render(
        request,
        "dashboard/zonas_distritos.html",
        {
            "zonas": ZonaService.listar(),
            "distritos": DistritoService.listar(),
            "form_zona": ZonaForm(),
            "form_distrito": DistritoForm(),
        },
    )


@rol_requerido("ADMIN")
def crear_zona(request):
    if request.method == "POST":
        form = ZonaForm(request.POST)
        if form.is_valid():
            try:
                ZonaService.crear(request.user, form.cleaned_data["nombre"])
                messages.success(request, "Zona creada correctamente.")
            except DomainException as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Revisa los datos de la zona.")
    return redirect("gestionar_zonas")


@rol_requerido("ADMIN")
def editar_zona(request, zona_id):
    if request.method == "POST":
        _ejecutar_msg(
            request,
            ZonaService.actualizar,
            "Zona actualizada.",
            request.user,
            zona_id,
            request.POST.get("nombre", ""),
        )
    return redirect("gestionar_zonas")


@rol_requerido("ADMIN")
def eliminar_zona(request, zona_id):
    if request.method == "POST":
        _ejecutar_msg(
            request, ZonaService.eliminar, "Zona eliminada.",
            request.user, zona_id,
        )
    return redirect("gestionar_zonas")


@rol_requerido("ADMIN")
def crear_distrito(request):
    if request.method == "POST":
        form = DistritoForm(request.POST)
        if form.is_valid():
            try:
                DistritoService.crear(
                    request.user,
                    form.cleaned_data["zona"].id,
                    form.cleaned_data["distrito"],
                )
                messages.success(request, "Distrito creado correctamente.")
            except DomainException as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Revisa los datos del distrito.")
    return redirect("gestionar_zonas")


@rol_requerido("ADMIN")
def editar_distrito(request, distrito_id):
    if request.method == "POST":
        _ejecutar_msg(
            request,
            DistritoService.actualizar,
            "Distrito actualizado.",
            request.user,
            distrito_id,
            request.POST.get("zona"),
            request.POST.get("distrito", ""),
        )
    return redirect("gestionar_zonas")


@rol_requerido("ADMIN")
def eliminar_distrito(request, distrito_id):
    if request.method == "POST":
        _ejecutar_msg(
            request, DistritoService.eliminar, "Distrito eliminado.",
            request.user, distrito_id,
        )
    return redirect("gestionar_zonas")


def _ejecutar_msg(request, metodo, exito, *args):
    """Ejecuta una acción de servicio y traduce el resultado a un message."""
    try:
        metodo(*args)
        messages.success(request, exito)
    except DomainException as e:
        messages.error(request, str(e))


@rol_requerido("ADMIN")
def aprobar_repartidor(request, repartidor_id):
    if request.method == "POST":
        _ejecutar(request, AdminPanelService.aprobar_repartidor, repartidor_id, request.user)
    return redirect("admin_dashboard")


@rol_requerido("ADMIN")
def rechazar_repartidor(request, repartidor_id):
    if request.method == "POST":
        _ejecutar(request, AdminPanelService.rechazar_repartidor, repartidor_id, request.user)
    return redirect("admin_dashboard")