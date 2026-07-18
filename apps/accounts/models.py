from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario del proyecto con rol y estado de aprobación.

    - Cliente y Admin quedan aprobados automáticamente.
    - Negocio y Repartidor se registran pero quedan PENDIENTES hasta que
      un administrador los apruebe (ver AccountService y las políticas
      en domain/policies.py).
    """

    class Rol(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        NEGOCIO = "NEGOCIO", "Negocio"
        REPARTIDOR = "REPARTIDOR", "Repartidor"
        ADMIN = "ADMIN", "Administrador"

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )
    aprobado = models.BooleanField(default=True)

    # Dirección de entrega del cliente. Se pide en el registro y se usa como
    # valor por defecto al crear un pedido. El pedido guarda su propia copia
    # histórica en Pedido.direccion_entrega, así que cambiar esto no altera
    # pedidos ya realizados.
    direccion = models.CharField(max_length=255, blank=True, default="")

    # Distrito del cliente (ZonaEntrega). Su zona general determina qué
    # negocios ve en su panel. Se guarda como relación, no como texto.
    # Referencia por string para evitar un import circular con businesses.
    zona_entrega = models.ForeignKey(
        "businesses.ZonaEntrega",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="clientes",
        help_text="Distrito del cliente; su zona determina los negocios visibles.",
    )

    # --- Helpers de rol (evitan comparar strings sueltos en las vistas) ---
    @property
    def es_cliente(self) -> bool:
        return self.rol == self.Rol.CLIENTE

    @property
    def es_negocio(self) -> bool:
        return self.rol == self.Rol.NEGOCIO

    @property
    def es_repartidor(self) -> bool:
        return self.rol == self.Rol.REPARTIDOR

    @property
    def es_admin(self) -> bool:
        return self.rol == self.Rol.ADMIN or self.is_superuser

    @property
    def tiene_direccion(self) -> bool:
        return bool((self.direccion or "").strip())

    @property
    def zona_general(self):
        """Zona general del cliente (a partir de su distrito), o None."""
        return self.zona_entrega.zona if self.zona_entrega_id else None