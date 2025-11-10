# apps/contracts/views/pmo_api.py
"""
API endpoints pour le module PMO (Project Management Office)
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ..models import ContractWorkflow


@login_required
def workflow_stats_api(request):
    """Retourne les statistiques du PMO en JSON"""
    stats = {
        'total': ContractWorkflow.objects.count(),
        'par_etape': {},
        'par_statut': {},
    }

    # Stats par étape
    for etape_code, etape_label in ContractWorkflow.ETAPE_CHOICES:
        stats['par_etape'][etape_code] = {
            'label': etape_label,
            'count': ContractWorkflow.objects.filter(etape_actuelle=etape_code).count()
        }

    # Stats par statut dossier
    for statut_code, statut_label in ContractWorkflow.STATUT_DOSSIER_CHOICES:
        stats['par_statut'][statut_code] = {
            'label': statut_label,
            'count': ContractWorkflow.objects.filter(statut_dossier=statut_code).count()
        }

    return JsonResponse(stats)
