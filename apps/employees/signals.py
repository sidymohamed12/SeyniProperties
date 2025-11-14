# apps/employees/signals.py
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.employees.models.employee import Employee
from apps.employees.models.task import Task
from apps.maintenance.models.intervention import Intervention

@receiver(post_save, sender=Task)
def invalidate_task_cache(sender, instance, **kwargs):
    """Invalide le cache quand une tâche est modifiée"""
    cache_keys = [
        f'user_tasks_{instance.assigne_a.id}',
        f'user_stats_{instance.assigne_a.id}',
        'global_task_stats'
    ]
    cache.delete_many(cache_keys)

@receiver(post_save, sender=Intervention)
def invalidate_intervention_cache(sender, instance, **kwargs):
    """Invalide le cache quand une intervention est modifiée"""
    if instance.technicien:
        cache_keys = [
            f'user_interventions_{instance.technicien.id}',
            f'user_stats_{instance.technicien.id}',
            'global_intervention_stats'
        ]
        cache.delete_many(cache_keys)

@receiver(post_save, sender=Employee)
def update_employee_cache(sender, instance, **kwargs):
    """Met à jour le cache des employés"""
    cache.delete('active_employees')
    cache.delete(f'employee_profile_{instance.user.id}')
