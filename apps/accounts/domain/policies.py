"""
Políticas de la cuenta (Python puro, sin Django).

Reglas de negocio simples y testeables sin base de datos.
"""

# Roles que quedan aprobados apenas se registran.
ROLES_AUTOAPROBADOS = {"CLIENTE", "ADMIN"}


def aprobacion_por_defecto(rol: str) -> bool:
    """
    Devuelve el valor inicial de `aprobado` según el rol.

    Cliente y Admin -> True (entran de inmediato).
    Negocio y Repartidor -> False (quedan pendientes de aprobación).
    """
    return rol in ROLES_AUTOAPROBADOS