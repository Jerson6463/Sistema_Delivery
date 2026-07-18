from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.businesses.models import Negocio
from apps.shared.models import BaseModel


class Producto(BaseModel):
    """
    Producto vendible por un negocio.

    Reglas:
    - `precio` siempre > 0 (DecimalField, nunca float).
    - `stock_disponible` nunca negativo (PositiveIntegerField + validación
      en el servicio al descontar).
    - Solo se muestran al público los productos con activo=True.
    """
    negocio = models.ForeignKey(
        Negocio, on_delete=models.CASCADE, related_name="productos"
    )
    nombre = models.CharField(max_length=150)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    categoria = models.CharField(max_length=50, blank=True)
    stock_disponible = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        constraints = [
            models.CheckConstraint(
                check=models.Q(precio__gt=0),
                name="producto_precio_positivo",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.negocio.nombre})"

    @property
    def agotado(self) -> bool:
        return self.stock_disponible == 0


class CategoriaProducto(BaseModel):
    """
    Categoría de producto propia de un negocio, reutilizable.

    Cada negocio tiene su propio catálogo de categorías: las de un negocio
    NO se muestran en otro. Se guardan de forma independiente al producto,
    para poder reutilizarlas aunque el producto que las estrenó ya no exista.

    La unicidad (negocio, nombre) se condiciona a `activo=True` (soft delete).
    El duplicado por mayúsculas/minúsculas o espacios se evita en el servicio
    (comparación `nombre__iexact` sobre el nombre ya normalizado).
    """
    negocio = models.ForeignKey(
        Negocio, on_delete=models.CASCADE, related_name="categorias_producto"
    )
    nombre = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Categoría de producto"
        verbose_name_plural = "Categorías de producto"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "nombre"],
                condition=models.Q(activo=True),
                name="unique_categoria_por_negocio",
            ),
        ]

    def __str__(self):
        return self.nombre