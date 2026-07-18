from rest_framework import serializers


class UbicacionSerializer(serializers.Serializer):
    latitud = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=-90, max_value=90
    )
    longitud = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=-180, max_value=180
    )