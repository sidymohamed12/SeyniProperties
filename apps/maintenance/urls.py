# apps/maintenance/urls.py
from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    # === VUE PRINCIPALE ===
    path('', views.TravauxListView.as_view(), name='index'),

    # === LISTE ET FILTRES ===
    path('travaux/', views.TravauxListView.as_view(), name='travail_list'),
    path('interventions/', views.TravauxListView.as_view(), name='interventions_list'),  # Alias de compatibilité
    path('pending/', views.TravauxListView.as_view(), {'status': 'signale'}, name='pending_interventions'),
    path('urgent/', views.TravauxListView.as_view(), {'priority': 'urgente'}, name='urgent_interventions'),

    # === CRUD TRAVAUX (NOUVEAU SYSTÈME) ===
    path('travaux/create/', views.TravailCreateView.as_view(), name='travail_create'),
    path('travaux/<int:travail_id>/', views.travail_detail_view, name='travail_detail'),
    path('travaux/<int:travail_id>/edit/', views.TravailUpdateView.as_view(), name='travail_edit'),
    path('travaux/<int:travail_id>/delete/', views.travail_delete_view, name='travail_delete'),

    # === CRUD INTERVENTIONS (ANCIEN - Alias de compatibilité) ===
    path('create/', views.TravailCreateView.as_view(), name='intervention_create'),
    path('<int:travail_id>/', views.travail_detail_view, name='intervention_detail'),
    path('<int:travail_id>/edit/', views.TravailUpdateView.as_view(), name='intervention_edit'),
    path('<int:travail_id>/delete/', views.travail_delete_view, name='intervention_delete'),

    # === ACTIONS SUR TRAVAUX ===
    path('travaux/<int:travail_id>/assign/', views.travail_assign_view, name='travail_assign'),
    path('travaux/<int:travail_id>/start/', views.travail_start_view, name='travail_start'),
    path('travaux/<int:travail_id>/complete/', views.travail_complete_view, name='travail_complete'),

    # Alias de compatibilité
    path('<int:travail_id>/assign/', views.travail_assign_view, name='intervention_assign'),
    path('<int:travail_id>/start/', views.travail_start_view, name='intervention_start'),
    path('<int:travail_id>/complete/', views.travail_complete_view, name='intervention_complete'),

    # === INTERFACE EMPLOYÉ (Mobile Checklist) ===
    path('travaux/<int:travail_id>/checklist/', views.travail_checklist_view, name='travail_checklist'),
    path('<int:travail_id>/checklist/', views.travail_checklist_view, name='intervention_checklist'),  # Alias

    # === UPLOAD DE MÉDIAS ===
    path('travaux/<int:travail_id>/upload/', views.travail_upload_media_view, name='travail_upload_media'),
    path('<int:travail_id>/upload/', views.travail_upload_media_view, name='intervention_upload_media'),  # Alias

    # === APIs ===
    path('api/stats/', views.travaux_stats_api, name='travaux_stats_api'),
    path('api/stats/', views.travaux_stats_api, name='interventions_stats_api'),  # Alias
    path('api/calendar/', views.travail_calendar_api, name='travail_calendar_api'),
    path('api/calendar/', views.travail_calendar_api, name='intervention_calendar_api'),  # Alias

    # === RECHERCHE ET EXPORT ===
    path('search/', views.travaux_search, name='travaux_search'),
    path('export/', views.travaux_export, name='travaux_export'),
    path('bulk-action/', views.travaux_bulk_action, name='travaux_bulk_action'),

    # === MES TRAVAUX (pour employés) ===
    path('mes-travaux/', views.mes_travaux_view, name='mes_travaux'),
]
