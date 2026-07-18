from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.businesses.models import Negocio, ZonaEntrega
from apps.catalog.models import Producto
from apps.orders.domain.states import Estado
from apps.shared.models import BaseModel


class Pedido(BaseModel):
    """
    Pedido de un cliente a un negocio.

    Guarda los montos ya calculados (subtotal, costo_envio, total) porque
    las tarifas y precios pueden cambiar después; el pedido conserva el
    valor histórico. El campo `repartidor` se agrega en la Fase 6.
    """

    class MetodoPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        YAPE_PLIN = "YAPE_PLIN", "Yape / Plin"
        TARJETA = "TARJETA", "Tarjeta"

    class CanceladoPor(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        NEGOCIO = "NEGOCIO", "Negocio"

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pedidos"
    )
    negocio = models.ForeignKey(
        Negocio, on_delete=models.PROTECT, related_name="pedidos"
    )
    repartidor = models.ForeignKey(
        "delivery.Repartidor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    estado = models.CharField(
        max_length=20, choices=Estado.CHOICES, default=Estado.RECIBIDO
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    direccion_entrega = models.CharField(max_length=255)
    zona_entrega = models.ForeignKey(
        ZonaEntrega, on_delete=models.PROTECT, related_name="pedidos"
    )
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices)

    # Cancelación (se usa en Fase 5)
    cancelado_por = models.CharField(
        max_length=20, choices=CanceladoPor.choices, null=True, blank=True
    )
    motivo_cancelacion = models.CharField(max_length=255, null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    # Entrega (se usa en Fase 7)
    entregado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-creado_en"]
        constraints = [
            # Un repartidor no puede tener dos pedidos activos asignados
            # al mismo tiempo (asignado en LISTO_PARA_RECOJO o EN_CAMINO).
            models.UniqueConstraint(
                fields=["repartidor"],
                condition=models.Q(
                    estado__in=[Estado.LISTO_PARA_RECOJO, Estado.EN_CAMINO],
                    repartidor__isnull=False,
                ),
                name="unique_repartidor_pedido_activo",
            ),
        ]

    def __str__(self):
        return f"Pedido #{self.pk} - {self.get_estado_display()}"


class DetallePedido(models.Model):
    """Línea de un pedido. Guarda el precio unitario al momento de la compra."""
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="detalles"
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


class Calificacion(BaseModel):
    """
    Calificación que el cliente hace de un pedido YA ENTREGADO.

    Un pedido se califica una sola vez (OneToOne) y en ese acto se valora,
    de forma independiente, al negocio y al repartidor. El negocio y el
    repartidor se desnormalizan aquí para que el recálculo del promedio sea
    estable aunque `pedido.repartidor` cambie (es SET_NULL). El puntaje del
    repartidor es opcional porque un pedido podría no tener repartidor.

    Las reglas (solo el cliente dueño, solo si está ENTREGADO, sin duplicar)
    se validan en CalificacionService, nunca en la vista.
    """

    PUNTAJE_MIN = 1
    PUNTAJE_MAX = 5
    _validadores = [
        MinValueValidator(PUNTAJE_MIN),
        MaxValueValidator(PUNTAJE_MAX),
    ]

    pedido = models.OneToOneField(
        Pedido, on_delete=models.CASCADE, related_name="calificacion"
    )
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="calificaciones",
    )
    negocio = models.ForeignKey(
        Negocio, on_delete=models.PROTECT, related_name="calificaciones"
    )
    repartidor = models.ForeignKey(
        "delivery.Repartidor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calificaciones",
    )
    puntaje_negocio = models.PositiveSmallIntegerField(validators=_validadores)
    puntaje_repartidor = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=_validadores
    )
    comentario_negocio = models.CharField(max_length=255, blank=True)
    comentario_repartidor = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        ordering = ["-creado_en"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(puntaje_negocio__gte=1, puntaje_negocio__lte=5),
                name="calificacion_puntaje_negocio_rango",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(puntaje_repartidor__isnull=True)
                    | models.Q(puntaje_repartidor__gte=1, puntaje_repartidor__lte=5)
                ),
                name="calificacion_puntaje_repartidor_rango",
            ),
        ]

    def __str__(self):
        return f"Calificación del pedido #{self.pedido_id}"


class HistorialEstadoPedido(models.Model):
    """
    Registro (append-only) de cada cambio de estado del pedido.
    Es la base del timeline del tracking (Fase 8). No se edita ni se borra.
    """
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="historial"
    )
    estado_anterior = models.CharField(max_length=20, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cambios_estado",
    )
    comentario = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en"]

    def __str__(self):
        return f"Pedido #{self.pedido_id}: {self.estado_anterior} -> {self.estado_nuevo}"