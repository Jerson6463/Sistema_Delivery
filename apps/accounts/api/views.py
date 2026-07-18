from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api.serializers import (
    LoginSerializer, RegistroClienteSerializer, RegistroNegocioSerializer,
    RegistroRepartidorSerializer, UserSerializer,
)
from apps.accounts.application.services import AccountService

_REGISTRADORES = {
    "cliente": AccountService.registrar_cliente,
    "negocio": AccountService.registrar_negocio,
    "repartidor": AccountService.registrar_repartidor,
}
_SERIALIZERS = {
    "cliente": RegistroClienteSerializer,
    "negocio": RegistroNegocioSerializer,
    "repartidor": RegistroRepartidorSerializer,
}


@api_view(["POST"])
@permission_classes([AllowAny])
def registrar(request, rol):
    metodo = _REGISTRADORES.get(rol)
    if metodo is None:
        return Response({"error": "ROL_INVALIDO"}, status=400)

    serializer = _SERIALIZERS[rol](data=request.data)
    serializer.is_valid(raise_exception=True)
    user = metodo(**serializer.validated_data)
    data = UserSerializer(user).data
    if user.aprobado:
        token, _ = Token.objects.get_or_create(user=user)
        data["token"] = token.key
    return Response(data, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def opciones_registro(request):
    return Response(AccountService.opciones_registro())


@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        username=serializer.validated_data["username"],
        password=serializer.validated_data["password"],
    )
    if user is None:
        return Response({"error": "CREDENCIALES_INVALIDAS"}, status=401)
    if not user.aprobado:
        return Response({"error": "CUENTA_PENDIENTE"}, status=403)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_api(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
