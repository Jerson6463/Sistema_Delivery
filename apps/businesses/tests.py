"""
Pruebas de TarifaEnvioService centradas en su interacción con el soft delete.

El caso importante es la reactivación: `unique_tarifa_negocio_zona` está
condicionado a `activo=True`, así que crear una tarifa nueva para un par
(negocio, zona) que ya tuvo una borrada NO da error de unicidad — dejaría dos
filas para el mismo par, una viva y otra borrada. El servicio lo evita
reactivando la existente con el manager `todos`.
"""
from datetime import datetime
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.businesses.application.services import (
    DistritoService,
    NegocioService,
    TarifaEnvioService,
    ZonaService,
)
from apps.businesses.domain.horario import esta_abierto
from apps.businesses.models import Negocio, TarifaEnvio, Zona, ZonaEntrega
from apps.businesses.web.forms import ConfiguracionNegocioForm
from apps.catalog.models import Producto
from apps.shared.domain.exceptions import DomainException, PermisoDominioException


class TarifaEnvioServiceSoftDeleteTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="clave", rol=User.Rol.ADMIN
        )
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.zona = Zona.objects.create(nombre="Centro")
        self.distrito = ZonaEntrega.objects.create(
            zona=self.zona, distrito="Miraflores"
        )

    def _guardar(self, costo):
        return TarifaEnvioService.guardar_tarifa(
            self.admin, self.negocio.id, costo=costo, zona_id=self.distrito.id
        )

    def test_guardar_crea_la_tarifa(self):
        tarifa = self._guardar(Decimal("5.00"))

        self.assertEqual(tarifa.costo, Decimal("5.00"))
        self.assertTrue(tarifa.activo)

    def test_eliminar_tarifa_es_soft_delete(self):
        tarifa = self._guardar(Decimal("5.00"))

        TarifaEnvioService.eliminar_tarifa(self.admin, tarifa.id)

        tarifa.refresh_from_db()
        self.assertFalse(tarifa.activo)
        self.assertTrue(TarifaEnvio.todos.filter(pk=tarifa.pk).exists())

    def test_volver_a_guardar_reactiva_en_vez_de_duplicar(self):
        tarifa = self._guardar(Decimal("5.00"))
        TarifaEnvioService.eliminar_tarifa(self.admin, tarifa.id)

        reactivada = self._guardar(Decimal("8.00"))

        # Misma fila, no una nueva: el UniqueConstraint condicional habría
        # permitido crear un duplicado y nadie se habría enterado.
        self.assertEqual(reactivada.pk, tarifa.pk)
        self.assertEqual(
            TarifaEnvio.todos.filter(
                negocio=self.negocio, zona_entrega=self.distrito
            ).count(),
            1,
        )

    def test_al_reactivar_limpia_eliminado_en(self):
        tarifa = self._guardar(Decimal("5.00"))
        TarifaEnvioService.eliminar_tarifa(self.admin, tarifa.id)

        reactivada = self._guardar(Decimal("8.00"))

        self.assertTrue(reactivada.activo)
        self.assertIsNone(reactivada.eliminado_en)
        self.assertEqual(reactivada.costo, Decimal("8.00"))

    def test_listar_oculta_las_tarifas_borradas(self):
        tarifa = self._guardar(Decimal("5.00"))
        TarifaEnvioService.eliminar_tarifa(self.admin, tarifa.id)

        self.assertEqual(
            list(TarifaEnvioService.listar_por_negocio(self.negocio.id)), []
        )
        self.assertFalse(
            TarifaEnvioService.negocio_tiene_tarifas(self.negocio.id)
        )

    def test_obtener_tarifa_ignora_las_borradas(self):
        tarifa = self._guardar(Decimal("5.00"))
        TarifaEnvioService.eliminar_tarifa(self.admin, tarifa.id)

        self.assertIsNone(
            TarifaEnvioService.obtener_tarifa(self.negocio.id, self.distrito.id)
        )


class TarifaEnvioServicePermisosTests(TestCase):
    """La propiedad no basta: configurar tarifas es solo del admin."""

    def setUp(self):
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        self.negocio = Negocio.objects.create(
            usuario_dueno=self.dueno, nombre="Bodega", direccion="Av. Uno"
        )
        self.zona = Zona.objects.create(nombre="Centro")
        self.distrito = ZonaEntrega.objects.create(
            zona=self.zona, distrito="Miraflores"
        )

    def test_el_dueno_no_puede_guardar_su_propia_tarifa(self):
        with self.assertRaises(PermisoDominioException):
            TarifaEnvioService.guardar_tarifa(
                self.dueno, self.negocio.id,
                costo=Decimal("5.00"), zona_id=self.distrito.id,
            )

    def test_el_costo_negativo_se_rechaza(self):
        admin = User.objects.create_user(
            username="admin", password="clave", rol=User.Rol.ADMIN
        )
        with self.assertRaises(DomainException):
            TarifaEnvioService.guardar_tarifa(
                admin, self.negocio.id,
                costo=Decimal("-1.00"), zona_id=self.distrito.id,
            )


