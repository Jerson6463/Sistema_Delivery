from django.contrib import admin

from apps.shared.admin import SoftDeleteAdminMixin

from .models import CategoriaProducto, Producto


@admin.register(Producto)
class ProductoAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "negocio", "precio", "stock_disponible", "activo")
    list_filter = ("negocio", "activo")
    search_fields = ("nombre",)


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "negocio", "activo")
    list_filter = ("negocio", "activo")
    search_fields = ("nombre", "negocio__nombre")