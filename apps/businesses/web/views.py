from django.contrib import messages
from django.shortcuts import redirect, render

from apps.businesses.application.services import NegocioService
from apps.businesses.domain.horario import DIAS
from apps.businesses.models import Negocio
from apps.businesses.web.forms import ETIQUETAS_DIAS, ConfiguracionNegocioForm
from apps.shared.domain.exceptions import DomainException
from apps.shared.roles import rol_requerido


def _es_negocio(user):
    return user.is_authenticated and getattr(user, "es_negocio", False)


def _ir_a_su_negocio(user):
    """
    Destino de un usuario NEGOCIO: la vista de su propio negocio
    (detalle_negocio, con la distribución de sus productos). Si aún no tiene
    ficha, va al panel de productos (que muestra el aviso correspondiente).
    """
    negocio = NegocioService.obtener_negocio_de_usuario(user)
    if negocio is None:
        return redirect("panel_productos")
    return redirect("detalle_negocio", negocio_id=negocio.id)


def home(request):
    """
    Landing tras el login. Un negocio no ve el catálogo general: entra directo
    a la vista de su negocio. Los demás roles ven la página de inicio normal.
    """
    if _es_negocio(request.user):
        return _ir_a_su_negocio(request.user)
    return render(request, "base.html")


def lista_negocios(request):
    # Los negocios no pueden ver la lista de negocios disponibles: se les
    # redirige a la vista de su propio negocio.
    if _es_negocio(request.user):
        return _ir_a_su_negocio(request.user)

    categoria = request.GET.get("categoria") or None
    solo_abiertos = request.GET.get("disponible") == "true"

    contexto_base = {
        "categorias": Negocio.Categoria.choices,
        "categoria_actual": categoria,
        "solo_abiertos": solo_abiertos,
    }

    zona_cliente = None
    if request.user.is_authenticated and request.user.es_cliente:
        if request.user.zona_entrega_id is None:
            return render(
                request,
                "businesses/lista_negocios.html",
                {**contexto_base, "items": [], "sin_distrito": True},
            )
        zona_cliente = request.user.zona_general

    negocios = NegocioService.listar_negocios_disponibles(
        categoria=categoria, solo_abiertos=solo_abiertos, zona=zona_cliente
    )
    items = [
        {"negocio": negocio, "estado": NegocioService.calcular_estado(negocio)}
        for negocio in negocios
    ]

    return render(
        request,
        "businesses/lista_negocios.html",
        {**contexto_base, "items": items, "zona_cliente": zona_cliente},
    )


def detalle_negocio(request, negocio_id):
    # El dueño puede ver su propio escaparate aunque esté cerrado (es su vista
    # al iniciar sesión); al público se le sigue exigiendo que esté abierto.
    es_dueno = _es_negocio(request.user) and Negocio.objects.filter(
        pk=negocio_id, usuario_dueno=request.user
    ).exists()
    try:
        detalle = NegocioService.obtener_detalle_publico(
            negocio_id, exigir_abierto=not es_dueno
        )
    except (Negocio.DoesNotExist, DomainException):
        # Para el dueño se evita rebotar a lista_negocios (que lo devolvería
        # aquí): se le manda a su panel de productos.
        if es_dueno:
            return redirect("panel_productos")
        messages.warning(
            request,
            "Este negocio se encuentra cerrado. "
            "No puedes realizar pedidos en este momento.",
        )
        return redirect("lista_negocios")

    negocio = detalle["negocio"]
    return render(
        request,
        "businesses/detalle_negocio.html",
        {
            "negocio": negocio,
            "estado": NegocioService.calcular_estado(negocio),
            "productos": detalle["productos"],
        },
    )


@rol_requerido("NEGOCIO")
def configuracion_negocio(request):
    negocio = NegocioService.obtener_negocio_de_usuario(request.user)
    if negocio is None:
        return render(request, "catalog/sin_negocio.html")

    if request.method == "POST":
        form = ConfiguracionNegocioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                NegocioService.actualizar_configuracion(
                    negocio.id,
                    request.user,
                    hora_apertura=form.cleaned_data["hora_apertura"],
                    hora_cierre=form.cleaned_data["hora_cierre"],
                    dias_atencion=form.cleaned_data["dias_atencion"],
                    imagen=form.cleaned_data.get("imagen"),
                )
                messages.success(request, "Horario actualizado correctamente.")
                return redirect("configuracion_negocio")
            except DomainException as e:
                messages.error(request, str(e))
    else:
        form = ConfiguracionNegocioForm(
            initial=ConfiguracionNegocioForm.initial_from_negocio(negocio)
        )

    horario = negocio.horario_json or {}
    dias_actuales = [
        ETIQUETAS_DIAS[dia]
        for dia in DIAS
        if horario.get(dia, {}).get("abierto")
    ]
    return render(
        request,
        "businesses/configuracion_negocio.html",
        {"negocio": negocio, "form": form, "dias_actuales": dias_actuales},
    )
