from rest_framework import serializers

from apps.orders.models import DetallePedido, Pedido


class DetallePedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = DetallePedido
        fields = ("producto_nombre", "cantidad", "precio_unitario", "subtotal")


class PedidoSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    detalles = DetallePedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = (
            "id", "estado", "estado_display", "subtotal", "costo_envio", "total",
            "direccion_entrega", "metodo_pago", "creado_en", "detalles",
        )


class ItemSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)


class CrearPedidoSerializer(serializers.Serializer):
    negocio_id = serializers.IntegerField()
    items = ItemSerializer(many=True)
    # Opcional: si no se envía, se usa la dirección guardada del cliente.
    direccion_entrega = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    zona_entrega_id = serializers.IntegerField()
    metodo_pago = serializers.ChoiceField(choices=Pedido.MetodoPago.choices)


class CambiarEstadoSerializer(serializers.Serializer):
    estado = serializers.CharField()
    motivo = serializers.CharField(required=False, allow_blank=True, default="")