from rest_framework import serializers
from .models import SeguimientoEntrega

class SeguimientoEntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeguimientoEntrega
        fields = ['id', 'pedido', 'latitud', 'longitud', 'timestamp']
        read_only_fields = ['id', 'pedido', 'timestamp']