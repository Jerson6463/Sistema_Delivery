from django.contrib import admin
from django.utils.html import format_html # <-- Importación para colores
from .models import Negocio, Producto, Zona, TipoVehiculo

@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'propietario', 'categoria', 
        'activo', 'calificacion_promedio'
    )
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'direccion', 'propietario__username')
    raw_id_fields = ('propietario',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 'negocio', 'precio', 
        'stock_disponible', 'estado_stock'
    )
    list_filter = ('categoria', 'negocio')
    search_fields = ('nombre', 'negocio__nombre')
    raw_id_fields = ('negocio',)

    def estado_stock(self, obj):
        # Usamos format_html para inyectar CSS seguro en el panel
        if obj.stock_disponible == 0:
            return format_html('<span style="color: red; font-weight: bold;">AGOTADO</span>')
        elif obj.stock_disponible < 5:
            return format_html('<span style="color: orange; font-weight: bold;">BAJO ({})</span>', obj.stock_disponible)
        return format_html('<span style="color: green;">OK</span>')
    
    # CORRECCIÓN: short_description en inglés
    estado_stock.short_description = 'Estado Stock'

@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'centro_latitud', 'centro_longitud')
    # Nota: También agregué la coma aquí por buenas prácticas
    search_fields = ('nombre',) 

@admin.register(TipoVehiculo)
class TipoVehiculoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'radio_maximo_km', 'activo')
    # CORRECCIÓN FATAL: La coma es obligatoria en tuplas de 1 elemento
    list_filter = ('activo',)