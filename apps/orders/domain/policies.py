"""
Actor permitido por transición (Python puro, sin Django).

Cada transición indica QUÉ TIPO de actor puede ejecutarla. La verificación
concreta (si este usuario es realmente el dueño del negocio, el cliente del
pedido o el repartidor asignado) se hace en el servicio, porque necesita
consultar la base de datos.
"""
from apps.orders.domain.states import Estado

# Categorías de actor
NEGOCIO = "NEGOCIO"
CLIENTE = "CLIENTE"
REPARTIDOR_ASIGNADO = "REPARTIDOR_ASIGNADO"

ACTORES_POR_TRANSICION = {
    (Estado.RECIBIDO, Estado.CONFIRMADO): {NEGOCIO},
    (Estado.RECIBIDO, Estado.CANCELADO): {CLIENTE, NEGOCIO},
    (Estado.CONFIRMADO, Estado.EN_PREPARACION): {NEGOCIO},
    (Estado.CONFIRMADO, Estado.CANCELADO): {CLIENTE, NEGOCIO},
    (Estado.EN_PREPARACION, Estado.LISTO_PARA_RECOJO): {NEGOCIO},
    (Estado.LISTO_PARA_RECOJO, Estado.EN_CAMINO): {REPARTIDOR_ASIGNADO},
    (Estado.EN_CAMINO, Estado.ENTREGADO): {REPARTIDOR_ASIGNADO},
}


def actores_permitidos(actual: str, nuevo: str) -> set:
    return ACTORES_POR_TRANSICION.get((actual, nuevo), set())