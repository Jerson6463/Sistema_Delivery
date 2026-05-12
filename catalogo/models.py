from django.db import models
from django.core.validators import MinValueValidator
from core.choices import CategoriaNegocio, CategoriaProducto
from django.conf import settings
from django.utils import timezone
from datetime import datetime
# Create your models here.

class Negocio(models.Model):
    propietario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='negocio',
        limit_choices_to={'rol': 'ADMIN'}
    )
    nombre = models.CharField(
        max_length=150
    )

    categoria = models.CharField(
        choices=CategoriaNegocio.choices,
        default=CategoriaNegocio.RESTAURANTE
    )

    direccion = models.CharField(
        max_length=255
    )

    #Requisito: Horario en formato Json para flexibilidad
    horario = models.JSONField(
        default=dict
    )

    activo = models.BooleanField(
        default=True,
        db_index=True
    )

    calificacion_promedio = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    @property
    def esta_abierto(self):
        if not self.horario or not self.activo:
            return False
            
        # Diccionario para mapear los días en inglés de Django a español
        dias_espanol = {
            'monday': 'lunes', 'tuesday': 'martes', 'wednesday': 'miercoles',
            'thursday': 'jueves', 'friday': 'viernes', 'saturday': 'sabado', 'sunday': 'domingo'
        }
        
        # Obtener el día actual en español
        dia_actual_ingles = timezone.now().strftime('%A').lower()
        dia_actual_espanol = dias_espanol.get(dia_actual_ingles)

        horario_hoy = self.horario.get(dia_actual_espanol)
        
        # Si no hay horario definido para hoy o dice 'cerrado'
        if not horario_hoy:
            return False

        try:
            # Separar la hora de apertura y cierre (ej. "08:00-22:00")
            apertura_str = horario_hoy[0]
            cierre_str = horario_hoy[1]
            hora_actual = timezone.now().time()
            
            apertura = datetime.strptime(apertura_str.strip(), '%H:%M').time()
            cierre = datetime.strptime(cierre_str.strip(), '%H:%M').time()
            
            return apertura <= hora_actual <= cierre
        except (IndexError, TypeError, ValueError):
            # Si el JSON tiene un formato inválido por alguna razón, por seguridad marcamos cerrado
            return False

    class Meta:
        db_table = 'negocios'
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name='productos'
    )

    nombre = models.CharField(
        max_length=150
    )

    precio = models.DecimalField(
        max_digits= 5,
        decimal_places=2
    )
    
    categoria = models.CharField(
        choices=CategoriaProducto.choices,
        default=CategoriaProducto.ENTRADA
    )

    #Regla: no puede pedir si stock = 0
    stock_disponible = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    #Imagen del negocio
    imagen = models.ImageField(
        upload_to='productos/',
        null=True,
        blank=True
    )

    @property
    def disponible(self):
        """Calcula en tiempo real si el producto se puede comprar."""
        return self.stock_disponible > 0

    class Meta:
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f"{self.nombre} - {self.negocio.nombre}"

class Zona(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    #Coordenadas centrales de la zona para los calculos de distancia futuros
    centro_latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    centro_longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'zonas_cobertura'
        verbose_name = 'Zona de Cobertura'
        verbose_name_plural = 'Zonas de Cobertura'

    def __str__(self):
        return self.nombre

class TipoVehiculo(models.Model):
    nombre = models.CharField(
        max_length=50,
        unique=True
    )
    radio_maximo_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Radio maximo de entrega permitido en kilometros"
    )
    activo = models.BooleanField(
        default=True
    )

    class Meta:
        db_table = 'tipos_vehiculo'
        verbose_name = 'Tipo de Vehiculo'
        verbose_name_plural = 'Tipos de Vehiculo'

    def __str__(self):
        return f"{self.nombre} (Max: {self.radio_maximo_km}km)"

