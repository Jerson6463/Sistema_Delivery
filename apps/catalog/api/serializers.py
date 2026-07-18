from rest_framework import serializers

from apps.catalog.models import Producto


class ProductoSerializer(serializers.ModelSerializer):
    agotado = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = (
            "id", "nombre", "precio", "categoria", "stock_disponible",
            "imagen", "activo", "agotado",
        )
        read_only_fields = ("activo",)


class ProductoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = ("nombre", "precio", "categoria", "stock_disponible", "imagen")