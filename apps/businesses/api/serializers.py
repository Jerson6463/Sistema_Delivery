from rest_framework import serializers

from apps.businesses.application.services import NegocioService
from apps.businesses.models import Negocio


class NegocioSerializer(serializers.ModelSerializer):
    categoria_display = serializers.CharField(source="get_categoria_display", read_only=True)
    abierto = serializers.SerializerMethodField()

    class Meta:
        model = Negocio
        fields = (
            "id", "nombre", "categoria", "categoria_display", "direccion",
            "calificacion_promedio", "abierto",
        )

    def get_abierto(self, obj):
        return NegocioService.esta_abierto(obj)