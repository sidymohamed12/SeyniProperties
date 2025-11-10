# apps/contracts/apps.py
from django.apps import AppConfig

class ContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contracts'

    def ready(self):
        """Import signals when app is ready"""
        import apps.contracts.signals 
