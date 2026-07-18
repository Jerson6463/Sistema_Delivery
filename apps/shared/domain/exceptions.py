"""
Excepciones de dominio (Python puro, sin Django).

Se lanzan desde los servicios cuando se viola una regla de negocio y
se capturan en la capa de entrada (API / vistas web) para devolver un
error limpio al usuario. Fase 11 conecta esto con un handler de DRF.
"""


class DomainException(Exception):
    """Excepción base de todas las reglas de negocio."""
    codigo = "ERROR_DOMINIO"
    default_message = "Error de dominio"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


class NegocioCerradoException(DomainException):
    codigo = "NEGOCIO_CERRADO"
    default_message = "El negocio está cerrado en este momento."


class StockInsuficienteException(DomainException):
    codigo = "STOCK_INSUFICIENTE"
    default_message = "No hay stock suficiente para el pedido."


class TransicionEstadoInvalidaException(DomainException):
    codigo = "TRANSICION_INVALIDA"
    default_message = "La transición de estado no está permitida."


class PermisoDominioException(DomainException):
    codigo = "PERMISO_DENEGADO"
    default_message = "No tienes permiso para realizar esta acción."


class PedidoNoCancelableException(DomainException):
    codigo = "PEDIDO_NO_CANCELABLE"
    default_message = "El pedido no se puede cancelar en su estado actual."


class RepartidorNoDisponibleException(DomainException):
    codigo = "REPARTIDOR_NO_DISPONIBLE"
    default_message = "No hay repartidor disponible en la zona."


class CalificacionDuplicadaException(DomainException):
    codigo = "CALIFICACION_DUPLICADA"
    default_message = "El pedido ya fue calificado."


class PedidoNoEntregadoException(DomainException):
    codigo = "PEDIDO_NO_ENTREGADO"
    default_message = "Solo se puede calificar un pedido entregado."


class ZonaNoDisponibleException(DomainException):
    codigo = "ZONA_NO_DISPONIBLE"
    default_message = "El negocio no cubre la zona de entrega seleccionada."