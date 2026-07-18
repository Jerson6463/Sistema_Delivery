from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username", "first_name", "last_name", "email", "rol", "aprobado",
        "is_active", "is_staff",
    )
    list_filter = ("rol", "aprobado", "is_active")
    # Añade rol/aprobado a los fieldsets del UserAdmin estándar
    fieldsets = UserAdmin.fieldsets + (
        ("Rol y aprobación", {"fields": ("rol", "aprobado")}),
    )
