from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cliente, Repartidor

@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informacion de Rol', {'fields':('rol',)}),
    )

    list_display = (
        'username',
        'email',
        'rol',
        'is_staff',
        'is_active'
    )

    list_filter = (
        'rol',
        'is_staff',
        'is_active'
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'telefono',
        'direccion_principal'
    )

    search_fields = (
        'usuario__username',
        'usuario__email',
        'telefono'
    )

    raw_id_fields = (
        'usuario',
    )

@admin.register(Repartidor)
class RepartidorAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'tipo_vehiculo',
        'zona_cobertura'
    )

    search_fields = (
        'usuario__username',
        'usuario__email'
    )

    raw_id_fields = (
        'usuario',
    )

    readonly_fields = (
        'calificacion',
        'ultima_latitud',
        'ultima_longitud'
    )