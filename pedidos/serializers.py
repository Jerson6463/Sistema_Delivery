from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import Pedido, DetallePedido
from .validators import validar_creacion_pedido
from core.choices import Estados
from catalogo.models import Producto

class DetallePedidoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = DetallePedido
        fields = ['id', 'producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True)
    nombre_negocio = serializers.ReadOnlyField(source='negocio.nombre')
    
    # CORRECCIÓN: 'get' en lugar de 'ger'
    estado_display = serializers.ReadOnlyField(source='get_estado_display')

    class Meta:
        model = Pedido
        # CORRECCIÓN: 'estado_display' añadido a la lista
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
        detalles_data = validated_data.pop('detalles')
        negocio = validated_data['negocio']
        cliente = validated_data['cliente']
        
        # DRF ya se encarga de que item['producto'] sea un objeto.
        validar_creacion_pedido(negocio, detalles_data)
        
        with transaction.atomic():
            
            # CORRECCIÓN: Definimos un costo de envío inicial. 
            # (Más adelante podemos hacer que esto se calcule según la Zona).
            costo_envio_inicial = Decimal('5.00') 
            
            pedido = Pedido.objects.create(
                cliente=cliente,
                negocio=negocio,
                costo_envio=costo_envio_inicial,
                **validated_data
            )
            
            subtotal_acumulado = Decimal('0.00')
            
            for item in detalles_data:
                producto = item['producto']
                cantidad = item['cantidad']
                precio = producto.precio 
                linea_subtotal = precio * cantidad
                
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=linea_subtotal
                )
                
                # Tu excelente optimización se mantiene
                producto.stock_disponible -= cantidad
                producto.save(update_fields=['stock_disponible'])
                
                subtotal_acumulado += linea_subtotal
            
            pedido.subtotal = subtotal_acumulado
            pedido.total = subtotal_acumulado + pedido.costo_envio
            pedido.save(update_fields=['subtotal', 'total'])
            
            return pedido