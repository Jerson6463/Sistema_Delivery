from django.contrib import admin, messages
from django.db import IntegrityError, transaction

# Campos que gestionan el borrado lógico. Nunca se editan a mano desde un
# formulario: hacerlo saltaría el guard `proteger_si_hay` y dejaría un
# registro invisible con `eliminado_en` a NULL, imposible de auditar. El
# borrado y la restauración van por las acciones de más abajo.
CAMPOS_SOFT_DELETE = ("activo", "eliminado_en")


class SoftDeleteAdminMixin:
    """
    Mixin de admin para modelos con soft delete (que heredan de BaseModel).

    - Muestra también los registros borrados lógicamente (usa el manager
      `todos`), para que un administrador pueda auditarlos y restaurarlos.
      El manager por defecto `objects` los oculta, así que sin esto el admin
      no vería nada borrado.
    - Añade acciones para restaurar y para borrar definitivamente (físico).

    La acción estándar "Eliminar seleccionados" queda como borrado LÓGICO,
    porque `QuerySet.delete()` de BaseModel es soft delete.
    """

    def get_queryset(self, request):
        return self.model.todos.all()

    def get_readonly_fields(self, request, obj=None):
        """Añade los campos de soft delete a los que declare cada admin."""
        return tuple(super().get_readonly_fields(request, obj)) + CAMPOS_SOFT_DELETE

    def get_deleted_objects(self, objs, request):
        """
        Suma los hijos que `proteger_si_hay` bloquea a la lista `protected`
        de Django.

        Django la construye con su Collector, que solo entiende el borrado
        FÍSICO y por tanto no ve las protecciones del borrado lógico. Al
        añadirlos aquí, el admin reutiliza su comportamiento nativo para
        PROTECT: muestra los objetos que lo impiden y oculta el botón de
        confirmar, en vez de reventar con un ProtectedError.
        """
        deletable, model_count, perms_needed, protected = super().get_deleted_objects(
            objs, request
        )
        protegidos = list(protected)
        for obj in objs:
            for _, hijos in obj.hijos_protegidos():
                protegidos.extend(hijos)
        return deletable, model_count, perms_needed, protegidos

    @admin.action(description="Restaurar seleccionados (deshacer borrado lógico)")
    def restaurar_seleccionados(self, request, queryset):
        """
        Restaura fila a fila, no en masa.

        Restaurar puede violar un UniqueConstraint condicionado a
        `activo=True`: si se borró "Centro" y luego se creó otro "Centro",
        reactivar el viejo deja dos activos con el mismo nombre. Un update()
        en masa reventaría con un IntegrityError crudo (error 500) y no
        restauraría ninguno; así se restaura lo que se puede y se informa del
        resto.
        """
        restaurados = 0
        fallidos = []
        for obj in queryset:
            try:
                with transaction.atomic():
                    obj.restaurar()
            except IntegrityError:
                fallidos.append(str(obj))
            else:
                restaurados += 1

        if restaurados:
            self.message_user(
                request, f"{restaurados} registro(s) restaurado(s).", messages.SUCCESS
            )
        if fallidos:
            self.message_user(
                request,
                "No se pudo restaurar: "
                + ", ".join(fallidos)
                + ". Ya existe un registro activo equivalente.",
                messages.ERROR,
            )

    @admin.action(description="Eliminar DEFINITIVAMENTE (borrado físico)")
    def eliminar_definitivamente(self, request, queryset):
        queryset.hard_delete()
        self.message_user(request, "Borrado físico completado.")

    actions = ["restaurar_seleccionados", "eliminar_definitivamente"]


class SoftDeleteInlineMixin:
    """
    Inline para modelos con soft delete.

    Sin esto, un inline usa el manager por defecto (`objects`) y OCULTA los
    hijos borrados aunque su ModelAdmin padre los muestre con `todos`: la
    misma pantalla acabaría siendo incoherente consigo misma.
    """

    def get_queryset(self, request):
        return self.model.todos.all()

    def get_readonly_fields(self, request, obj=None):
        return tuple(super().get_readonly_fields(request, obj)) + CAMPOS_SOFT_DELETE
