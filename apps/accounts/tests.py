from django.test import TestCase

from apps.accounts.api.serializers import RegistroSerializer, UserSerializer
from apps.accounts.application.services import AccountService
from apps.accounts.models import User
from apps.accounts.web.forms import RegistroUsuarioForm
from apps.businesses.models import Negocio, Zona, ZonaEntrega
from apps.delivery.models import Repartidor


class RegistroConDatosPersonalesTests(TestCase):
    def setUp(self):
        self.zona = Zona.objects.create(nombre="Centro")
        self.distrito = ZonaEntrega.objects.create(zona=self.zona, distrito="Lima")

    def test_formulario_exige_nombres_y_apellidos(self):
        form = RegistroUsuarioForm(data={
            "username": "cliente",
            "email": "cliente@example.com",
            "password1": "UnaClaveSegura123!",
            "password2": "UnaClaveSegura123!",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn("last_name", form.errors)

    def test_registra_los_tres_roles_con_datos_personales(self):
        cliente = AccountService.registrar_cliente(
            "cliente", "cliente@example.com", "clave",
            first_name="Ana", last_name="Torres",
        )
        negocio = AccountService.registrar_negocio(
            "negocio", "negocio@example.com", "clave", "Luis", "Rojas",
            "Bodega Central", Negocio.Categoria.ABARROTES, "Av. Uno", self.distrito,
        )
        repartidor = AccountService.registrar_repartidor(
            "repartidor", "repartidor@example.com", "clave", "Juan", "Paz",
            Repartidor.Vehiculo.MOTO, self.zona,
        )

        self.assertEqual(cliente.get_full_name(), "Ana Torres")
        self.assertEqual(negocio.get_full_name(), "Luis Rojas")
        self.assertEqual(repartidor.get_full_name(), "Juan Paz")

    def test_api_mapea_nombres_a_campos_existentes_del_usuario(self):
        serializer = RegistroSerializer(data={
            "username": "api_cliente",
            "email": "api@example.com",
            "nombres": "María",
            "apellidos": "López",
            "password": "UnaClaveSegura123!",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["first_name"], "María")
        self.assertEqual(serializer.validated_data["last_name"], "López")

        user = User(
            username="api_cliente", first_name="María", last_name="López"
        )
        data = UserSerializer(user).data
        self.assertEqual(data["nombres"], "María")
        self.assertEqual(data["apellidos"], "López")

    def test_actualiza_cliente_y_perfil_asociado(self):
        cliente = AccountService.registrar_cliente(
            "cliente", "cliente@example.com", "clave",
            first_name="Ana", last_name="Torres",
        )
        AccountService.actualizar_perfil(cliente, "Ana María", "Torres Paz")
        cliente.refresh_from_db()

        self.assertEqual(cliente.get_full_name(), "Ana María Torres Paz")
