"""
Señales de sesión para repartidores.

Regla de negocio: un repartidor solo debe recibir pedidos cuando está
trabajando de forma activa. Por eso, tanto al INICIAR como al CERRAR
sesión se le coloca automáticamente en descanso (``disponible=False``),
de modo que la asignación automática no le adjudique pedidos si no está
atendiendo la app. El repartidor vuelve a "activo" manualmente desde su
panel cuando empieza su turno.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in)
@receiver(user_logged_out)
def poner_repartidor_en_descanso(sender, request, user, **kwargs):
    # user_logged_out puede llegar con user=None (sesión anónima).
    if user is None or not getattr(user, "es_repartidor", False):
        return

    # Import diferido: evita importar la app delivery al cargar accounts.
    from apps.delivery.application.services import RepartidorService

    repartidor = RepartidorService.obtener_repartidor_de_usuario(user)
    # Solo escribe si hace falta (ya en descanso => nada que hacer).
    if repartidor is None or not repartidor.disponible:
        return

    RepartidorService.actualizar_disponibilidad(repartidor.id, disponible=False)
