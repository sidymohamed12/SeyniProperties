# apps/contracts/urls.py - Architecture modulaire

from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    # URLs principales
    path('', views.contract_list_view, name='list'),
    path('create/', views.contract_create_view, name='create'),
    path('<int:pk>/', views.contract_detail_view, name='detail'),
    path('<int:pk>/edit/', views.contract_edit_view, name='edit'),
    path('<int:pk>/delete/', views.contract_delete_view, name='delete'),
    
    # Actions sur contrats
    path('<int:pk>/renew/', views.contract_renew_view, name='renew'),
    path('<int:pk>/terminate/', views.contract_terminate_view, name='terminate'),
    path('<int:pk>/pdf/', views.contract_download_pdf, name='download_pdf'),
    path('<int:pk>/pdf/preview/', views.contract_preview_pdf, name='preview_pdf'),
    
    # Statistiques et rapports
    path('statistics/', views.contracts_statistics_view, name='statistics'),
    path('reports/expiring/', views.contracts_expiring_report, name='expiring_report'),
    path('reports/revenue/', views.contracts_revenue_report, name='revenue_report'),
    
    # Export
    path('export/csv/', views.export_contracts_csv, name='export_csv'),
    
    # API/AJAX
    path('api/appartement-info/', views.get_appartement_info, name='appartement_info'),
    path('api/locataire-info/', views.get_locataire_info, name='locataire_info'),
    path('api/validate-dates/', views.validate_contract_dates, name='validate_dates'),
    path('api/<int:pk>/info/', views.get_contract_info_api, name='contract_info_api'),

    # ============================================================================
    # URLs PMO (Project Management Office)
    # ============================================================================

    # Dashboard PMO
    path('pmo/', views.PMODashboardView.as_view(), name='pmo_dashboard'),

    # Création workflow
    path('pmo/workflow/create/', views.workflow_create_view, name='pmo_workflow_create'),

    # Détail workflow
    path('pmo/workflow/<int:workflow_id>/', views.WorkflowDetailView.as_view(), name='pmo_workflow_detail'),

    # Modification et suppression workflow
    path('pmo/workflow/<int:workflow_id>/edit/', views.workflow_edit_view, name='pmo_workflow_edit'),
    path('pmo/workflow/<int:workflow_id>/delete/', views.workflow_delete_view, name='pmo_workflow_delete'),

    # Gestion documents
    path('pmo/workflow/<int:workflow_id>/documents/upload/', views.upload_document, name='pmo_upload_document'),
    path('pmo/workflow/<int:workflow_id>/documents/<int:document_id>/upload/', views.upload_document, name='pmo_upload_document_existing'),
    path('pmo/workflow/<int:workflow_id>/documents/<int:document_id>/supprimer/', views.supprimer_document, name='pmo_supprimer_document'),
    path('pmo/documents/<int:document_id>/valider/', views.valider_document, name='pmo_valider_document'),
    path('pmo/documents/<int:document_id>/refuser/', views.refuser_document, name='pmo_refuser_document'),

    # Rédaction et signature du contrat
    path('pmo/workflow/<int:workflow_id>/contrat/upload/', views.upload_contrat_signe, name='pmo_upload_contrat'),

    # Visite et état des lieux
    path('pmo/workflow/<int:workflow_id>/visite/planifier/', views.planifier_visite, name='pmo_planifier_visite'),
    path('pmo/workflow/<int:workflow_id>/etat-lieux/upload/', views.upload_etat_lieux, name='pmo_upload_etat_lieux'),

    # Remise des clés
    path('pmo/workflow/<int:workflow_id>/cles/remise/', views.remise_cles, name='pmo_remise_cles'),

    # Actions workflow
    path('pmo/workflow/<int:workflow_id>/passer-etape/', views.passer_etape_suivante, name='pmo_passer_etape'),
    path('pmo/workflow/<int:workflow_id>/envoyer-finance/', views.envoyer_finance, name='pmo_envoyer_finance'),
    path('pmo/workflow/<int:workflow_id>/notes/', views.ajouter_notes, name='pmo_ajouter_notes'),

    # API PMO
    path('pmo/api/stats/', views.workflow_stats_api, name='pmo_stats_api'),

]