class NegocioConProductoDisponibleTests(TestCase):
    """
    `listar_negocios_disponibles` solo devuelve negocios con al menos un
    producto disponible para la venta (activo y con stock).
    """

    def _crear_negocio(self, username, nombre):
        dueno = User.objects.create_user(
            username=username, password="clave", rol=User.Rol.NEGOCIO
        )
        return Negocio.objects.create(
            usuario_dueno=dueno, nombre=nombre,
            direccion="Av. Uno", aprobado=True,
        )

    def test_negocio_sin_productos_no_aparece(self):
        self._crear_negocio("d1", "Sin productos")

        self.assertEqual(NegocioService.listar_negocios_disponibles(), [])

    def test_negocio_con_producto_agotado_no_aparece(self):
        negocio = self._crear_negocio("d2", "Agotado")
        Producto.objects.create(
            negocio=negocio, nombre="Pan",
            precio=Decimal("1.00"), stock_disponible=0,
        )

        self.assertEqual(NegocioService.listar_negocios_disponibles(), [])

    def test_negocio_con_producto_inactivo_no_aparece(self):
        negocio = self._crear_negocio("d3", "Inactivo")
        producto = Producto.objects.create(
            negocio=negocio, nombre="Pan",
            precio=Decimal("1.00"), stock_disponible=5,
        )
        producto.eliminar()  # soft delete -> activo=False

        self.assertEqual(NegocioService.listar_negocios_disponibles(), [])

    def test_negocio_con_producto_disponible_aparece_sin_duplicar(self):
        negocio = self._crear_negocio("d4", "Con stock")
        Producto.objects.create(
            negocio=negocio, nombre="Pan",
            precio=Decimal("1.00"), stock_disponible=5,
        )
        # Un segundo producto disponible no debe duplicar el negocio.
        Producto.objects.create(
            negocio=negocio, nombre="Leche",
            precio=Decimal("2.00"), stock_disponible=3,
        )

        negocios = NegocioService.listar_negocios_disponibles()

        self.assertEqual([n.id for n in negocios], [negocio.id])


# 2024-01-05 es viernes; 2024-01-06, sábado (para fijar el weekday sin depender
# de la fecha real del sistema).
VIERNES = datetime(2024, 1, 5)
SABADO = datetime(2024, 1, 6)


class HorarioNocturnoTests(TestCase):
    """Ventana que cruza la medianoche (Python puro, sin DB)."""

    def _horario_viernes(self, inicio, fin):
        cerrado = {"abierto": False, "inicio": None, "fin": None}
        horario = {
            dia: dict(cerrado) for dia in
            ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
        }
        horario["viernes"] = {"abierto": True, "inicio": inicio, "fin": fin}
        return horario

    def _en(self, horario, dia, hh, mm):
        return esta_abierto(horario, dia.replace(hour=hh, minute=mm))

    def test_viernes_noche_esta_abierto(self):
        horario = self._horario_viernes("18:00", "02:00")
        self.assertTrue(self._en(horario, VIERNES, 20, 0))
        self.assertTrue(self._en(horario, VIERNES, 23, 59))

    def test_sabado_madrugada_arrastra_desde_el_viernes(self):
        horario = self._horario_viernes("18:00", "02:00")
        # El sábado está cerrado, pero la franja pertenece al viernes.
        self.assertTrue(self._en(horario, SABADO, 1, 0))
        self.assertFalse(horario["sabado"]["abierto"])

    def test_sabado_despues_del_cierre_esta_cerrado(self):
        horario = self._horario_viernes("18:00", "02:00")
        self.assertFalse(self._en(horario, SABADO, 2, 30))

    def test_viernes_antes_de_abrir_esta_cerrado(self):
        horario = self._horario_viernes("18:00", "02:00")
        self.assertFalse(self._en(horario, VIERNES, 17, 59))
        self.assertFalse(self._en(horario, VIERNES, 10, 0))

    def test_ventana_normal_sigue_funcionando(self):
        horario = self._horario_viernes("08:00", "22:00")
        self.assertTrue(self._en(horario, VIERNES, 12, 0))
        self.assertFalse(self._en(horario, VIERNES, 23, 0))
        # Una ventana normal no arrastra nada al día siguiente.
        self.assertFalse(self._en(horario, SABADO, 1, 0))


class ConfiguracionNegocioFormHorarioTests(TestCase):
    """La validación permite horario nocturno pero no apertura == cierre."""

    def _form(self, apertura, cierre):
        return ConfiguracionNegocioForm(data={
            "hora_apertura": apertura,
            "hora_cierre": cierre,
            "dias_atencion": ["viernes"],
        })

    def test_horario_nocturno_es_valido(self):
        self.assertTrue(self._form("18:00", "02:00").is_valid())

    def test_apertura_igual_a_cierre_es_invalido(self):
        form = self._form("18:00", "18:00")
        self.assertFalse(form.is_valid())
        self.assertIn("hora_cierre", form.errors)

    def test_horario_normal_sigue_siendo_valido(self):
        self.assertTrue(self._form("08:00", "22:00").is_valid())


