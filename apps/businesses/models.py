from django.conf import settings
from django.db import models

from apps.businesses.domain.horario import horario_por_defecto
from apps.shared.models import BaseModel


class Zona(BaseModel):
    """
    Zona general de cobertura (Centro, Norte, Sur, Este, Oeste).

    Se registra UNA sola vez y agrupa varios distritos (ZonaEntrega). El
    nombre no se repite: es único. `activo` permite desactivarla sin borrarla.
    """

    # No se puede borrar (ni lógicamente) una zona que aún tenga distritos o
    # repartidores vivos: quedarían apuntando a una zona invisible. Sus
    # `on_delete=PROTECT` no bastan, porque el soft delete es un UPDATE.
    proteger_si_hay = ("distritos", "repartidores")

    # La unicidad se condiciona a `activo=True` (soft delete): un registro
    # borrado lógicamente no debe bloquear la creación de uno nuevo.
    nombre = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["nombre"],
                condition=models.Q(activo=True),
                name="unique_zona_nombre_activa",
            ),
        ]

    def __str__(self):
        return self.nombre


class ZonaEntrega(BaseModel):
    """
    Distrito de cobertura para el envío, perteneciente a una zona general.

    Varios distritos pueden pertenecer a la misma `Zona`; el par
    (zona, distrito) es único para no duplicar un distrito dentro de la
    misma zona. En formularios y selects se muestra solo el distrito.
    """

    # Negocios, tarifas y clientes vivos bloquean el borrado del distrito.
    # `pedidos` NO se incluye a propósito pese a ser PROTECT: es histórico y
    # el soft delete ya lo conserva; incluirlo impediría retirar para siempre
    # cualquier distrito que haya tenido un pedido.
    # Ojo con `clientes`: User no hereda BaseModel, así que cuentan también
    # los dados de baja con is_active=False.
    proteger_si_hay = ("negocios", "tarifas", "clientes")

    zona = models.ForeignKey(
        Zona,
        on_delete=models.PROTECT,
        related_name="distritos",
        help_text="Zona general a la que pertenece el distrito.",
    )
    distrito = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Distrito de entrega"
        verbose_name_plural = "Distritos de entrega"
        ordering = ["zona__nombre", "distrito"]
        constraints = [
            models.UniqueConstraint(
                fields=["zona", "distrito"],
                condition=models.Q(activo=True),
                name="unique_distrito_por_zona",
            ),
        ]

    def __str__(self):
        return self.distrito


class Negocio(BaseModel):
    """
    Negocio con un único usuario dueño/administrador (OneToOne).

    `aprobado` controla la visibilidad pública del negocio; se activa
    cuando el administrador lo aprueba (Fase 10). El `horario_json` guarda
    el horario por día y se interpreta con domain/horario.py.
    """

    class Categoria(models.TextChoices):
        COMIDA = "COMIDA", "Comida"
        FARMACIA = "FARMACIA", "Farmacia"
        ABARROTES = "ABARROTES", "Abarrotes"
        BEBIDAS = "BEBIDAS", "Bebidas"
        OTROS = "OTROS", "Otros"

    # PROTECT y no CASCADE: `User` no hereda BaseModel, así que su `delete()`
    # es físico y arrastraría el negocio (y con él sus productos y tarifas),
    # justo lo que el soft delete existe para impedir. Para dar de baja a un
    # dueño se usa `is_active=False` (ver AccountService.rechazar_usuario).
    usuario_dueno = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="negocio",
    )
    nombre = models.CharField(max_length=150)
    categoria = models.CharField(
        max_length=20,
        choices=Categoria.choices,
        default=Categoria.COMIDA,
    )
    direccion = models.CharField(max_length=255)
    zona = models.ForeignKey(
        ZonaEntrega,
        on_delete=models.PROTECT,
        related_name="negocios",
        null=True,
        blank=True,
        help_text="",
    )
    horario_json = models.JSONField(default=horario_por_defecto, blank=True)
    imagen = models.ImageField(upload_to="negocios/", blank=True, null=True)
    calificacion_promedio = models.DecimalField(
        max_digits=3, decimal_places=2, default=0
    )
    aprobado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"

    def __str__(self):
        return self.nombre


class TarifaEnvio(BaseModel):
    """Costo de envío de un negocio hacia una zona concreta."""
    negocio = models.ForeignKey(
        Negocio, on_delete=models.CASCADE, related_name="tarifas"
    )
    zona_entrega = models.ForeignKey(
        ZonaEntrega, on_delete=models.PROTECT, related_name="tarifas"
    )
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Tarifa de envío"
        verbose_name_plural = "Tarifas de envío"
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "zona_entrega"],
                condition=models.Q(activo=True),
                name="unique_tarifa_negocio_zona",
            ),
            models.CheckConstraint(
                check=models.Q(costo__gte=0),
                name="tarifa_costo_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.negocio} -> {self.zona_entrega}: S/ {self.costo}"
