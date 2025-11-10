# apps/dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # === VUES PRINCIPALES ===
    path('', views.DashboardView.as_view(), name='index'),
    path('properties/', views.PropertiesOverviewView.as_view(), name='properties_overview'),
    path('financial/', views.FinancialOverviewView.as_view(), name='financial_overview'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('enregistrements/', views.enregistrements_view, name='enregistrements'),
    
    # Centre de documents
    path('documents/', views.documents_center, name='documents'),
    
    # === VUES HIÉRARCHIQUES RÉSIDENCES/APPARTEMENTS ===
    path('residences/', views.ResidencesListView.as_view(), name='residences_list'),
    path('residences/<int:residence_id>/', views.ResidenceDetailView.as_view(), name='residence_detail'),
    path('appartements/', views.PropertiesOverviewView.as_view(), name='appartements_list'),
    
    # === VUE OBSOLÈTE (gardée pour compatibilité - redirige vers employees) ===
    path('tasks-interventions/', views.tasks_interventions_unified_view, name='tasks_interventions'),
    
    # === APIs POUR STATISTIQUES ET DONNÉES EN TEMPS RÉEL ===
    path('api/stats/', views.dashboard_stats_api, name='stats_api'),
    path('api/revenue/', views.dashboard_revenue_api, name='revenue_api'),
    path('api/weather/', views.dashboard_weather_api, name='weather_api'),
    path('api/alerts/', views.dashboard_alerts_api, name='alerts_api'),
    
    # === APIs POUR LES FORMULAIRES MODAUX ===
    path('api/landlords/', views.get_landlords_for_property, name='landlords_api'),
    path('api/residences-by-landlord/<int:landlord_id>/', views.get_residences_by_landlord, name='residences_by_landlord_api'),
    path('api/appartements-by-residence/<int:residence_id>/', views.get_appartements_by_residence, name='appartements_by_residence_api'),
    path('api/properties-all/', views.get_all_properties, name='properties_all_api'),
    path('api/appartements-all/', views.get_all_appartements, name='appartements_all_api'),
    path('api/technicians/', views.get_technicians_api, name='technicians_api'),
    path('api/tenants/', views.get_tenants_api, name='tenants_api'),
    path('api/appartement/<str:appartement_id>/info/', views.get_appartement_info_api, name='appartement_info_api'),
    
    # === DASHBOARDS SPÉCIALISÉS ===
    path('manager/', views.manager_dashboard_view, name='manager_dashboard'),
    path('accountant/', views.accountant_dashboard_view, name='accountant_dashboard'),
    path('employee/', views.employee_dashboard_redirect, name='employee_dashboard'),
    
    # === ACTIONS RAPIDES ===
    path('api/quick-action/', views.dashboard_quick_action, name='quick_action'),
    
    # === APIs POUR GESTION HIÉRARCHIQUE ===
    path('api/residence/<int:residence_id>/stats/', views.residence_stats_api, name='residence_stats_api'),
    path('api/appartement/<int:appartement_id>/status/', views.update_appartement_status, name='update_appartement_status'),
    path('api/residences/stats/', views.residences_dashboard_stats, name='residences_dashboard_stats'),
    
    # === VUES D'ENREGISTREMENT ===
    path('nouveau/bien/', views.nouveau_bien, name='nouveau_bien'),
    path('nouveau/appartement/', views.nouveau_bien, name='nouveau_appartement'),
    path('nouveau/residence/', views.nouvelle_residence, name='nouvelle_residence'),
    path('nouveau/locataire/', views.nouveau_locataire, name='nouveau_locataire'),
    path('nouveau/bailleur/', views.nouveau_bailleur, name='nouveau_bailleur'),
    path('nouveau/contrat/', views.nouveau_contrat, name='nouveau_contrat'),
    path('nouveau/tache/', views.nouvelle_tache, name='nouvelle_tache'),
    path('nouveau/employe/', views.nouvel_employe, name='nouvel_employe'),
    path('nouveau/intervention/', views.nouvelle_intervention, name='nouvelle_intervention'),
    path('nouveau/paiement/', views.nouveau_paiement, name='nouveau_paiement'),
    
    # === APIs POUR LES EMPLOYÉS ===
    path('api/employee/<int:employee_id>/availability/', views.get_employee_availability, name='employee_availability'),
    path('api/task/quick-add/', views.quick_add_task_ajax, name='quick_add_task_ajax'),
    path('api/recent-activities/', views.recent_activities_api, name='recent_activities_api'),

    # === AJOUTS RAPIDES VIA MODALS ===
    path('quick/property/', views.quick_add_property, name='quick_add_property'),
    path('quick/landlord/', views.quick_add_landlord, name='quick_add_landlord'),
    path('quick/task/', views.quick_add_task, name='quick_add_task'),
    path('quick/residence/', views.quick_add_residence, name='quick_add_residence'),
    path('quick/appartement/', views.quick_add_appartement, name='quick_add_appartement'),
    
    # === ACTIONS TÂCHES (Redirections vers employees) ===
    path('tasks/<int:task_id>/start/', views.task_start_action, name='task_start'),
    path('tasks/<int:task_id>/complete/', views.task_complete_action, name='task_complete'),
    path('tasks/<int:task_id>/pause/', views.task_pause_action, name='task_pause'),
    path('tasks/<int:task_id>/cancel/', views.task_cancel_action, name='task_cancel'),
    
    # === GESTION DES MÉDIAS ===
    path('upload-media/', views.upload_media_ajax, name='upload_media'),
    path('delete-media/<int:media_id>/', views.delete_media_ajax, name='delete_media'),
    
    # === EXPORTS ET RAPPORTS ===
    path('export/residences/', views.export_residences, name='export_residences'),
    path('export/appartements/', views.export_appartements, name='export_appartements'),
    path('rapport/occupation/', views.rapport_occupation, name='rapport_occupation'),
]