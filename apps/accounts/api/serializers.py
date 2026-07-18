from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User
from apps.businesses.models import Negocio, Zona, ZonaEntrega
from apps.delivery.models import Repartidor


class UserSerializer(serializers.ModelSerializer):
    nombres = serializers.CharField(source="first_name", read_only=True)
    apellidos = serializers.CharField(source="last_name", read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "nombres", "apellidos", "rol", "aprobado",
        )


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    nombres = serializers.CharField(source="first_name", max_length=150)
    apellidos = serializers.CharField(source="last_name", max_length=150)
    password = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El usuario ya existe.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class RegistroClienteSerializer(RegistroSerializer):
    direccion = serializers.CharField(max_length=255)
    zona_entrega = serializers.PrimaryKeyRelatedField(
        queryset=ZonaEntrega.objects.filter(activo=True)
    )


class RegistroNegocioSerializer(RegistroSerializer):
    nombre = serializers.CharField(max_length=150)
    categoria = serializers.ChoiceField(choices=Negocio.Categoria.choices)
    direccion = serializers.CharField(max_length=255)
    zona = serializers.PrimaryKeyRelatedField(
        queryset=ZonaEntrega.objects.filter(activo=True)
    )


class RegistroRepartidorSerializer(RegistroSerializer):
    vehiculo = serializers.ChoiceField(choices=Repartidor.Vehiculo.choices)
    zona_cobertura = serializers.PrimaryKeyRelatedField(
        queryset=Zona.objects.filter(activo=True)
    )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
