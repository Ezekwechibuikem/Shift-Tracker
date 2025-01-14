from django.apps import AppConfig


class FlowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flow'

    def ready(self):
        from . import signals
        signals_module = signals