# apps/contracts/views/__init__.py
"""
Vues du module contracts - Architecture modulaire

Ce fichier centralise les imports pour maintenir la rétrocompatibilité.
Les imports depuis l'ancien emplacement continuent de fonctionner:
    from apps.contracts.views import contract_list_view, PMODashboardView
"""

# Contract CRUD views
from .contract_views import (
    contract_list_view,
    contract_detail_view,
    contract_create_view,
    contract_edit_view,
    contract_delete_view,
    contract_renew_view,
    contract_terminate_view,
    contract_download_pdf,
    contract_preview_pdf,
    contract_print_view,
)

# Contract API endpoints
from .contract_api import (
    get_appartement_info,
    get_locataire_info,
    validate_contract_dates,
    contract_api_list,
    contract_stats_api,
    get_contract_info_api,
)

# Contract reports
from .contract_reports import (
    contracts_statistics_view,
    contracts_expiring_report,
    contracts_revenue_report,
    export_contracts_csv,
)

# PMO workflow views
from .pmo_views import (
    workflow_create_view,
    workflow_edit_view,
    workflow_delete_view,
    PMODashboardView,
    WorkflowDetailView,
    upload_document,
    valider_document,
    refuser_document,
    supprimer_document,
    upload_contrat_signe,
    planifier_visite,
    upload_etat_lieux,
    remise_cles,
    passer_etape_suivante,
    envoyer_finance,
    ajouter_notes,
)

# PMO API
from .pmo_api import (
    workflow_stats_api,
)

__all__ = [
    # Contract CRUD
    'contract_list_view',
    'contract_detail_view',
    'contract_create_view',
    'contract_edit_view',
    'contract_delete_view',
    'contract_renew_view',
    'contract_terminate_view',
    'contract_download_pdf',
    'contract_preview_pdf',
    'contract_print_view',

    # Contract API
    'get_appartement_info',
    'get_locataire_info',
    'validate_contract_dates',
    'contract_api_list',
    'contract_stats_api',
    'get_contract_info_api',

    # Contract reports
    'contracts_statistics_view',
    'contracts_expiring_report',
    'contracts_revenue_report',
    'export_contracts_csv',

    # PMO workflow
    'workflow_create_view',
    'workflow_edit_view',
    'workflow_delete_view',
    'PMODashboardView',
    'WorkflowDetailView',
    'upload_document',
    'valider_document',
    'refuser_document',
    'supprimer_document',
    'upload_contrat_signe',
    'planifier_visite',
    'upload_etat_lieux',
    'remise_cles',
    'passer_etape_suivante',
    'envoyer_finance',
    'ajouter_notes',

    # PMO API
    'workflow_stats_api',
]
