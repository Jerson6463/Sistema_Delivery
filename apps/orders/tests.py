from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.businesses.application.services import TarifaEnvioService
from apps.businesses.domain.horario import DIAS
from apps.businesses.models import Negocio, Zona, ZonaEntrega
from apps.catalog.models import Producto
from apps.orders.application.services import PedidoService
from apps.orders.domain.states import Estado
from apps.orders.models import Pedido
from apps.orders.web.cart import SESSION_KEY


def _horario(abierto):
    if abierto:
        return {
            dia: {"abierto": True, "inicio": "00:00", "fin": "23:59"}
            for dia in DIAS
        }
    return {
        dia: {"abierto": False, "inicio": None, "fin": None}
        for dia in DIAS
    }


class NegocioCerradoBloqueaCompraTests(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cliente", email="cliente@example.com", password="clave",
            rol=User.Rol.CLIENTE, aprobado=True,
        )
        self.dueno = User.objects.create_user(
            username="dueno", email="dueno@example.com", password="clave",
            rol=User.Rol.NEGOCIO, aprobado=True,
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno",
            aprobado=True, activo=True, horario_json=_horario(abierto=False),
        )
        self.producto = Producto.objects.create(
            negocio=self.negocio, nombre="Arroz", precio=Decimal("5.00"),
            stock_disponible=10, activo=True,
        )
        self.client.force_login(self.cliente)

    def _cerrar(self):
        self.negocio.horario_json = _horario(abierto=False)
        self.negocio.save(update_fields=["horario_json"])

    def _abrir(self):
        self.negocio.horario_json = _horario(abierto=True)
        self.negocio.save(update_fields=["horario_json"])

    def test_detalle_negocio_cerrado_bloquea_acceso(self):
        self._cerrar()
        resp = self.client.get(reverse("detalle_negocio", args=[self.negocio.id]))
        self.assertRedirects(resp, reverse("lista_negocios"))

    def test_agregar_al_carrito_cerrado_lo_rechaza(self):
        self._cerrar()
        resp = self.client.post(reverse("agregar_al_carrito", args=[self.producto.id]))
        self.assertRedirects(resp, reverse("lista_negocios"))
        carrito = self.client.session.get(SESSION_KEY) or {"items": {}}
        self.assertEqual(carrito.get("items"), {})

    def test_detalle_negocio_abierto_se_ve(self):
        self._abrir()
        resp = self.client.get(reverse("detalle_negocio", args=[self.negocio.id]))
        self.assertEqual(resp.status_code, 200)

    def test_agregar_al_carrito_abierto_funciona(self):
        self._abrir()
        resp = self.client.post(reverse("agregar_al_carrito", args=[self.producto.id]))
        self.assertRedirects(resp, reverse("detalle_negocio", args=[self.negocio.id]))
        carrito = self.client.session.get(SESSION_KEY)
        self.assertEqual(carrito["items"], {str(self.producto.id): 1})


class PedidoServiceCarritoTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", email="admin@example.com", password="clave",
            rol=User.Rol.ADMIN, aprobado=True,
        )
        self.cliente = User.objects.create_user(
            username="cliente", email="cliente@example.com", password="clave",
            rol=User.Rol.CLIENTE, aprobado=True, direccion="Av. Cliente",
        )
        self.zona = Zona.objects.create(nombre="Centro")
        self.distrito = ZonaEntrega.objects.create(
            zona=self.zona, distrito="Miraflores"
        )
        self.cliente.zona_entrega = self.distrito
        self.cliente.save(update_fields=["zona_entrega"])

        self.dueno = User.objects.create_user(
            username="dueno", email="dueno@example.com", password="clave",
            rol=User.Rol.NEGOCIO, aprobado=True,
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno,
            nombre="Bodega",
            direccion="Av. Uno",
            aprobado=True,
            activo=True,
            zona=self.distrito,
            horario_json=_horario(abierto=True),
        )
        self.producto = Producto.objects.create(
            negocio=self.negocio, nombre="Arroz", precio=Decimal("5.00"),
            stock_disponible=10, activo=True,
        )

        self.otro_dueno = User.objects.create_user(
            username="otro", email="otro@example.com", password="clave",
            rol=User.Rol.NEGOCIO, aprobado=True,
        )
        self.otro_negocio = Negocio.objects.create(
            usuario_dueno=self.otro_dueno,
            nombre="Tienda 2",
            direccion="Av. Dos",
            aprobado=True,
            activo=True,
            zona=self.distrito,
            horario_json=_horario(abierto=True),
        )
        self.otro_producto = Producto.objects.create(
            negocio=self.otro_negocio, nombre="Leche", precio=Decimal("4.00"),
            stock_disponible=7, activo=True,
        )

        TarifaEnvioService.guardar_tarifa(
            self.admin, self.negocio.id, costo=Decimal("5.00"), zona_id=self.distrito.id
        )

    def test_agregar_producto_de_otro_negocio_reinicia_el_carrito(self):
        session = {}

        PedidoService.agregar_al_carrito(session, self.producto.id)
        PedidoService.agregar_al_carrito(session, self.otro_producto.id)

        self.assertEqual(
            session[SESSION_KEY],
            {
                "negocio_id": self.otro_negocio.id,
                "items": {str(self.otro_producto.id): 1},
            },
        )

    def test_resumen_carrito_devuelve_lineas_y_subtotal(self):
        session = {}

        PedidoService.agregar_al_carrito(session, self.producto.id)
        PedidoService.agregar_al_carrito(session, self.producto.id)
        resumen = PedidoService.resumen_carrito(session)

        self.assertEqual(len(resumen["lineas"]), 1)
        self.assertEqual(resumen["lineas"][0]["cantidad"], 2)
        self.assertEqual(resumen["subtotal"], Decimal("10.00"))

    def test_crear_pedido_desde_carrito_lo_limpia(self):
        session = {}
        PedidoService.agregar_al_carrito(session, self.producto.id)

        pedido = PedidoService.crear_pedido_desde_carrito(
            self.cliente,
            session,
            direccion_entrega="Av. Cliente",
            zona_entrega_id=self.distrito.id,
            metodo_pago="EFECTIVO",
        )

        self.assertEqual(pedido.negocio_id, self.negocio.id)
        self.assertEqual(session[SESSION_KEY], {"negocio_id": None, "items": {}})


class ListarPedidosNegocioCicloVidaTests(TestCase):
    """El pedido acompaña todo su ciclo en el panel y solo desaparece al final."""

    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cliente", email="cliente@example.com", password="clave",
            rol=User.Rol.CLIENTE, aprobado=True,
        )
        self.dueno = User.objects.create_user(
            username="dueno", email="dueno@example.com", password="clave",
            rol=User.Rol.NEGOCIO, aprobado=True,
        )
        self.zona = Zona.objects.create(nombre="Centro")
        self.distrito = ZonaEntrega.objects.create(zona=self.zona, distrito="Miraflores")
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno",
            aprobado=True, activo=True, zona=self.distrito,
            horario_json=_horario(abierto=True),
        )

    def _pedido(self, estado):
        return Pedido.objects.create(
            cliente=self.cliente, negocio=self.negocio, estado=estado,
            subtotal=Decimal("10.00"), costo_envio=Decimal("5.00"),
            total=Decimal("15.00"), direccion_entrega="Av. Cliente",
            zona_entrega=self.distrito, metodo_pago="EFECTIVO",
        )

    def test_en_camino_sigue_visible_en_el_panel(self):
        pedido = self._pedido(Estado.EN_CAMINO)
        activos = PedidoService.listar_pedidos_negocio(self.negocio, solo_activos=True)
        self.assertIn(pedido, activos)

    def test_entregado_desaparece_del_panel(self):
        pedido = self._pedido(Estado.ENTREGADO)
        activos = PedidoService.listar_pedidos_negocio(self.negocio, solo_activos=True)
        self.assertNotIn(pedido, activos)

    def test_cancelado_desaparece_del_panel(self):
        pedido = self._pedido(Estado.CANCELADO)
        activos = PedidoService.listar_pedidos_negocio(self.negocio, solo_activos=True)
        self.assertNotIn(pedido, activos)
