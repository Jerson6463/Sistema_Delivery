from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.businesses.models import Negocio, Zona, ZonaEntrega
from apps.delivery.models import Repartidor


class RegistroUsuarioForm(UserCreationForm):
    """
    Valida username, email y contraseña (con los validadores de Django).
    El ROL no se pide en el formulario: lo fija la vista según la URL,
    y el usuario se crea a través de AccountService, no con form.save().
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, label="Nombres", required=True)
    last_name = forms.CharField(max_length=150, label="Apellidos", required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")


class RegistroClienteForm(RegistroUsuarioForm):
    """Registro de cliente: pide además la dirección y el distrito de entrega."""
    direccion = forms.CharField(
        max_length=255, label="Dirección de entrega", required=True
    )
    zona_entrega = forms.ModelChoiceField(
        queryset=ZonaEntrega.objects.none(),
        label="Distrito",
        empty_label="Selecciona tu distrito...",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo distritos activos; el select muestra solo el distrito (ver
        # ZonaEntrega.__str__), no la zona general.
        self.fields["zona_entrega"].queryset = ZonaEntrega.objects.filter(
            activo=True
        ).order_by("distrito")


class DatosPersonalesForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, label="Nombres", required=True)
    last_name = forms.CharField(max_length=150, label="Apellidos", required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name")


class ClienteDatosForm(DatosPersonalesForm):
    """Datos personales del cliente + su dirección y distrito guardados."""
    direccion = forms.CharField(
        max_length=255, label="Dirección de entrega", required=True
    )
    zona_entrega = forms.ModelChoiceField(
        queryset=ZonaEntrega.objects.none(),
        label="Distrito",
        empty_label="Selecciona tu distrito...",
    )

    class Meta(DatosPersonalesForm.Meta):
        fields = ("first_name", "last_name", "direccion", "zona_entrega")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zona_entrega"].queryset = ZonaEntrega.objects.filter(
            activo=True
        ).order_by("distrito")


class RegistroNegocioForm(RegistroUsuarioForm):
    nombre = forms.CharField(max_length=150, label="Nombre del negocio")
    categoria = forms.ChoiceField(choices=Negocio.Categoria.choices)
    direccion = forms.CharField(max_length=255, label="Dirección del negocio")
    zona = forms.ModelChoiceField(
        queryset=ZonaEntrega.objects.none(), label="Distrito de la dirección"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zona"].queryset = ZonaEntrega.objects.filter(
            activo=True
        ).order_by("zona__nombre", "distrito")


class RegistroRepartidorForm(RegistroUsuarioForm):
    vehiculo = forms.ChoiceField(
        choices=Repartidor.Vehiculo.choices, label="Tipo de vehículo"
    )
    zona_cobertura = forms.ModelChoiceField(
        queryset=Zona.objects.none(), label="Zona de reparto"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zona_cobertura"].queryset = Zona.objects.filter(
            activo=True
        ).order_by("nombre")


class NegocioPerfilForm(forms.ModelForm):
    class Meta:
        model = Negocio
        fields = ("nombre", "categoria", "direccion", "zona")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zona"].label = "Distrito"
        self.fields["zona"].required = True
        self.fields["zona"].queryset = ZonaEntrega.objects.filter(
            activo=True
        ).order_by("zona__nombre", "distrito")


class RepartidorPerfilForm(forms.ModelForm):
    class Meta:
        model = Repartidor
        fields = ("vehiculo", "zona_cobertura")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zona_cobertura"].label = "Zona de reparto"
        self.fields["zona_cobertura"].queryset = Zona.objects.filter(
            activo=True
        ).order_by("nombre")


class LoginConAprobacionForm(AuthenticationForm):
    """Bloquea el login de negocios/repartidores aún no aprobados."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)  # valida is_active
        if not user.aprobado:
            raise ValidationError(
                "Tu cuenta está pendiente de aprobación por el administrador.",
                code="pendiente",
            )
