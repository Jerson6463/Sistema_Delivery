from rest_framework import serializers
from .models import Negocio, Producto, Zona, TipoVehiculo
from .validators import validar_formato_horario


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = ['id', 'nombre', 'centro_latitud', 'centro_longitud']
        read_only_fields = ['id']


class TipoVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoVehiculo
        fields = ['id', 'nombre', 'radio_maximo_km', 'activo']
        read_only_fields = ['id']


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = [
            'id', 'negocio', 'nombre', 'precio', 
            'categoria', 'stock_disponible', 'disponible', 'imagen'
        ]
        # 'disponible' es el @property, DRF lo inferirá automáticamente
        read_only_fields = ['id', 'disponible']


class NegocioListSerializer(serializers.ModelSerializer):
    """Para GET /api/negocios/ — listado ligero sin productos anidados."""
    cantidad_productos = serializers.SerializerMethodField()
    
    class Meta:
        model = Negocio
        fields = [
            'id', 'nombre', 'categoria', 'direccion', 'horario',
            'activo', 'calificacion_promedio', 'cantidad_productos',
            'esta_abierto'
        ]
        read_only_fields = ['id', 'calificacion_promedio', 'esta_abierto']
    
    def get_cantidad_productos(self, obj):
        return obj.productos.filter(stock_disponible__gt=0).count()


class NegocioDetailSerializer(serializers.ModelSerializer):
    productos = ProductoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Negocio
        fields = [
            'id', 'nombre', 'categoria', 'direccion', 'horario',
            'activo', 'calificacion_promedio', 'productos', 'esta_abierto'
        ]
        read_only_fields = ['id', 'calificacion_promedio', 'esta_abierto']

    def validate_horario(self, value):
        return validar_formato_horario(value)