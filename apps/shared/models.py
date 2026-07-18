from django.conf import settings
from django.db import models
from django.db.models.deletion import ProtectedError
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet con borrado lógico.

    `delete()` marca los registros como inactivos (soft delete) en lugar de
    borrarlos físicamente. Para el borrado físico definitivo se usa
    `hard_delete()`. Así el borrado lógico funciona también en masa
    (`Modelo.objects.filter(...).delete()`), no solo por instancia.
    """

    def delete(self):
        """
        Borrado lógico en masa. NO elimina filas de la base de datos.

        Devuelve la misma tupla que `QuerySet.delete()` de Django,
        `(total, {label: total})`, para no romper su contrato: hay código
        (propio y de terceros) que desempaqueta ese valor.
        """
        if self.model.proteger_si_hay:
            # El modelo declara relaciones protegidas, así que hay que
            # comprobarlas fila a fila: un UPDATE en masa no las vería.
            # Se validan TODAS antes de tocar nada, para que la operación
            # sea todo-o-nada.
            for obj in self:
                obj.validar_sin_hijos_protegidos()

        ahora = timezone.now()
        # `actualizado_en` se pasa a mano: update() no dispara auto_now, y sin
        # esto el borrado en masa dejaría una marca de tiempo distinta a la
        # del borrado por instancia.
        total = self.update(activo=False, eliminado_en=ahora, actualizado_en=ahora)
        return total, ({self.model._meta.label: total} if total else {})

    def hard_delete(self):
        """Borrado físico definitivo en masa."""
        return super().delete()

    def vivos(self):
        return self.filter(activo=True)

    def eliminados(self):
        return self.filter(activo=False)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """
    Manager que, por defecto, oculta los registros borrados lógicamente.

    Con `incluir_eliminados=True` devuelve TODOS los registros (vivos y
    borrados). Ese manager sin filtro (`todos`) se usa además como
    `base_manager_name` para que las operaciones internas de Django
    (recolección de cascadas, validación de claves foráneas) no ignoren
    registros borrados.
    """

    def __init__(self, *args, incluir_eliminados=False, **kwargs):
        self._incluir_eliminados = incluir_eliminados
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self._incluir_eliminados:
            return qs
        return qs.filter(activo=True)


class BaseModel(models.Model):
    """
    Modelo base para todo el proyecto.

    Aporta auditoría (creado/actualizado, creado_por) y borrado lógico
    (soft delete). En este sistema NO se borra físicamente pedidos,
    productos, usuarios ni negocios, porque afecta auditoría, reportes y
    trazabilidad.

    Soft delete:
    - `delete()` (instancia y QuerySet) marca `activo=False` y guarda
      `eliminado_en`; NO elimina la fila.
    - El manager por defecto `objects` OCULTA los registros borrados; el
      manager `todos` los incluye.
    - `restaurar()` deshace el borrado; `hard_delete()` borra físicamente.
    - El borrado lógico NO cascada: desactivar un registro no desactiva sus
      hijos (es una desactivación, no un DELETE). Si un flujo necesita
      cascada lógica, debe hacerlo explícitamente en su service.
    - Para impedir que un borrado lógico deje hijos vivos huérfanos, el
      modelo declara `proteger_si_hay` (ver más abajo).
    """

    # Relaciones inversas que impiden el borrado lógico mientras tengan
    # hijos vivos. Emula on_delete=PROTECT, que el soft delete NO dispara:
    # al ser un UPDATE y no un DELETE, Django nunca evalúa on_delete.
    #
    # Solo se declaran relaciones a entidades VIVAS (un distrito, un
    # negocio, un cliente), donde el daño es real: quedarían apuntando a un
    # padre invisible para `objects`. Las relaciones HISTÓRICAS (Pedido,
    # DetallePedido, Calificacion) no se declaran aunque sean PROTECT: ese
    # PROTECT existe para no perder el histórico ante un borrado físico, y
    # el soft delete ya lo conserva. Declararlas haría que un producto o un
    # distrito ya usado no se pudiera retirar nunca.
    proteger_si_hay: tuple[str, ...] = ()

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_creados",
    )
    activo = models.BooleanField(default=True)
    eliminado_en = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()                       # oculta borrados
    todos = SoftDeleteManager(incluir_eliminados=True)  # incluye borrados

    class Meta:
        abstract = True
        # `todos` (sin filtro) como base_manager: las operaciones internas de
        # Django (acceso a una FK, recolección de cascadas) deben ver también
        # los registros borrados, o `pedido.negocio` reventaría con
        # DoesNotExist en cuanto el negocio se borrara lógicamente.
        #
        # Es explícito a propósito, no imprescindible: si no se declarara,
        # Django caería en un Manager() sin filtro que hace lo mismo. Se deja
        # escrito para fijar la intención y porque un `default_manager_name`
        # futuro sí podría cambiar el comportamiento. Los modelos hijos
        # declaran su propio Meta y no heredan este, así que el valor llega
        # por el fallback de MRO de Django; lo que importa es el
        # comportamiento, y está fijado en BaseManagerTests.
        base_manager_name = "todos"

    def hijos_protegidos(self):
        """
        Relaciones de `proteger_si_hay` que todavía tienen hijos vivos.

        Devuelve [(nombre_relacion, queryset), ...]. "Vivo" es lo que
        devuelve el manager por defecto de la relación: para los modelos que
        heredan BaseModel eso ya excluye los borrados lógicamente, así que
        un hijo borrado no bloquea el borrado del padre.
        """
        encontrados = []
        for relacion in self.proteger_si_hay:
            hijos = getattr(self, relacion).all()
            if hijos.exists():
                encontrados.append((relacion, hijos))
        return encontrados

    def validar_sin_hijos_protegidos(self):
        """Lanza ProtectedError si el borrado lógico dejaría hijos huérfanos."""
        encontrados = self.hijos_protegidos()
        if not encontrados:
            return
        detalle = ", ".join(
            f"{hijos.count()} en «{relacion}»" for relacion, hijos in encontrados
        )
        protegidos = set()
        for _, hijos in encontrados:
            protegidos.update(hijos)
        raise ProtectedError(
            f"No se puede eliminar «{self}» porque tiene registros que "
            f"dependen de él: {detalle}. Elimínalos o reasígnalos primero.",
            protegidos,
        )

    def delete(self, using=None, keep_parents=False):
        """
        Borrado lógico (por defecto). Para el físico usar `hard_delete()`.

        Lanza ProtectedError si el modelo declara `proteger_si_hay` y alguna
        de esas relaciones tiene hijos vivos.
        """
        self.validar_sin_hijos_protegidos()
        self.activo = False
        self.eliminado_en = timezone.now()
        self.save(
            using=using,
            update_fields=["activo", "eliminado_en", "actualizado_en"],
        )

    def hard_delete(self, using=None, keep_parents=False):
        """Borrado físico definitivo: elimina la fila de la base de datos."""
        return super().delete(using=using, keep_parents=keep_parents)

    def restaurar(self):
        """Deshace un borrado lógico."""
        self.activo = True
        self.eliminado_en = None
        self.save(update_fields=["activo", "eliminado_en", "actualizado_en"])

    def eliminar(self):
        """Alias de compatibilidad para `delete()` (borrado lógico)."""
        self.delete()
