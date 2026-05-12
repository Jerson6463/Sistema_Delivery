from django.db import models
from pedidos.models import Pedido

# Create your models here.
class SeguimientoEntrega(models.Model):
    # Relacion con el pedido (usamos string para evitar conflictos)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='historial_ubicaciones'
    )

    #Mantenemos la precision estandar de gps
    latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )
    
    longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        db_table = 'seguimiento_entregas'
        verbose_name = 'Seguimiento de Entrega'
        verbose_name_plural = 'Seguimientos de Entregas'
        #Ordenar por el mas reciente por defecto ayuda al fronted a dibujar 
        #la ruta sin procesar datos
        ordering = ['-timestamp']

    def __str__(self):
        return f"Ubicacion Pedido #{self.pedido_id} a las {self.timestamp.strftime('%H:%M:%S')}"
