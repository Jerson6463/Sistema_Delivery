from django.db import models

class Roles (models.TextChoices):
    ADMIN = 'ADMIN', 'Adminitrador/Negocio'
    CLIENTE = 'CLIENTE', 'Cliente'
    REPARTIDOR = 'REPARTIDOR', 'Repartidor'

class ZonasCobertura(models.TextChoices):
    CHICLAYO_CENTRO = 'CHICLAYO_CENTRO', 'Chiclayo'
    LA_VICTORIA = 'LA_VICTORIA', 'La Victoria'
    JLO = 'JLO', 'Jose Leonardo Ortiz'
    PIMENTEL = 'PIMENTEL', 'Pimentel'

class CategoriaNegocio(models.TextChoices):
    RESTAURANTE = 'RESTAURANTE', 'Restaurante'
    POLLERIA = 'POLLERIA', 'Pollería'
    CHIFA = 'CHIFA', 'Chifa'
    PIZZERIA = 'PIZZERIA', 'Pizzería'
    CEVICHERIA = 'CEVICHERIA', 'Cevichería'
    PANADERIA = 'PANADERIA', 'Panadería'
    FARMACIA = 'FARMACIA', 'Farmacia'
    SUPERMERCADO = 'SUPERMERCADO', 'Supermercado'
    LICORERIA = 'LICORERIA', 'Licorería'
    HELADERIA = 'HELADERIA', 'Heladería'
    PASTELERIA = 'PASTELERIA', 'Pastelería'

class CategoriaProducto(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada'
    PLATO_FUERTE = 'PLATO_FUERTE', 'Plato Fuerte'
    BEBIDA = 'BEBIDA', 'Bebida'
    POSTRE = 'POSTRE', 'Postre'

class Estados(models.TextChoices):
    RECIBIDO = 'RECIBIDO', 'Recibido'
    CONFIRMADO = 'CONFIRMADO', 'Confirmado'
    EN_PREPARACION = 'EN_PREPARACION', 'En Preparacion'
    LISTO_PARA_RECOJO = 'LISTO_PARA_RECOJO', 'Listo para Recojo'
    EN_CAMINO = 'EN_CAMINO', 'En Camino'
    ENTREGADO = 'ENTREGADO', 'Entregado'
    CANCELADO = 'CANCELADO', 'Cancelado'


