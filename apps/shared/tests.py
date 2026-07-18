"""
Pruebas del comportamiento de soft delete provisto por BaseModel.

Se usa el modelo `Zona` (hereda BaseModel y solo requiere `nombre`) como
representante de cualquier modelo con borrado lógico. Cuando la prueba
depende de las relaciones (protección de hijos, histórico, OneToOne) se usan
los modelos reales que las tienen.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.businesses.models import Negocio, Zona, ZonaEntrega
from apps.catalog.models import Producto
from apps.orders.models import DetallePedido, Pedido


class SoftDeleteInstanciaTests(TestCase):
    def test_delete_de_instancia_es_logico(self):
        z = Zona.objects.create(nombre="Centro")
        z.delete()
        z.refresh_from_db()  # sigue existiendo la fila
        self.assertFalse(z.activo)
        self.assertIsNotNone(z.eliminado_en)

    def test_eliminar_es_alias_de_delete(self):
        z = Zona.objects.create(nombre="Norte")
        z.eliminar()
        z.refresh_from_db()
        self.assertFalse(z.activo)

    def test_hard_delete_de_instancia_borra_la_fila(self):
        z = Zona.objects.create(nombre="Sur")
        pk = z.pk
        z.hard_delete()
        self.assertFalse(Zona.todos.filter(pk=pk).exists())

    def test_restaurar_reactiva(self):
        z = Zona.objects.create(nombre="Este")
        z.delete()
        z.restaurar()
        z.refresh_from_db()
        self.assertTrue(z.activo)
        self.assertIsNone(z.eliminado_en)


class SoftDeleteManagerTests(TestCase):
    def test_objects_oculta_eliminados_y_todos_los_incluye(self):
        viva = Zona.objects.create(nombre="Viva")
        muerta = Zona.objects.create(nombre="Muerta")
        muerta.delete()

        ids_objects = set(Zona.objects.values_list("pk", flat=True))
        ids_todos = set(Zona.todos.values_list("pk", flat=True))

        self.assertIn(viva.pk, ids_objects)
        self.assertNotIn(muerta.pk, ids_objects)
        self.assertEqual(ids_todos, {viva.pk, muerta.pk})

    def test_get_por_objects_no_encuentra_eliminado(self):
        z = Zona.objects.create(nombre="Oculta")
        z.delete()
        with self.assertRaises(Zona.DoesNotExist):
            Zona.objects.get(pk=z.pk)
        # pero `todos` sí lo encuentra
        self.assertEqual(Zona.todos.get(pk=z.pk).pk, z.pk)

    def test_helpers_vivos_y_eliminados(self):
        viva = Zona.objects.create(nombre="A")
        muerta = Zona.objects.create(nombre="B")
        muerta.delete()
        self.assertEqual(list(Zona.todos.vivos()), [viva])
        self.assertEqual(list(Zona.todos.eliminados()), [muerta])


class SoftDeleteQuerySetTests(TestCase):
    def test_delete_en_masa_es_logico(self):
        Zona.objects.create(nombre="Q1")
        Zona.objects.create(nombre="Q2")
        borrados = Zona.objects.all().delete()

        # Respeta el contrato de Django: (total, {label: total}).
        self.assertEqual(borrados, (2, {"businesses.Zona": 2}))
        self.assertEqual(Zona.objects.count(), 0)
        self.assertEqual(Zona.todos.count(), 2)
        self.assertEqual(Zona.todos.eliminados().count(), 2)

    def test_delete_en_masa_sin_filas_devuelve_cero(self):
        # Django devuelve (0, {}) cuando no borra nada; el diccionario va
        # vacío, no con el label a 0.
        self.assertEqual(Zona.objects.none().delete(), (0, {}))

    def test_delete_en_masa_actualiza_actualizado_en(self):
        zona = Zona.objects.create(nombre="Q1")
        antes = Zona.todos.get(pk=zona.pk).actualizado_en

        Zona.objects.all().delete()

        despues = Zona.todos.get(pk=zona.pk)
        # update() no dispara auto_now, así que el valor se pasa a mano: sin
        # eso, el borrado en masa dejaría una marca distinta a la del borrado
        # por instancia.
        self.assertGreater(despues.actualizado_en, antes)
        self.assertEqual(despues.actualizado_en, despues.eliminado_en)

    def test_hard_delete_en_masa_borra_filas(self):
        Zona.objects.create(nombre="H1")
        Zona.objects.create(nombre="H2")
        Zona.todos.all().hard_delete()
        self.assertEqual(Zona.todos.count(), 0)


class SoftDeleteUnicidadTests(TestCase):
    def test_unicidad_ignora_registros_eliminados(self):
        z1 = Zona.objects.create(nombre="Centro")
        z1.delete()
        # Se puede recrear con el mismo nombre porque el anterior está borrado.
        z2 = Zona.objects.create(nombre="Centro")
        self.assertNotEqual(z1.pk, z2.pk)

    def test_dos_activos_con_mismo_nombre_fallan(self):
        Zona.objects.create(nombre="Centro")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Zona.objects.create(nombre="Centro")

    def test_unicidad_condicional_en_distrito(self):
        zona = Zona.objects.create(nombre="Lima")
        d1 = ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        d1.delete()
        # Se puede recrear el mismo distrito en la misma zona tras borrarlo.
        ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")


class SoftDeleteProteccionTests(TestCase):
    """
    `proteger_si_hay` emula on_delete=PROTECT en el borrado lógico.

    Django nunca evalúa on_delete en un soft delete, porque es un UPDATE y no
    un DELETE. Sin este guard, borrar una Zona dejaría sus distritos vivos
    apuntando a un padre que `objects` ya no devuelve.
    """

    def test_zona_con_distrito_vivo_no_se_puede_borrar(self):
        zona = Zona.objects.create(nombre="Centro")
        ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        with self.assertRaises(ProtectedError):
            zona.delete()
        zona.refresh_from_db()
        self.assertTrue(zona.activo)
        self.assertIsNone(zona.eliminado_en)

    def test_zona_sin_hijos_se_borra(self):
        zona = Zona.objects.create(nombre="Centro")
        zona.delete()
        zona.refresh_from_db()
        self.assertFalse(zona.activo)

    def test_un_hijo_borrado_ya_no_protege(self):
        zona = Zona.objects.create(nombre="Centro")
        distrito = ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        distrito.delete()
        zona.delete()  # el único distrito está borrado: ya no bloquea
        zona.refresh_from_db()
        self.assertFalse(zona.activo)

    def test_distrito_con_cliente_no_se_puede_borrar(self):
        zona = Zona.objects.create(nombre="Centro")
        distrito = ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        User.objects.create_user(
            username="cliente", password="clave", zona_entrega=distrito
        )
        with self.assertRaises(ProtectedError):
            distrito.delete()

    def test_borrado_en_masa_tambien_protege(self):
        zona = Zona.objects.create(nombre="Centro")
        ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        with self.assertRaises(ProtectedError):
            Zona.objects.filter(pk=zona.pk).delete()
        self.assertEqual(Zona.objects.count(), 1)

    def test_borrado_en_masa_es_todo_o_nada(self):
        libre = Zona.objects.create(nombre="Libre")
        ocupada = Zona.objects.create(nombre="Ocupada")
        ZonaEntrega.objects.create(zona=ocupada, distrito="Miraflores")

        with self.assertRaises(ProtectedError):
            Zona.objects.all().delete()

        # La zona sin hijos tampoco se borró: se validan todas las filas
        # ANTES de tocar ninguna.
        libre.refresh_from_db()
        self.assertTrue(libre.activo)


class SoftDeleteNoProtegeHistoricoTests(TestCase):
    """
    El guard NO debe emular los PROTECT hacia registros históricos.

    `DetallePedido.producto` es PROTECT para que un borrado FÍSICO no destruya
    el histórico del pedido; el soft delete ya lo conserva. Si alguien
    convirtiera `proteger_si_hay` en una regla general, un producto vendido no
    se podría desactivar nunca y este test lo detectaría.
    """

    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cliente", password="clave", rol=User.Rol.CLIENTE
        )
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.zona = Zona.objects.create(nombre="Centro")
        self.distrito = ZonaEntrega.objects.create(
            zona=self.zona, distrito="Miraflores"
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.producto = Producto.objects.create(
            negocio=self.negocio, nombre="Arroz",
            precio=Decimal("5.00"), stock_disponible=10,
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente, negocio=self.negocio,
            subtotal=Decimal("5.00"), costo_envio=Decimal("2.00"),
            total=Decimal("7.00"), direccion_entrega="Av. Uno",
            zona_entrega=self.distrito,
            metodo_pago=Pedido.MetodoPago.EFECTIVO,
        )
        DetallePedido.objects.create(
            pedido=self.pedido, producto=self.producto, cantidad=1,
            precio_unitario=Decimal("5.00"), subtotal=Decimal("5.00"),
        )

    def test_producto_ya_vendido_se_puede_desactivar(self):
        self.producto.delete()
        self.producto.refresh_from_db()
        self.assertFalse(self.producto.activo)
        # La línea del pedido sigue intacta: el histórico no se pierde.
        self.assertTrue(
            DetallePedido.objects.filter(producto=self.producto).exists()
        )

    def test_distrito_con_pedidos_se_puede_borrar(self):
        # `Pedido.zona_entrega` es PROTECT, pero es histórico y por eso no
        # está en `proteger_si_hay`. Nada vivo apunta a este distrito.
        self.assertTrue(self.distrito.pedidos.exists())

        self.distrito.delete()
        self.distrito.refresh_from_db()
        self.assertFalse(self.distrito.activo)

    def test_distrito_con_negocio_vivo_si_esta_protegido(self):
        # Contraste con el test anterior: el negocio SÍ es una entidad viva.
        self.negocio.zona = self.distrito
        self.negocio.save(update_fields=["zona"])

        with self.assertRaises(ProtectedError):
            self.distrito.delete()


class SoftDeleteOneToOneTests(TestCase):
    """
    Límite CONOCIDO y no resuelto: un OneToOneField crea un UNIQUE
    incondicional a nivel de columna que `condition=Q(activo=True)` no puede
    relajar, así que una fila borrada lógicamente sigue ocupando el slot.

    Hoy ningún flujo lo alcanza: `registrar_negocio` y `registrar_repartidor`
    siempre crean un usuario nuevo, así que `usuario_dueno` nunca colisiona.
    Este test fija el límite para que, si algún día se añade un flujo que cree
    un perfil para un usuario EXISTENTE, falle aquí y no en producción.
    """

    def test_negocio_borrado_bloquea_otro_negocio_del_mismo_dueno(self):
        dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        negocio = Negocio.objects.create(
            usuario_dueno=dueno, nombre="Bodega 1", direccion="Av. Uno"
        )
        negocio.delete()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Negocio.objects.create(
                    usuario_dueno=dueno, nombre="Bodega 2", direccion="Av. Dos"
                )

    def test_la_salida_es_reactivar_el_perfil_borrado(self):
        """La forma correcta de sortear el límite anterior: reactivar."""
        dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        negocio = Negocio.objects.create(
            usuario_dueno=dueno, nombre="Bodega 1", direccion="Av. Uno"
        )
        negocio.delete()

        recuperado = Negocio.todos.get(usuario_dueno=dueno)
        recuperado.restaurar()
        self.assertTrue(Negocio.objects.filter(usuario_dueno=dueno).exists())


class BaseManagerTests(TestCase):
    """
    El acceso a una FK usa `_base_manager`, que NO debe filtrar los borrados.

    Si filtrara, `distrito.zona` lanzaría DoesNotExist en cuanto la zona se
    borrara lógicamente, y el histórico se volvería inconsultable. Lo que
    importa es este comportamiento, no por qué vía lo consigue Django
    (`base_manager_name` en BaseModel.Meta o su fallback).
    """

    def test_fk_encuentra_al_padre_borrado(self):
        zona = Zona.objects.create(nombre="Centro")
        distrito = ZonaEntrega.objects.create(zona=zona, distrito="Miraflores")
        distrito.delete()  # el hijo borrado deja de proteger a la zona
        zona.delete()

        # Se relee desde cero para no usar la caché de la instancia.
        recargado = ZonaEntrega.todos.get(pk=distrito.pk)
        self.assertEqual(recargado.zona.pk, zona.pk)
        self.assertFalse(recargado.zona.activo)


class SoftDeleteAdminTests(TestCase):
    """
    El admin es el único sitio desde el que hoy se puede borrar una Zona, así
    que sus garantías se prueban contra el admin real (URLs + middleware), no
    llamando a los métodos del mixin sueltos.
    """

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="clave"
        )
        self.client.force_login(self.admin_user)
        self.url = reverse("admin:businesses_zona_changelist")

    def test_la_lista_muestra_los_registros_borrados(self):
        borrada = Zona.objects.create(nombre="Borrada")
        borrada.delete()
        resp = self.client.get(self.url)
        self.assertContains(resp, "Borrada")

    def test_restaurar_funciona_en_el_caso_normal(self):
        zona = Zona.objects.create(nombre="Centro")
        zona.delete()

        self.client.post(
            self.url,
            {
                "action": "restaurar_seleccionados",
                "_selected_action": [str(zona.pk)],
            },
            follow=True,
        )

        zona.refresh_from_db()
        self.assertTrue(zona.activo)
        self.assertIsNone(zona.eliminado_en)

    def test_restaurar_no_revienta_si_el_nombre_ya_esta_ocupado(self):
        vieja = Zona.objects.create(nombre="Centro")
        vieja.delete()
        Zona.objects.create(nombre="Centro")  # ocupa el hueco de unicidad

        resp = self.client.post(
            self.url,
            {
                "action": "restaurar_seleccionados",
                "_selected_action": [str(vieja.pk)],
            },
            follow=True,
        )

        # Antes esto era un IntegrityError crudo (error 500).
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No se pudo restaurar")
        vieja.refresh_from_db()
        self.assertFalse(vieja.activo)

    def test_restaurar_lo_que_puede_y_avisa_del_resto(self):
        bloqueada = Zona.objects.create(nombre="Centro")
        bloqueada.delete()
        Zona.objects.create(nombre="Centro")
        libre = Zona.objects.create(nombre="Norte")
        libre.delete()

        self.client.post(
            self.url,
            {
                "action": "restaurar_seleccionados",
                "_selected_action": [str(bloqueada.pk), str(libre.pk)],
            },
            follow=True,
        )

        # Que una falle no debe impedir que la otra se restaure.
        libre.refresh_from_db()
        bloqueada.refresh_from_db()
        self.assertTrue(libre.activo)
        self.assertFalse(bloqueada.activo)

    def test_activo_y_eliminado_en_no_son_editables_a_mano(self):
        zona = Zona.objects.create(nombre="Centro")
        resp = self.client.get(
            reverse("admin:businesses_zona_change", args=[zona.pk])
        )
        campos = resp.context["adminform"].form.fields
        self.assertNotIn("activo", campos)
        self.assertNotIn("eliminado_en", campos)
