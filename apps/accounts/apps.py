from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        # Registra las señales de sesión (repartidor en descanso al
        # iniciar/cerrar sesión).
        from apps.accounts import signals  # noqa: F401
