from django.contrib import admin

from apps.shared.admin import SoftDeleteAdminMixin

from .models import Calificacion, DetallePedido, HistorialEstadoPedido, Pedido


class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0


class HistorialInline(admin.TabularInline):
    model = HistorialEstadoPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "cliente", "negocio", "estado", "total", "creado_en")
    list_filter = ("estado", "negocio")
    inlines = [DetalleInline, HistorialInline]


@admin.register(Calificacion)
class CalificacionAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "pedido", "negocio", "repartidor",
        "puntaje_negocio", "puntaje_repartidor", "creado_en",
    )
    list_filter = ("puntaje_negocio", "puntaje_repartidor", "negocio")
    readonly_fields = ("creado_en", "actualizado_en")