class ZonaServiceTests(TestCase):
    """Gestión de zonas desde el panel: alta, edición, borrado y validaciones."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="clave", rol=User.Rol.ADMIN
        )
        self.dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )

    def test_crear_zona(self):
        zona = ZonaService.crear(self.admin, "Centro")
        self.assertTrue(zona.activo)
        self.assertEqual(zona.nombre, "Centro")

    def test_crear_zona_duplicada_falla(self):
        ZonaService.crear(self.admin, "Centro")
        with self.assertRaises(DomainException):
            ZonaService.crear(self.admin, "  centro  ")  # case/espacios ignorados

    def test_crear_zona_vacia_falla(self):
        with self.assertRaises(DomainException):
            ZonaService.crear(self.admin, "   ")

    def test_actualizar_zona(self):
        zona = ZonaService.crear(self.admin, "Centro")
        ZonaService.actualizar(self.admin, zona.id, "Centro Histórico")
        zona.refresh_from_db()
        self.assertEqual(zona.nombre, "Centro Histórico")

    def test_actualizar_a_nombre_existente_falla(self):
        ZonaService.crear(self.admin, "Norte")
        zona = ZonaService.crear(self.admin, "Sur")
        with self.assertRaises(DomainException):
            ZonaService.actualizar(self.admin, zona.id, "Norte")

    def test_eliminar_zona_es_soft_delete(self):
        zona = ZonaService.crear(self.admin, "Centro")
        ZonaService.eliminar(self.admin, zona.id)
        zona.refresh_from_db()
        self.assertFalse(zona.activo)

    def test_no_se_puede_eliminar_zona_con_distritos(self):
        zona = ZonaService.crear(self.admin, "Centro")
        DistritoService.crear(self.admin, zona.id, "Miraflores")
        with self.assertRaises(DomainException):
            ZonaService.eliminar(self.admin, zona.id)
        zona.refresh_from_db()
        self.assertTrue(zona.activo)  # sigue viva

    def test_recrear_zona_borrada_la_reactiva_sin_duplicar(self):
        zona = ZonaService.crear(self.admin, "Centro")
        ZonaService.eliminar(self.admin, zona.id)
        recreada = ZonaService.crear(self.admin, "Centro")
        self.assertEqual(recreada.pk, zona.pk)
        self.assertEqual(Zona.todos.filter(nombre__iexact="Centro").count(), 1)

    def test_no_admin_no_puede_gestionar(self):
        with self.assertRaises(PermisoDominioException):
            ZonaService.crear(self.dueno, "Centro")


class DistritoServiceTests(TestCase):
    """Gestión de distritos: alta con zona, edición, borrado y validaciones."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="clave", rol=User.Rol.ADMIN
        )
        self.zona = ZonaService.crear(self.admin, "Centro")
        self.otra_zona = ZonaService.crear(self.admin, "Norte")

    def test_crear_distrito_asociado_a_zona(self):
        distrito = DistritoService.crear(self.admin, self.zona.id, "Miraflores")
        self.assertEqual(distrito.zona_id, self.zona.id)
        self.assertTrue(distrito.activo)

    def test_crear_distrito_duplicado_en_la_zona_falla(self):
        DistritoService.crear(self.admin, self.zona.id, "Miraflores")
        with self.assertRaises(DomainException):
            DistritoService.crear(self.admin, self.zona.id, "miraflores")

    def test_mismo_distrito_en_otra_zona_es_valido(self):
        DistritoService.crear(self.admin, self.zona.id, "Miraflores")
        distrito = DistritoService.crear(self.admin, self.otra_zona.id, "Miraflores")
        self.assertEqual(distrito.zona_id, self.otra_zona.id)

    def test_crear_distrito_en_zona_inexistente_falla(self):
        with self.assertRaises(DomainException):
            DistritoService.crear(self.admin, 999999, "Miraflores")

    def test_editar_distrito_reasigna_zona(self):
        distrito = DistritoService.crear(self.admin, self.zona.id, "Miraflores")
        DistritoService.actualizar(
            self.admin, distrito.id, self.otra_zona.id, "Miraflores"
        )
        distrito.refresh_from_db()
        self.assertEqual(distrito.zona_id, self.otra_zona.id)

    def test_eliminar_distrito_es_soft_delete(self):
        distrito = DistritoService.crear(self.admin, self.zona.id, "Miraflores")
        DistritoService.eliminar(self.admin, distrito.id)
        distrito.refresh_from_db()
        self.assertFalse(distrito.activo)

    def test_no_se_puede_eliminar_distrito_con_negocio(self):
        distrito = DistritoService.crear(self.admin, self.zona.id, "Miraflores")
        dueno = User.objects.create_user(
            username="dueno", password="clave", rol=User.Rol.NEGOCIO
        )
        Negocio.objects.create(
            usuario_dueno=dueno, nombre="Bodega", direccion="Av. Uno", zona=distrito
        )
        with self.assertRaises(DomainException):
            DistritoService.eliminar(self.admin, distrito.id)
        distrito.refresh_from_db()
        self.assertTrue(distrito.activo)
