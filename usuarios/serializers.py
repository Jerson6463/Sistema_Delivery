from rest_framework import serializers
from .models import Usuario
from . import services

class RegistroClienteSerializer(serializers.ModelSerializer):
    direccion_principal = serializers.CharField(write_only=True)
    telefono = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'direccion_principal', 'telefono']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # 1. Extraemos los datos que no pertenecen al modelo Usuario base
        direccion = validated_data.pop('direccion_principal')
        telefono = validated_data.pop('telefono')
        
        # 2. Delegamos la ejecución al Servicio
        return services.registrar_nuevo_cliente(
            datos_usuario=validated_data,
            direccion=direccion,
            telefono=telefono
        )

class RegistroEmpresaSerializer(serializers.ModelSerializer):
    nombre_negocio = serializers.CharField(write_only=True)
    categoria_negocio = serializers.CharField(write_only=True)
    direccion_negocio = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'nombre_negocio', 'categoria_negocio', 'direccion_negocio']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        nombre = validated_data.pop('nombre_negocio')
        categoria = validated_data.pop('categoria_negocio')
        direccion = validated_data.pop('direccion_negocio')

        return services.registrar_nueva_empresa(
            datos_usuario=validated_data,
            nombre=nombre,
            categoria=categoria,
            direccion=direccion
        )
    
class RegistroRepartidorSerializer(serializers.ModelSerializer):
    # Campos adicionales del Perfil del Repartidor
    tipo_vehiculo_id = serializers.IntegerField(write_only=True)
    zona_cobertura_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'tipo_vehiculo_id', 'zona_cobertura_id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # 1. Extraemos los campos que no pertenecen al modelo Usuario
        vehiculo_id = validated_data.pop('tipo_vehiculo_id')
        zona_id = validated_data.pop('zona_cobertura_id')

        # 2. Delegamos la creación a la Capa de Servicios
        usuario = services.registrar_repartidor(
            datos_usuario=validated_data, 
            vehiculo_id=vehiculo_id, 
            zona_id=zona_id
        )
        
        return usuario
    
class PerfilUsuarioSerializer(serializers.ModelSerializer):
    """Traductor exclusivo para devolver la información pública del usuario logueado."""
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol']