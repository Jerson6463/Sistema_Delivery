from django.contrib import admin

from apps.shared.admin import SoftDeleteAdminMixin, SoftDeleteInlineMixin

from .models import Negocio, TarifaEnvio, Zona, ZonaEntrega


class ZonaEntregaInline(SoftDeleteInlineMixin, admin.TabularInline):
    """
    Distritos que pertenecen a la zona, editables desde la propia zona.

    El mixin hace que el inline muestre también los distritos borrados, igual
    que hace ZonaAdmin con las zonas, y que `activo` se vea pero no se edite
    aquí (el borrado va por las acciones de la lista de distritos).
    """
    model = ZonaEntrega
    extra = 1
    fields = ("distrito", "activo")


@admin.register(Zona)
class ZonaAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)
    inlines = [ZonaEntregaInline]


@admin.register(ZonaEntrega)
class ZonaEntregaAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("distrito", "zona", "activo")
    list_filter = ("zona", "activo")
    search_fields = ("distrito", "zona__nombre")


@admin.register(Negocio)
class NegocioAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "usuario_dueno", "categoria", "aprobado", "activo")
    list_filter = ("categoria", "aprobado", "activo")
    search_fields = ("nombre",)


@admin.register(TarifaEnvio)
class TarifaEnvioAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("negocio", "zona_entrega", "costo", "activo")
    list_filter = ("negocio", "activo")