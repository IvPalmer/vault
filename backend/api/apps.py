from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Vault API'

    def ready(self):
        from api.signals import connect_signals
        connect_signals()
