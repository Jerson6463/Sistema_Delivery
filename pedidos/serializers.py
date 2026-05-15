from rest_framework import serializers
from .models import Pedido, DetallePedido
from .services import PedidoService

class DetallePedidoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True)
    nombre_negocio = serializers.ReadOnlyField(source='negocio.nombre')
    estado_display = serializers.ReadOnlyField(source='get_estado_display')

    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'negocio', 'nombre_negocio', 'repartidor', 
            'estado', 'estado_display', 'subtotal', 'costo_envio', 'total', 
            'direccion_entrega', 'detalles', 'creado_en'
        ]
        read_only_fields = [
            'estado', 'estado_display', 'subtotal', 'total', 
            'repartidor', 'costo_envio', 'creado_en'
        ]

    def create(self, validated_data):
        # 1. Separamos los detalles de la cabecera
        detalles_data = validated_data.pop('detalles')
        
        # 2. DELEGAMOS la responsabilidad a la Capa de Servicios
        return PedidoService.procesar_nuevo_pedido(
            datos_pedido=validated_data,
            detalles_data=detalles_data
        )