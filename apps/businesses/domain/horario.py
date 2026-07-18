"""
Lógica de horario (Python puro, sin Django).

El horario se guarda como JSON con esta forma (claves SIN tildes para
evitar problemas de codificación):

    {
      "lunes":   {"abierto": true,  "inicio": "08:00", "fin": "22:00"},
      "martes":  {"abierto": true,  "inicio": "08:00", "fin": "22:00"},
      ...
      "domingo": {"abierto": false, "inicio": null,    "fin": null}
    }

Una ventana puede cruzar la medianoche: si `fin <= inicio` (p. ej.
18:00 -> 02:00), se interpreta como horario nocturno que cierra en la
madrugada del día siguiente. Esa franja de madrugada "pertenece" al día
de apertura: marcar el viernes con 18:00-02:00 abre el viernes por la
noche y el sábado de 00:00 a 02:00, aunque el sábado esté cerrado.
"""
from datetime import datetime

# Índice según datetime.weekday(): 0 = lunes ... 6 = domingo
DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def horario_por_defecto() -> dict:
    """Horario base: L-S 08:00-22:00, domingo cerrado."""
    base = {
        dia: {"abierto": True, "inicio": "08:00", "fin": "22:00"}
        for dia in DIAS[:6]
    }
    base["domingo"] = {"abierto": False, "inicio": None, "fin": None}
    return base


def _a_hora(valor):
    if not valor:
        return None
    return datetime.strptime(valor, "%H:%M").time()


def _es_nocturna(inicio, fin) -> bool:
    """La ventana cruza la medianoche cuando cierra antes (o igual) de abrir."""
    return fin <= inicio


def _abierto_ese_dia(config_dia, hora) -> bool:
    """Tramo del propio día de apertura (noche incluida si es nocturna)."""
    if not config_dia or not config_dia.get("abierto"):
        return False
    inicio = _a_hora(config_dia.get("inicio"))
    fin = _a_hora(config_dia.get("fin"))
    if inicio is None or fin is None:
        return False
    if _es_nocturna(inicio, fin):
        return hora >= inicio          # tramo de la tarde/noche
    return inicio <= hora <= fin       # ventana normal dentro del mismo día


def _arrastre_de_ayer(config_ayer, hora) -> bool:
    """Tramo de madrugada que una ventana nocturna del día anterior arrastra."""
    if not config_ayer or not config_ayer.get("abierto"):
        return False
    inicio = _a_hora(config_ayer.get("inicio"))
    fin = _a_hora(config_ayer.get("fin"))
    if inicio is None or fin is None:
        return False
    return _es_nocturna(inicio, fin) and hora <= fin


def esta_abierto(horario: dict, momento: datetime) -> bool:
    """Devuelve True si el negocio está abierto en `momento` según su horario."""
    if not horario:
        return False

    hora = momento.time()
    dia = momento.weekday()
    hoy = horario.get(DIAS[dia])
    ayer = horario.get(DIAS[(dia - 1) % 7])
    return _abierto_ese_dia(hoy, hora) or _arrastre_de_ayer(ayer, hora)