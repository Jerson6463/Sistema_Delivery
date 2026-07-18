"""
Capa de aplicación del catálogo.

ProductoService concentra la gestión de productos y las operaciones de
stock. La regla clave: un negocio SOLO puede tocar sus propios productos,
y eso se valida aquí (no en el template).

Las operaciones descontar_stock/restaurar_stock se usarán dentro de la
transacción de creación/cancelación de pedidos (Fase 4), con las filas
ya bloqueadas mediante select_for_update().
"""
from django.db import transaction

from apps.catalog.models import CategoriaProducto, Producto
from apps.shared.domain.exceptions import (
    PermisoDominioException,
    StockInsuficienteException,
)


class CategoriaProductoService:
    """
    Catálogo de categorías por negocio, reutilizable entre productos.

    `registrar` normaliza el nombre (quita espacios sobrantes) y, si no está
    ya registrado para ese negocio (sin distinguir mayúsculas/minúsculas),
    lo crea. Devuelve SIEMPRE el nombre canónico que debe guardarse en el
    producto. Un nombre vacío no crea nada (la categoría es opcional).
    """

    @staticmethod
    def _normalizar(nombre_raw) -> str:
        # Colapsa espacios internos y recorta extremos: "  Bebidas  frías " ->
        # "Bebidas frías"; así "bebidas" y "Bebidas " se tratan igual.
        return " ".join((nombre_raw or "").split())

    @staticmethod
    def registrar(negocio, nombre_raw) -> str:
        nombre = CategoriaProductoService._normalizar(nombre_raw)
        if not nombre:
            return ""                       # sin categoría: no se registra nada

        existente = CategoriaProducto.objects.filter(
            negocio=negocio, nombre__iexact=nombre
        ).first()
        if existente:
            return existente.nombre         # reutiliza el nombre ya guardado

        inactiva = CategoriaProducto.todos.filter(
            negocio=negocio, nombre__iexact=nombre, activo=False
        ).first()
        if inactiva:                        # estaba borrada lógicamente: se reactiva
            inactiva.activo = True
            inactiva.eliminado_en = None
            inactiva.save(update_fields=["activo", "eliminado_en", "actualizado_en"])
            return inactiva.nombre

        CategoriaProducto.objects.create(negocio=negocio, nombre=nombre)
        return nombre

    @staticmethod
    def listar_nombres(negocio_id):
        """
        Categorías reutilizables del negocio (para el autocompletado).

        Une las categorías ya registradas con las que usan sus productos
        actuales (para que el histórico aparezca sin depender de una migración
        de datos), sin duplicar por mayúsculas/minúsculas.
        """
        vistos = {}
        registradas = CategoriaProducto.objects.filter(
            negocio_id=negocio_id
        ).values_list("nombre", flat=True)
        usadas = (
            Producto.objects.filter(negocio_id=negocio_id)
            .exclude(categoria="")
            .values_list("categoria", flat=True)
            .distinct()
        )
        for nombre in list(registradas) + list(usadas):
            vistos.setdefault(nombre.lower(), nombre)
        return sorted(vistos.values(), key=str.lower)


class ProductoService:

    # --- Consulta ---
    @staticmethod
    def listar_por_negocio(negocio_id, solo_activos=True):
        # `objects` ya oculta los borrados; para incluirlos (panel del dueño)
        # se usa el manager `todos`.
        manager = Producto.objects if solo_activos else Producto.todos
        return manager.filter(negocio_id=negocio_id).order_by("nombre")

    # --- Gestión (dueño del negocio) ---
    @staticmethod
    @transaction.atomic
    def crear_producto(negocio, **datos):
        # La categoría se registra dentro de la MISMA transacción: si el
        # producto no llega a guardarse, la categoría tampoco se persiste.
        if "categoria" in datos:
            datos["categoria"] = CategoriaProductoService.registrar(
                negocio, datos["categoria"]
            )
        return Producto.objects.create(negocio=negocio, **datos)

    @staticmethod
    @transaction.atomic
    def actualizar_producto(producto_id, usuario, **datos):
        # `todos`: el dueño puede editar (incluso reactivar) un producto
        # que fue desactivado, y `objects` lo ocultaría.
        producto = Producto.todos.select_related("negocio").get(pk=producto_id)
        ProductoService._verificar_propiedad(producto, usuario)
        if "categoria" in datos:
            datos["categoria"] = CategoriaProductoService.registrar(
                producto.negocio, datos["categoria"]
            )
        for campo, valor in datos.items():
            setattr(producto, campo, valor)
        producto.save()
        return producto

    @staticmethod
    def desactivar_producto(producto_id, usuario):
        producto = Producto.todos.select_related("negocio").get(pk=producto_id)
        ProductoService._verificar_propiedad(producto, usuario)
        producto.eliminar()  # soft delete (activo=False)
        return producto

    @staticmethod
    def activar_producto(producto_id, usuario):
        # `todos`: el producto está desactivado, así que `objects` lo ocultaría.
        producto = Producto.todos.select_related("negocio").get(pk=producto_id)
        ProductoService._verificar_propiedad(producto, usuario)
        producto.restaurar()  # deshace el soft delete (activo=True)
        return producto

    # --- Stock (se invoca desde el pedido, dentro de una transacción) ---
    @staticmethod
    def validar_stock(producto, cantidad):
        if producto.stock_disponible < cantidad or producto.stock_disponible == 0:
            raise StockInsuficienteException(
                f"Stock insuficiente para '{producto.nombre}' "
                f"(disponible: {producto.stock_disponible}, pedido: {cantidad})."
            )

    @staticmethod
    def descontar_stock(producto, cantidad):
        ProductoService.validar_stock(producto, cantidad)
        producto.stock_disponible -= cantidad
        producto.save(update_fields=["stock_disponible", "actualizado_en"])

    @staticmethod
    def restaurar_stock(producto, cantidad):
        producto.stock_disponible += cantidad
        producto.save(update_fields=["stock_disponible", "actualizado_en"])

    # --- Helpers ---
    @staticmethod
    def _verificar_propiedad(producto, usuario):
        es_dueno = producto.negocio.usuario_dueno_id == getattr(usuario, "id", None)
        if not (es_dueno or getattr(usuario, "is_superuser", False)):
            raise PermisoDominioException(
                "No puedes gestionar productos de otro negocio."
            )