"""
Capa de aplicación de negocios.
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from apps.businesses.domain.horario import DIAS, esta_abierto
from apps.businesses.models import Negocio, TarifaEnvio, Zona, ZonaEntrega
from apps.catalog.application.services import ProductoService
from apps.catalog.models import Producto
from apps.shared.domain.exceptions import (
    DomainException,
    NegocioCerradoException,
    PermisoDominioException,
    ZonaNoDisponibleException,
)


class NegocioService:

    @staticmethod
    def obtener_negocio_de_usuario(usuario):
        return Negocio.objects.filter(usuario_dueno=usuario).first()

    @staticmethod
    def esta_abierto(negocio: Negocio, momento=None) -> bool:
        momento = momento or timezone.localtime()
        return esta_abierto(negocio.horario_json, momento)

    @staticmethod
    def calcular_estado(negocio: Negocio, momento=None) -> str:
        return "Abierto" if NegocioService.esta_abierto(negocio, momento) else "Cerrado"

    @staticmethod
    def validar_abierto(negocio: Negocio, momento=None) -> None:
        if not NegocioService.esta_abierto(negocio, momento):
            raise NegocioCerradoException()

    @staticmethod
    def obtener_detalle_publico(negocio_id, *, exigir_abierto=False):
        negocio = Negocio.objects.get(pk=negocio_id, activo=True, aprobado=True)
        if exigir_abierto:
            NegocioService.validar_abierto(negocio)
        return {
            "negocio": negocio,
            "productos": ProductoService.listar_por_negocio(
                negocio_id, solo_activos=True
            ),
        }

    @staticmethod
    @transaction.atomic
    def actualizar_configuracion(
        negocio_id, actor, *, hora_apertura, hora_cierre, dias_atencion, imagen=None
    ):
        negocio = Negocio.objects.select_for_update().get(pk=negocio_id)
        es_dueno = negocio.usuario_dueno_id == getattr(actor, "id", None)
        if not (getattr(actor, "is_superuser", False) or es_dueno):
            raise PermisoDominioException(
                "No puedes editar la configuración de este negocio."
            )

        inicio = hora_apertura.strftime("%H:%M")
        fin = hora_cierre.strftime("%H:%M")
        seleccionados = set(dias_atencion)
        negocio.horario_json = {
            dia: (
                {"abierto": True, "inicio": inicio, "fin": fin}
                if dia in seleccionados
                else {"abierto": False, "inicio": None, "fin": None}
            )
            for dia in DIAS
        }
        campos = ["horario_json", "actualizado_en"]
        # La imagen es opcional: solo se toca si el negocio subió una nueva.
        if imagen:
            negocio.imagen = imagen
            campos.append("imagen")
        negocio.save(update_fields=campos)
        return negocio

    @staticmethod
    def listar_negocios_disponibles(categoria=None, solo_abiertos=False, zona=None):
        producto_disponible = Producto.objects.filter(
            negocio=OuterRef("pk"), stock_disponible__gt=0
        )
        qs = (
            Negocio.objects
            .filter(activo=True, aprobado=True)
            .filter(Exists(producto_disponible))
            .order_by("nombre")
        )
        if categoria:
            qs = qs.filter(categoria=categoria)
        if zona is not None:
            qs = qs.filter(zona__zona=zona)

        negocios = list(qs)
        if solo_abiertos:
            negocios = [n for n in negocios if NegocioService.esta_abierto(n)]
        return negocios


class TarifaEnvioService:

    @staticmethod
    def _exigir_admin(actor):
        if not getattr(actor, "es_admin", False):
            raise PermisoDominioException(
                "Solo un administrador puede configurar tarifas de envío."
            )

    @staticmethod
    def listar_por_negocio(negocio_id):
        return (
            TarifaEnvio.objects
            .filter(negocio_id=negocio_id, activo=True)
            .select_related("zona_entrega", "zona_entrega__zona")
            .order_by("zona_entrega__zona__nombre", "zona_entrega__distrito")
        )

    @staticmethod
    def negocio_tiene_tarifas(negocio_id) -> bool:
        return TarifaEnvio.objects.filter(
            negocio_id=negocio_id, activo=True
        ).exists()

    @staticmethod
    @transaction.atomic
    def guardar_tarifa(
        actor,
        negocio_id,
        *,
        costo,
        zona_id=None,
        nueva_zona_nombre=None,
        nueva_zona_distrito=None,
    ):
        TarifaEnvioService._exigir_admin(actor)

        if costo is None or costo < 0:
            raise DomainException(
                "El costo de envío debe ser un número mayor o igual a 0."
            )

        negocio = Negocio.objects.get(pk=negocio_id)

        if nueva_zona_nombre and nueva_zona_nombre.strip():
            nombre = nueva_zona_nombre.strip()
            distrito = (nueva_zona_distrito or nombre).strip()
            zona_general, _ = Zona.objects.get_or_create(
                nombre=nombre,
                defaults={"creado_por": actor},
            )
            zona, _ = ZonaEntrega.objects.get_or_create(
                zona=zona_general,
                distrito=distrito,
                defaults={"creado_por": actor},
            )
        elif zona_id:
            zona = ZonaEntrega.objects.get(pk=zona_id)
        else:
            raise DomainException("Debes seleccionar un distrito o crear uno nuevo.")

        tarifa, _ = TarifaEnvio.todos.update_or_create(
            negocio=negocio,
            zona_entrega=zona,
            defaults={
                "costo": costo,
                "activo": True,
                "eliminado_en": None,
                "creado_por": actor,
            },
        )
        return tarifa

    @staticmethod
    @transaction.atomic
    def actualizar_costo(actor, negocio_id, tarifa_id, nuevo_costo):
        """
        Actualiza SOLO el precio de una tarifa existente (edición en línea).

        A diferencia de `guardar_tarifa`, no depende del catálogo de distritos
        del negocio: la zona ya está fijada en la tarifa, así que solo se
        valida y guarda el monto. Valida que la tarifa pertenezca al negocio.
        """
        TarifaEnvioService._exigir_admin(actor)

        try:
            costo = Decimal(str(nuevo_costo).strip())
        except (InvalidOperation, TypeError, AttributeError):
            raise DomainException(
                "El precio debe ser un número válido, por ejemplo 5.50."
            )
        if costo < 0:
            raise DomainException("El precio no puede ser negativo.")
        costo = costo.quantize(Decimal("0.01"))

        try:
            tarifa = TarifaEnvio.objects.get(pk=tarifa_id, negocio_id=negocio_id)
        except TarifaEnvio.DoesNotExist:
            raise DomainException("La tarifa que intentas actualizar no existe.")

        tarifa.costo = costo
        tarifa.save(update_fields=["costo", "actualizado_en"])
        return tarifa

    @staticmethod
    @transaction.atomic
    def eliminar_tarifa(actor, tarifa_id):
        TarifaEnvioService._exigir_admin(actor)
        tarifa = TarifaEnvio.todos.get(pk=tarifa_id)
        tarifa.eliminar()
        return tarifa

    @staticmethod
    def obtener_tarifa(negocio_id, zona_id):
        return (
            TarifaEnvio.objects
            .filter(negocio_id=negocio_id, zona_entrega_id=zona_id, activo=True)
            .first()
        )

    @staticmethod
    def validar_zona_cubierta(negocio_id, zona_id) -> None:
        if TarifaEnvioService.obtener_tarifa(negocio_id, zona_id) is None:
            raise ZonaNoDisponibleException()

    @staticmethod
    def calcular_costo_envio(negocio_id, zona_id):
        tarifa = TarifaEnvioService.obtener_tarifa(negocio_id, zona_id)
        if tarifa is None:
            raise ZonaNoDisponibleException()
        return tarifa.costo


def _exigir_admin(actor):
    """Segunda barrera: la propiedad/rol no basta, la acción es solo de admin."""
    if not getattr(actor, "es_admin", False):
        raise PermisoDominioException(
            "Solo un administrador puede gestionar zonas y distritos."
        )


class ZonaService:
    """
    Gestión de zonas generales desde el panel de administración.

    La unicidad de `nombre` está condicionada a `activo=True`, así que una
    zona borrada lógicamente con el mismo nombre no bloquea recrearla: en su
    lugar se reactiva la fila existente (se usa el manager `todos`), igual que
    hace TarifaEnvioService al reactivar tarifas.
    """

    @staticmethod
    def listar():
        return (
            Zona.objects
            # Las agregaciones no aplican el filtro del manager: se cuentan
            # solo los distritos vivos explícitamente.
            .annotate(
                num_distritos=Count(
                    "distritos", filter=Q(distritos__activo=True)
                )
            )
            .order_by("nombre")
        )

    @staticmethod
    @transaction.atomic
    def crear(actor, nombre):
        _exigir_admin(actor)
        nombre = (nombre or "").strip()
        if not nombre:
            raise DomainException("El nombre de la zona no puede estar vacío.")

        if Zona.objects.filter(nombre__iexact=nombre).exists():
            raise DomainException(f"Ya existe una zona llamada «{nombre}».")

        inactiva = Zona.todos.filter(nombre__iexact=nombre, activo=False).first()
        if inactiva:                        # borrada lógicamente: se reactiva
            inactiva.nombre = nombre
            inactiva.activo = True
            inactiva.eliminado_en = None
            inactiva.save(update_fields=[
                "nombre", "activo", "eliminado_en", "actualizado_en",
            ])
            return inactiva
        return Zona.objects.create(nombre=nombre, creado_por=actor)

    @staticmethod
    @transaction.atomic
    def actualizar(actor, zona_id, nombre):
        _exigir_admin(actor)
        nombre = (nombre or "").strip()
        if not nombre:
            raise DomainException("El nombre de la zona no puede estar vacío.")

        zona = Zona.objects.select_for_update().get(pk=zona_id)
        if (
            Zona.objects.filter(nombre__iexact=nombre)
            .exclude(pk=zona.pk)
            .exists()
        ):
            raise DomainException(f"Ya existe una zona llamada «{nombre}».")

        zona.nombre = nombre
        zona.save(update_fields=["nombre", "actualizado_en"])
        return zona

    @staticmethod
    @transaction.atomic
    def eliminar(actor, zona_id):
        _exigir_admin(actor)
        zona = Zona.objects.select_for_update().get(pk=zona_id)
        try:
            zona.eliminar()             # soft delete; protege distritos/repartidores vivos
        except ProtectedError as e:
            raise DomainException(e.args[0])
        return zona


class DistritoService:
    """
    Gestión de distritos (ZonaEntrega), cada uno asociado a su zona.

    El par (zona, distrito) es único solo entre filas activas; un distrito
    borrado no impide recrearlo (se reactiva la fila existente).
    """

    @staticmethod
    def listar():
        return (
            ZonaEntrega.objects
            .select_related("zona")
            .order_by("zona__nombre", "distrito")
        )

    @staticmethod
    def _zona_activa(zona_id):
        try:
            return Zona.objects.get(pk=zona_id)
        except Zona.DoesNotExist:
            raise DomainException("La zona seleccionada no existe o fue eliminada.")

    @staticmethod
    @transaction.atomic
    def crear(actor, zona_id, distrito):
        _exigir_admin(actor)
        distrito = (distrito or "").strip()
        if not distrito:
            raise DomainException("El nombre del distrito no puede estar vacío.")
        zona = DistritoService._zona_activa(zona_id)

        if ZonaEntrega.objects.filter(zona=zona, distrito__iexact=distrito).exists():
            raise DomainException(
                f"El distrito «{distrito}» ya existe en la zona «{zona.nombre}»."
            )

        inactivo = ZonaEntrega.todos.filter(
            zona=zona, distrito__iexact=distrito, activo=False
        ).first()
        if inactivo:                        # borrado lógicamente: se reactiva
            inactivo.distrito = distrito
            inactivo.activo = True
            inactivo.eliminado_en = None
            inactivo.save(update_fields=[
                "distrito", "activo", "eliminado_en", "actualizado_en",
            ])
            return inactivo
        return ZonaEntrega.objects.create(
            zona=zona, distrito=distrito, creado_por=actor
        )

    @staticmethod
    @transaction.atomic
    def actualizar(actor, distrito_id, zona_id, distrito):
        _exigir_admin(actor)
        distrito = (distrito or "").strip()
        if not distrito:
            raise DomainException("El nombre del distrito no puede estar vacío.")
        zona = DistritoService._zona_activa(zona_id)

        obj = ZonaEntrega.objects.select_for_update().get(pk=distrito_id)
        if (
            ZonaEntrega.objects.filter(zona=zona, distrito__iexact=distrito)
            .exclude(pk=obj.pk)
            .exists()
        ):
            raise DomainException(
                f"El distrito «{distrito}» ya existe en la zona «{zona.nombre}»."
            )

        obj.zona = zona
        obj.distrito = distrito
        obj.save(update_fields=["zona", "distrito", "actualizado_en"])
        return obj

    @staticmethod
    @transaction.atomic
    def eliminar(actor, distrito_id):
        _exigir_admin(actor)
        obj = ZonaEntrega.objects.select_for_update().get(pk=distrito_id)
        try:
            obj.eliminar()              # soft delete; protege negocios/tarifas/clientes vivos
        except ProtectedError as e:
            raise DomainException(e.args[0])
        return obj
