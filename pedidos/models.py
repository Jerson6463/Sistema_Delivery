from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.choices import Estados
from usuarios.models import Cliente,Repartidor
from catalogo.models import Negocio, Producto

class Pedido(models.Model):

    #Relaciones: Usamos PROTECT para no perder el historial financiero
    #si un cliente o negocio se elimina
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )
    
    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )

    #El repartidor puede ser nulo al inicio, se asina despues
    repartidor = models.ForeignKey(
        Repartidor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos_asignados'
    )

    #Estado indexado para busquedas rapidas
    estado = models.CharField(
        choices=Estados.choices,
        default=Estados.RECIBIDO,
        db_index=True
    )

    #Totales financieros
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    costo_envio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    direccion_entrega = models.CharField(
        max_length=255
    )

    #Auditoria de tiempo
    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'pedidos'
        verbose_name = 'Pedidos'
        verbose_name_plural = 'Pedidos'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Pedido #{self.id} - {self.ger_estado}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )

    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        db_table = 'detalles_pedido'
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} (Pedido #{self.pedido_id})"