from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from apps.accounts.application.services import AccountService
from apps.accounts.models import User
from apps.accounts.web.forms import (
    ClienteDatosForm, DatosPersonalesForm, NegocioPerfilForm, RegistroClienteForm,
    RegistroNegocioForm, RegistroRepartidorForm, RepartidorPerfilForm,
)

# Mapea cada rol con el método de registro correspondiente del servicio.
_REGISTRADORES = {
    User.Rol.CLIENTE: AccountService.registrar_cliente,
    User.Rol.NEGOCIO: AccountService.registrar_negocio,
    User.Rol.REPARTIDOR: AccountService.registrar_repartidor,
}
_FORMULARIOS = {
    User.Rol.CLIENTE: RegistroClienteForm,
    User.Rol.NEGOCIO: RegistroNegocioForm,
    User.Rol.REPARTIDOR: RegistroRepartidorForm,
}


def _registrar(request, rol):
    """Vista genérica de registro; el rol lo decide la URL."""
    if request.method == "POST":
        form = _FORMULARIOS[rol](request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            data["password"] = data.pop("password1")
            data.pop("password2")
            user = _REGISTRADORES[rol](**data)
            if user.aprobado:
                login(request, user)
                messages.success(request, "¡Registro exitoso! Bienvenido.")
                return redirect("home")
            messages.info(
                request,
                "Registro recibido. Tu cuenta quedó pendiente de aprobación "
                "por el administrador.",
            )
            return redirect("login")
    else:
        form = _FORMULARIOS[rol]()

    return render(
        request,
        "accounts/registro.html",
        {"form": form, "rol": User.Rol(rol).label},
    )


def registro_cliente(request):
    return _registrar(request, User.Rol.CLIENTE)


def registro_negocio(request):
    return _registrar(request, User.Rol.NEGOCIO)


def registro_repartidor(request):
    return _registrar(request, User.Rol.REPARTIDOR)


@login_required
def editar_perfil(request):
    if request.user.es_negocio:
        perfil, form_class = request.user.negocio, NegocioPerfilForm
    elif request.user.es_repartidor:
        perfil, form_class = request.user.repartidor, RepartidorPerfilForm
    else:
        perfil, form_class = None, None

    # El cliente edita, además de sus datos, su dirección de entrega guardada.
    datos_form_class = ClienteDatosForm if request.user.es_cliente else DatosPersonalesForm
    datos_form = datos_form_class(request.POST or None, instance=request.user)
    perfil_form = (
        form_class(request.POST or None, instance=perfil) if form_class else None
    )
    formularios_validos = datos_form.is_valid() and (
        perfil_form is None or perfil_form.is_valid()
    )
    if request.method == "POST" and formularios_validos:
        perfil_data = perfil_form.cleaned_data if perfil_form else {}
        AccountService.actualizar_perfil(
            request.user, **datos_form.cleaned_data, **perfil_data
        )
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("editar_perfil")
    return render(request, "accounts/editar_perfil.html", {
        "datos_form": datos_form,
        "perfil_form": perfil_form,
    })


class LoginConRedireccionView(LoginView):
    """
    Login estándar que, tras autenticar, envía a los administradores
    directamente al panel de control (panel/admin/). El resto de usuarios
    sigue el flujo normal (parámetro ``next`` o LOGIN_REDIRECT_URL).
    """

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        # Respeta el ``next`` explícito (get_redirect_url); solo cambia el
        # destino por defecto cuando el usuario es administrador.
        if self.request.user.es_admin:
            return reverse_lazy("admin_dashboard")
        return super().get_default_redirect_url()
