# apps/employees/urls.py
from django.urls import path, include
from . import views

app_name = 'employees'

urlpatterns = [
    # ✅ ROUTES PRINCIPALES QUI EXISTENT
    path('', views.employees_list_view, name='index'),
    path('tasks/', views.TasksListView.as_view(), name='tasks'),
    
    # ✅ GESTION DES TÂCHES (vues qui existent dans employees)
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:task_id>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:task_id>/delete/', views.task_delete_view, name='task_delete'),
    path('tasks/<int:task_id>/start/', views.task_start, name='task_start'),
    path('tasks/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    
    # ✅ PLANNING ET STATS (vues qui existent dans employees)
    path('planning/', views.planning_view, name='planning'),
    path('api/calendar/', views.tasks_calendar_api, name='calendar_api'),
    path('api/stats/', views.task_stats_api, name='stats_api'),
    
    # ✅ EMPLOYÉS (vues qui existent dans employees)
    path('employee/create/', views.employee_create_view, name='employee_create'),
    path('employee/<int:employee_id>/', views.employee_detail_view, name='employee_detail'),
    
    # ✅ VUE DASHBOARD MOBILE (cette vue existe dans employees/views.py)
    path('dashboard/', views.employee_dashboard_mobile, name='employee_dashboard_mobile'),
    
    # ✅ VUES QUI EXISTENT DANS DASHBOARD - Redirection ou proxy
    # Ces vues sont dans apps.dashboard.views, donc on peut soit :
    # 1. Les importer depuis dashboard
    # 2. Créer des proxies
    # 3. Les commenter pour l'instant
    
    # Commentées pour éviter les erreurs en attendant la mise à jour
    # path('api/availability/<int:employee_id>/', views.get_employee_availability, name='employee_availability'),
    # path('api/sync-data/', views.get_employee_sync_data, name='sync_data'),
]