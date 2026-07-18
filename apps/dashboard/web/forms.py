from django import forms

from apps.businesses.models import Zona, ZonaEntrega


class ZonaForm(forms.Form):
    """Alta/edición del nombre de una zona general."""
    nombre = forms.CharField(
        label="Nombre de la zona",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ej. Centro"}
        ),
    )


class DistritoForm(forms.Form):
    """
    Alta/edición de un distrito y su asociación con una zona.

    El select de zona se limita a las zonas activas: no se puede colgar un
    distrito de una zona eliminada.
    """
    zona = forms.ModelChoiceField(
        queryset=Zona.objects.all().order_by("nombre"),
        label="Zona",
        empty_label="— Selecciona una zona —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    distrito = forms.CharField(
        label="Nombre del distrito",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ej. Miraflores"}
        ),
    )


class TarifaEnvioForm(forms.Form):
    """
    Alta/edición de una tarifa de envío por distrito desde el panel de admin.

    El distrito se elige de un catálogo restringido a la zona general del
    negocio: solo se ofrecen los distritos que pertenecen a la misma zona en
    la que se ubica el negocio. El costo se valida no-negativo.
    """
    zona = forms.ModelChoiceField(
        queryset=ZonaEntrega.objects.none(),
        required=True,
        label="Distrito existente",
        empty_label="— Selecciona un distrito —",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    costo = forms.DecimalField(
        label="Costo de envío (S/)",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01", "min": "0"}
        ),
    )

    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)
        distritos = ZonaEntrega.objects.filter(activo=True)
        # `Negocio.zona` es un distrito (ZonaEntrega); su zona general es
        # `negocio.zona.zona`. Solo se ofrecen los distritos de esa misma zona.
        if negocio is not None and negocio.zona_id:
            distritos = distritos.filter(zona=negocio.zona.zona_id)
        else:
            distritos = distritos.none()
        self.fields["zona"].queryset = distritos.order_by("distrito")
