"""
Pruebas de ProductoService centradas en su interacción con el soft delete.

El servicio es el único sitio donde se decide si una consulta usa `objects`
(oculta borrados) o `todos` (los incluye); equivocarse ahí significa que el
dueño de un negocio no pueda reactivar un producto que desactivó, o que un
producto desactivado siga apareciendo al público.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.businesses.models import Negocio
from apps.catalog.application.services import (
    CategoriaProductoService,
    ProductoService,
)
from apps.catalog.models import CategoriaProducto, Producto
from apps.shared.domain.exceptions import PermisoDominioException


class ProductoServiceSoftDeleteTests(TestCase):

    def setUp(self):
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.otro = User.objects.create_user(
            username="otro", password="clave", rol=User.Rol.NEGOCIO
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.producto = Producto.objects.create(
            negocio=self.negocio, nombre="Arroz",
            precio=Decimal("5.00"), stock_disponible=10,
        )

    def test_desactivar_producto_es_soft_delete(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)
        self.assertIsNotNone(self.producto.eliminado_en)
        # La fila sigue ahí: no se pierde el histórico de pedidos.
        self.assertTrue(Producto.todos.filter(pk=self.producto.pk).exists())

    def test_desactivar_producto_ajeno_esta_prohibido(self):
        with self.assertRaises(PermisoDominioException):
            ProductoService.desactivar_producto(self.producto.id, self.otro)

        self.producto.refresh_from_db()
        self.assertTrue(self.producto.activo)

    def test_listar_solo_activos_oculta_los_desactivados(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        visibles = ProductoService.listar_por_negocio(self.negocio.id)
        self.assertEqual(list(visibles), [])

    def test_listar_con_solo_activos_false_los_incluye(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        # El panel del dueño necesita ver los desactivados para reactivarlos.
        todos = ProductoService.listar_por_negocio(
            self.negocio.id, solo_activos=False
        )
        self.assertEqual(list(todos), [self.producto])

    def test_el_dueno_puede_reactivar_un_producto_desactivado(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        # `actualizar_producto` usa el manager `todos` justamente para esto:
        # con `objects` el producto sería invisible y saltaría DoesNotExist.
        ProductoService.actualizar_producto(
            self.producto.id, self.dueno, activo=True, eliminado_en=None
        )

        self.producto.refresh_from_db()
        self.assertTrue(self.producto.activo)

    def test_actualizar_un_producto_desactivado_no_lanza_does_not_exist(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        ProductoService.actualizar_producto(
            self.producto.id, self.dueno, precio=Decimal("7.50")
        )

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.precio, Decimal("7.50"))

    def test_activar_producto_deshace_el_soft_delete(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        ProductoService.activar_producto(self.producto.id, self.dueno)

        self.producto.refresh_from_db()
        self.assertTrue(self.producto.activo)
        self.assertIsNone(self.producto.eliminado_en)

    def test_activar_producto_ajeno_esta_prohibido(self):
        ProductoService.desactivar_producto(self.producto.id, self.dueno)

        with self.assertRaises(PermisoDominioException):
            ProductoService.activar_producto(self.producto.id, self.otro)

        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)


class EditarProductoInactivoViewTests(TestCase):
    """Un producto desactivado no debe poder editarse por URL directa."""

    def setUp(self):
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.producto = Producto.objects.create(
            negocio=self.negocio, nombre="Arroz",
            precio=Decimal("5.00"), stock_disponible=10,
        )
        self.client.force_login(self.dueno)

    def test_editar_producto_inactivo_por_url_da_404(self):
        self.producto.delete()  # soft delete -> activo=False

        resp = self.client.get(
            reverse("editar_producto", args=[self.producto.id])
        )
        self.assertEqual(resp.status_code, 404)

    def test_editar_producto_activo_funciona(self):
        resp = self.client.get(
            reverse("editar_producto", args=[self.producto.id])
        )
        self.assertEqual(resp.status_code, 200)


class ProductoRelacionInversaTests(TestCase):
    """
    El manager por defecto también filtra a través de las relaciones inversas:
    `negocio.productos` no debe devolver los productos borrados. Es lo que
    evita que un producto desactivado reaparezca en la ficha del negocio.
    """

    def setUp(self):
        dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.vivo = Producto.objects.create(
            negocio=self.negocio, nombre="Arroz",
            precio=Decimal("5.00"), stock_disponible=10,
        )
        self.borrado = Producto.objects.create(
            negocio=self.negocio, nombre="Fideos",
            precio=Decimal("3.00"), stock_disponible=5,
        )
        self.borrado.delete()

    def test_la_relacion_inversa_oculta_los_borrados(self):
        self.assertEqual(list(self.negocio.productos.all()), [self.vivo])

    def test_la_relacion_inversa_no_los_cuenta(self):
        self.assertEqual(self.negocio.productos.count(), 1)


class CategoriaProductoTests(TestCase):
    """Catálogo de categorías por negocio: reutilización, dedupe y aislamiento."""

    def setUp(self):
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.otro_dueno = User.objects.create_user(
            username="otro", password="clave", rol=User.Rol.NEGOCIO
        )
        self.otro_negocio = Negocio.objects.create(
            usuario_dueno=self.otro_dueno, nombre="Tienda 2", direccion="Av. Dos"
        )

    def _crear(self, negocio, categoria, nombre="Producto"):
        return ProductoService.crear_producto(
            negocio=negocio, nombre=nombre, precio=Decimal("5.00"),
            categoria=categoria, stock_disponible=3,
        )

    def test_crear_producto_registra_la_categoria_del_negocio(self):
        self._crear(self.negocio, "Bebidas")
        self.assertTrue(
            CategoriaProducto.objects.filter(negocio=self.negocio, nombre="Bebidas").exists()
        )

    def test_no_duplica_por_mayusculas_ni_espacios(self):
        p1 = self._crear(self.negocio, "Bebidas", nombre="Gaseosa")
        p2 = self._crear(self.negocio, "  bebidas  ", nombre="Agua")

        # Una sola categoría, y ambos productos usan el nombre canónico.
        self.assertEqual(
            CategoriaProducto.objects.filter(negocio=self.negocio).count(), 1
        )
        self.assertEqual(p1.categoria, "Bebidas")
        self.assertEqual(p2.categoria, "Bebidas")

    def test_normaliza_espacios_internos_y_extremos(self):
        p = self._crear(self.negocio, "  Comida   rápida  ")
        self.assertEqual(p.categoria, "Comida rápida")

    def test_categoria_vacia_no_crea_registro_y_guarda_el_producto(self):
        p = self._crear(self.negocio, "   ")
        self.assertEqual(p.categoria, "")
        self.assertFalse(CategoriaProducto.objects.filter(negocio=self.negocio).exists())

    def test_las_categorias_no_se_comparten_entre_negocios(self):
        self._crear(self.negocio, "Bebidas")
        self._crear(self.otro_negocio, "Postres")

        propias = CategoriaProductoService.listar_nombres(self.negocio.id)
        ajenas = CategoriaProductoService.listar_nombres(self.otro_negocio.id)
        self.assertIn("Bebidas", propias)
        self.assertNotIn("Postres", propias)
        self.assertIn("Postres", ajenas)
        self.assertNotIn("Bebidas", ajenas)

    def test_listar_incluye_categorias_de_productos_previos(self):
        # Producto creado "a mano" (histórico) sin pasar por el registro.
        Producto.objects.create(
            negocio=self.negocio, nombre="Pan",
            precio=Decimal("1.00"), stock_disponible=5, categoria="Panadería",
        )
        self.assertIn("Panadería", CategoriaProductoService.listar_nombres(self.negocio.id))

    def test_editar_producto_registra_la_categoria(self):
        producto = self._crear(self.negocio, "Bebidas")
        ProductoService.actualizar_producto(
            producto.id, self.dueno, categoria="Snacks"
        )
        self.assertTrue(
            CategoriaProducto.objects.filter(negocio=self.negocio, nombre="Snacks").exists()
        )

    def test_si_el_producto_falla_no_queda_categoria(self):
        # precio nulo -> el guardado del producto revienta; la categoría, al
        # registrarse en la misma transacción, no debe persistir.
        with self.assertRaises(Exception):
            ProductoService.crear_producto(
                negocio=self.negocio, nombre="Roto", precio=None,
                categoria="Fantasma", stock_disponible=1,
            )
        self.assertFalse(
            CategoriaProducto.objects.filter(
                negocio=self.negocio, nombre__iexact="Fantasma"
            ).exists()
        )
