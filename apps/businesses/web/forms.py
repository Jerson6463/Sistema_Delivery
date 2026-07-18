from datetime import time

from django import forms

from apps.businesses.domain.horario import DIAS
from apps.businesses.models import Negocio

# Etiquetas legibles (con tildes) para cada clave de día del horario_json.
ETIQUETAS_DIAS = {
    "lunes": "Lunes",
    "martes": "Martes",
    "miercoles": "Miércoles",
    "jueves": "Jueves",
    "viernes": "Viernes",
    "sabado": "Sábado",
    "domingo": "Domingo",
}


class ConfiguracionNegocioForm(forms.Form):
    hora_apertura = forms.TimeField(
        label="Hora de apertura",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}, format="%H:%M"),
    )
    hora_cierre = forms.TimeField(
        label="Hora de cierre",
        help_text="Si el cierre es menor que la apertura (p. ej. 18:00 a 02:00), "
                  "se interpreta como madrugada del día siguiente.",
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"}, format="%H:%M"),
    )
    dias_atencion = forms.MultipleChoiceField(
        label="Días de atención",
        choices=[(dia, ETIQUETAS_DIAS[dia]) for dia in DIAS],
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": "Selecciona al menos un día de atención."},
    )
    imagen = forms.ImageField(
        label="Imagen del local",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        apertura = cleaned_data.get("hora_apertura")
        cierre = cleaned_data.get("hora_cierre")
        # Se permite cierre < apertura (horario nocturno que cruza medianoche);
        # solo la igualdad es inválida (ventana de duración cero / ambigua).
        if apertura and cierre and apertura == cierre:
            self.add_error(
                "hora_cierre",
                "La hora de apertura y de cierre no pueden ser iguales.",
            )
        return cleaned_data

    @classmethod
    def initial_from_negocio(cls, negocio: Negocio):
        horario = negocio.horario_json or {}
        dias = [dia for dia in DIAS if horario.get(dia, {}).get("abierto")]
        primer_dia = horario.get(dias[0], {}) if dias else {}
        return {
            "hora_apertura": primer_dia.get("inicio") or time(8, 0),
            "hora_cierre": primer_dia.get("fin") or time(22, 0),
            "dias_atencion": dias,
        }
