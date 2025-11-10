# apps/payments/apps.py 
from django.apps import AppConfig 
 
class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = "Paiements et Factures"

    def ready(self):
        """Importer les signals lors du démarrage de l'application"""
        import apps.payments.signals 
