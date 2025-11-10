from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'  # ← IMPORTANT : doit être 'apps.core' et non 'core'
    verbose_name = 'Core'