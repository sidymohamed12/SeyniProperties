# apps/employees/views_redirects.py
"""
Vues de redirection pour backward compatibility
Redirection des anciennes URLs Task/Intervention vers le modèle Travail unifié
"""

from django.shortcuts import redirect
from django.contrib import messages


# === REDIRECTIONS TASK → TRAVAIL ===

def task_detail_redirect(request, task_id):
    """Redirige /tasks/<id>/ vers /travaux/<id>/"""
    messages.info(request, "Les tâches ont été migrées vers le système de travaux unifié.")
    return redirect('employees_mobile:travail_detail', travail_id=task_id)


def task_start_redirect(request, task_id):
    """Redirige /tasks/<id>/start/ vers /travaux/<id>/start/"""
    return redirect('employees_mobile:travail_start', travail_id=task_id)


def task_complete_redirect(request, task_id):
    """Redirige /tasks/<id>/complete/ vers /travaux/<id>/complete/"""
    return redirect('employees_mobile:travail_complete', travail_id=task_id)


def my_tasks_redirect(request):
    """Redirige /tasks/ vers /travaux/"""
    messages.info(request, "Les tâches ont été migrées vers le système de travaux unifié.")
    return redirect('employees_mobile:travaux_list')


# === REDIRECTIONS INTERVENTION → TRAVAIL ===

def intervention_detail_redirect(request, intervention_id):
    """Redirige /interventions/<id>/ vers /travaux/<id>/"""
    messages.info(request, "Les interventions ont été migrées vers le système de travaux unifié.")
    return redirect('employees_mobile:travail_detail', travail_id=intervention_id)


def intervention_start_redirect(request, intervention_id):
    """Redirige /interventions/<id>/start/ vers /travaux/<id>/start/"""
    return redirect('employees_mobile:travail_start', travail_id=intervention_id)


def intervention_complete_redirect(request, intervention_id):
    """Redirige /interventions/<id>/complete/ vers /travaux/<id>/complete/"""
    return redirect('employees_mobile:travail_complete', travail_id=intervention_id)


def my_interventions_redirect(request):
    """Redirige /interventions/ vers /travaux/"""
    messages.info(request, "Les interventions ont été migrées vers le système de travaux unifié.")
    return redirect('employees_mobile:travaux_list')
