from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import User
from apps.businesses.models import Negocio
from apps.realtime import notifiers
from apps.realtime.consumers import NegocioPedidosConsumer


class NotificadorAislamientoPorNegocioTests(TestCase):
    """El evento de un pedido solo debe llegar al grupo de su propio negocio."""

    def test_pedido_creado_solo_va_al_grupo_de_su_negocio(self):
        pedido = SimpleNamespace(
            id=7, negocio_id=42, estado="RECIBIDO", total=Decimal("10.00")
        )
        with patch.object(notifiers, "_send") as enviar:
            notifiers.notificar_pedido_creado(pedido)

        grupos = [llamada.args[0] for llamada in enviar.call_args_list]
        self.assertIn("negocio_42", grupos)
        self.assertNotIn("negocio_99", grupos)

        payload = next(
            llamada.args[1] for llamada in enviar.call_args_list
            if llamada.args[0] == "negocio_42"
        )
        self.assertEqual(payload["type"], "pedido_creado")
        self.assertEqual(payload["pedido_id"], 7)

    def test_cambio_estado_notifica_al_grupo_del_negocio(self):
        pedido = SimpleNamespace(
            id=3, negocio_id=42, estado="CONFIRMADO",
            get_estado_display=lambda: "Confirmado",
        )
        with patch.object(notifiers, "_send") as enviar:
            notifiers.notificar_estado(pedido)

        grupos = [llamada.args[0] for llamada in enviar.call_args_list]
        self.assertIn("negocio_42", grupos)
        self.assertNotIn("negocio_99", grupos)


class NegocioPedidosConsumerAutorizacionTests(TestCase):
    """Una tienda no puede suscribirse al canal de pedidos de otra."""

    def setUp(self):
        self.dueno = User.objects.create_user(
            username="dueno", email="dueno@example.com", password="clave",
            rol=User.Rol.NEGOCIO, aprobado=True,
        )
        self.otro_dueno = User.objects.create_user(
            username="otro", email="otro@example.com", password="clave",
            rol=User.Rol.NEGOCIO, aprobado=True,
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno",
            aprobado=True, activo=True,
        )

    def _consumer(self, user):
        consumer = NegocioPedidosConsumer()
        consumer.user = user
        consumer.kwargs = {"negocio_id": str(self.negocio.id)}
        return consumer

    def test_dueno_propio_puede_suscribirse(self):
        self.assertTrue(self._consumer(self.dueno).autorizado())

    def test_dueno_ajeno_no_puede_suscribirse(self):
        self.assertFalse(self._consumer(self.otro_dueno).autorizado())
