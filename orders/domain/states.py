"""
Estados del pedido (Python puro, sin Django).

En la Fase 4 solo se usa el enum de estados y su default (RECIBIDO).
La máquina de transiciones (qué estado puede pasar a cuál y quién puede
hacerlo) se agrega en la Fase 5, en este mismo módulo.
"""


class Estado:
    RECIBIDO = "RECIBIDO"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO_PARA_RECOJO = "LISTO_PARA_RECOJO"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"

    CHOICES = [
        (RECIBIDO, "Recibido"),
        (CONFIRMADO, "Confirmado"),
        (EN_PREPARACION, "En preparación"),
        (LISTO_PARA_RECOJO, "Listo para recojo"),
        (EN_CAMINO, "En camino"),
        (ENTREGADO, "Entregado"),
        (CANCELADO, "Cancelado"),
    ]

    # Estados finales: el pedido ya no cambia y no admite seguimiento activo.
    FINALES = {ENTREGADO, CANCELADO}


def es_estado_final(estado: str) -> bool:
    return estado in Estado.FINALES

TRANSICIONES = {
    Estado.RECIBIDO: {Estado.CONFIRMADO, Estado.CANCELADO},
    Estado.CONFIRMADO: {Estado.EN_PREPARACION, Estado.CANCELADO},
    Estado.EN_PREPARACION: {Estado.LISTO_PARA_RECOJO},
    Estado.LISTO_PARA_RECOJO: {Estado.EN_CAMINO},
    Estado.EN_CAMINO: {Estado.ENTREGADO},
    Estado.ENTREGADO: set(),   # estado final
    Estado.CANCELADO: set(),   # estado final
}
 
 
def transicion_valida(actual: str, nuevo: str) -> bool:
    return nuevo in TRANSICIONES.get(actual, set())