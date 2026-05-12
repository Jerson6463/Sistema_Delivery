from django.contrib import admin
from django.contrib.admin import DateFieldListFilter
from .models import Pedido, DetallePedido

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = (
        'precio_unitario',
        'subtotal'
    )
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cliente',
        'negocio',
        'repartidor',
        'estado_coloreado',
        'total',
        'creado_en'
    )

    list_filter = (
        'estado',
        ('creado_en',DateFieldListFilter)
    )

    search_fields = (
        'cliente__usuario__username',
        'negocio__nombre',
        'repartidor__usuario__username'
    )

    readonly_fields = (
        'subtotal',
        'total',
        'creado_en'
    )

    inlines = [DetallePedidoInline]

    def estado_coloreado(self, obj):
        colores = {
            'RECIBIDO': '🟡',
            'CONFIRMADO': '🟢',
            'EN_PREPARACION': '🟠',
            'LISTO_PARA_RECOJO': '🔵',
            'EN_CAMINO': '🚚',
            'ENTREGADO': '✅',
            'CANCELADO': '🔴',
        }

        icono = colores.get(obj.estado, '⚪')
        return f'{icono} {obj.get_estado_display()}'
    estado_coloreado.short_description = 'Estado'

    #----REGLAS DE NEGOCIO ESTRICTAS-----
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj = None):
        return False

