from django.db import models
from django.contrib.auth.models import AbstractUser
from catalogo.models import TipoVehiculo, Zona
from core.choices import Roles

# Create your models here.

class Usuario(AbstractUser):
    # modelo de usuario
    
    rol = models.CharField(
        choices=Roles.choices,
        default=Roles.CLIENTE
    )

    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_custom_set',  # Nombre único para evitar el choque
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_custom_permissions_set', # Nombre único para evitar el choque
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.username

class Cliente(models.Model):
    # Perfil extendido para clientes
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_cliente'
    )

    direccion_principal = models.CharField(
        max_length=255
    )

    telefono=models.CharField(
        max_length=9
    )

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"Cliente: {self.usuario.get_full_name() or self.usuario.username}"
    
class Repartidor(models.Model):

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_repartidor'
    )

    tipo_vehiculo = models.ForeignKey(
        'catalogo.TipoVehiculo',
        on_delete = models.RESTRICT,
        related_name = 'repartidores',
    )

    zona_cobertura = models.ForeignKey(
        'catalogo.Zona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    disponible = models.BooleanField(
        default=False,
        db_index=True
    )

    calificacion = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00
    )

    ultima_latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    ultima_longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'repartidores'
        verbose_name = 'Repartidor'
        verbose_name_plural = 'Repartidores'

    def __str__(self):
        return f"Repartidor: {self.usuario.get_full_name() or self.usuario.username}"