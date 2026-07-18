from django.conf import settings
from django.db import models

from apps.businesses.models import Zona
from apps.shared.models import BaseModel


class Repartidor(BaseModel):
    """
    Perfil de repartidor (OneToOne con el usuario).

    Alcance académico: cada repartidor cubre UNA zona general (FK simple),
    de modo que atiende todos los distritos de esa zona. La
    aprobación se controla con usuario.aprobado (el mismo flag que habilita
    el login); `disponible` es su interruptor de turno (activo/en descanso).
    """

    class Vehiculo(models.TextChoices):
        MOTO = "MOTO", "Moto"
        BICICLETA = "BICICLETA", "Bicicleta"
        AUTO = "AUTO", "Auto"
        A_PIE = "A_PIE", "A pie"

    # PROTECT y no CASCADE: `User` no hereda BaseModel, así que su `delete()`
    # es físico y arrastraría el perfil del repartidor. Para dar de baja a un
    # repartidor se usa `is_active=False` (ver AccountService.rechazar_usuario).
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="repartidor",
    )
    zona_cobertura = models.ForeignKey(
        Zona, on_delete=models.PROTECT, related_name="repartidores"
    )
    vehiculo = models.CharField(
        max_length=20, choices=Vehiculo.choices, default=Vehiculo.MOTO
    )
    disponible = models.BooleanField(default=True)
    calificacion_promedio = models.DecimalField(
        max_digits=3, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "Repartidor"
        verbose_name_plural = "Repartidores"

    def __str__(self):
        nombre = self.usuario.get_full_name() or self.usuario.username
        return f"{nombre} ({self.get_vehiculo_display()})"
    
class SeguimientoEntrega(models.Model):
    """
    Punto GPS reportado por el repartidor durante una entrega EN_CAMINO.
    El tracking muestra la ÚLTIMA ubicación (la más reciente por timestamp).
    """
    pedido = models.ForeignKey(
        "orders.Pedido", on_delete=models.CASCADE, related_name="ubicaciones"
    )
    repartidor = models.ForeignKey(
        Repartidor, on_delete=models.CASCADE, related_name="ubicaciones"
    )
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Seguimiento de entrega"
        verbose_name_plural = "Seguimientos de entrega"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Pedido #{self.pedido_id} @ ({self.latitud}, {self.longitud})"
