from django import forms

from apps.catalog.models import Producto


class ProductoForm(forms.ModelForm):
    """El negocio no se elige en el formulario: se toma del usuario logueado."""

    class Meta:
        model = Producto
        fields = ("nombre", "precio", "categoria", "stock_disponible", "imagen")
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            # `list` enlaza con el <datalist> del template (categorías del
            # negocio): el usuario puede elegir una existente o escribir una nueva.
            "categoria": forms.TextInput(attrs={
                "class": "form-control",
                "list": "categorias-existentes",
                "autocomplete": "off",
                "placeholder": "Elige una o escribe una nueva",
            }),
            "stock_disponible": forms.NumberInput(attrs={"class": "form-control"}),
            "imagen": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }