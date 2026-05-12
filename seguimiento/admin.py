from django.contrib import admin
from .models import SeguimientoEntrega

@admin.register(SeguimientoEntrega)
class SeguimientoEntregaAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'latitud', 'longitud', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('pedido__id',)
    
    # Ordenamos por los más recientes primero
    ordering = ('-timestamp',)

    # --- SEGURIDAD DE AUDITORÍA ---
    # Nadie puede agregar o modificar puntos GPS manualmente desde el panel.
    # Solo el sistema a través de la API (cuando el celular envíe su ubicación) puede hacerlo.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False