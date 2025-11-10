# apps/employees/mobile_urls.py

from django.urls import path
from . import views
from . import views_redirects  # Redirections pour backward compatibility


app_name = 'employees_mobile'

urlpatterns = [
    # === DASHBOARD MOBILE ===
    path('', views.employee_dashboard_mobile, name='dashboard'),
    path('dashboard/', views.employee_dashboard_mobile, name='dashboard_alt'),

    # === TRAVAUX MOBILE (NOUVEAU - MODÈLE UNIFIÉ) ===
    path('travaux/', views.my_tasks_mobile, name='travaux_list'),
    path('travaux/<int:travail_id>/', views.travail_detail_mobile, name='travail_detail'),
    path('travaux/<int:travail_id>/start/', views.travail_start_mobile, name='travail_start'),
    path('travaux/<int:travail_id>/complete/', views.travail_complete_mobile, name='travail_complete'),
    path('travaux/<int:travail_id>/checklist/<int:checklist_id>/toggle/', views.travail_checklist_toggle, name='travail_checklist_toggle'),
    path('travaux/<int:travail_id>/demande-materiel/', views.travail_demande_materiel, name='travail_demande_materiel'),
    path('demandes/<int:demande_id>/confirmer-reception/', views.confirmer_reception_materiel, name='confirmer_reception_materiel'),

    # === TÂCHES MOBILE (DEPRECATED - Redirige vers travaux) ===
    path('tasks/', views_redirects.my_tasks_redirect, name='tasks'),
    path('tasks/<int:task_id>/', views_redirects.task_detail_redirect, name='task_detail'),
    path('tasks/<int:task_id>/start/', views_redirects.task_start_redirect, name='task_start'),
    path('tasks/<int:task_id>/complete/', views_redirects.task_complete_redirect, name='task_complete'),

    # === INTERVENTIONS MOBILE (DEPRECATED - Redirige vers travaux) ===
    path('interventions/', views_redirects.my_interventions_redirect, name='interventions'),
    path('interventions/<int:intervention_id>/', views_redirects.intervention_detail_redirect, name='intervention_detail'),
    path('interventions/<int:intervention_id>/start/', views_redirects.intervention_start_redirect, name='intervention_start'),
    path('interventions/<int:intervention_id>/complete/', views_redirects.intervention_complete_redirect, name='intervention_complete'),

    # === PLANNING MOBILE ===
    path('schedule/', views.my_schedule_mobile, name='schedule'),

    # === PROFIL ET SÉCURITÉ ===
    path('profil/', views.employee_profile_mobile, name='profil'),
    path('change-password-required/', views.change_password_required_mobile, name='change_password_required'),

    # === UPLOAD ET RAPPORTS MOBILE ===
    path('upload/<str:item_type>/<int:item_id>/', views.upload_media_mobile, name='upload_media'),
    path('report/<str:item_type>/<int:item_id>/', views.quick_report_mobile, name='quick_report'),

    # === PWA ===
    path('manifest.json', views.pwa_manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
]