from django.contrib import admin

from apps.shared.admin import SoftDeleteAdminMixin

from .models import Repartidor, SeguimientoEntrega


@admin.register(Repartidor)
class RepartidorAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "usuario", "zona_cobertura", "vehiculo",
        "calificacion_promedio", "disponible", "activo",
    )
    list_filter = ("zona_cobertura", "disponible", "activo")

@admin.register(SeguimientoEntrega)
class SeguimientoEntregaAdmin(admin.ModelAdmin):
    list_display = ("pedido", "repartidor", "latitud", "longitud", "timestamp")
    list_filter = ("repartidor",)