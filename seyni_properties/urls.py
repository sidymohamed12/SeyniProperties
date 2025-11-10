# seyni_properties/urls.py - URLs principales avec healthcheck

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from . import views  # Import des vues healthcheck

def home_view(request):
    """Page d'accueil avec formulaire de connexion"""
    # Si l'utilisateur est déjà connecté, le rediriger vers son dashboard
    if request.user.is_authenticated:
        if request.user.user_type == 'manager':
            from django.shortcuts import redirect
            return redirect('dashboard:manager_dashboard')
        elif request.user.user_type == 'accountant':
            from django.shortcuts import redirect
            return redirect('dashboard:accountant_dashboard')
        elif request.user.user_type in ['agent_terrain', 'technicien', 'field_agent', 'technician']:
            from django.shortcuts import redirect
            return redirect('employees:index')  # ✅ CORRECTION: Utiliser l'URL qui existe
        elif request.user.user_type == 'tenant':
            from django.shortcuts import redirect
            return redirect('portals:tenant_portal')
        elif request.user.user_type == 'landlord':
            from django.shortcuts import redirect
            return redirect('portals:landlord_portal')
    
    return render(request, 'home.html')

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),
    
    # Healthcheck pour Railway
    path('health/', views.health_check, name='health_check'),
    
    # Applications principales
    path('dashboard/', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('properties/', include('apps.properties.urls')),
    path('contracts/', include('apps.contracts.urls')),
    path('payments/', include('apps.payments.urls')),
    path('maintenance/', include('apps.maintenance.urls')),
    path('employees/', include('apps.employees.urls')),
    path('employees/mobile/', include('apps.employees.mobile_urls')),
    path('accounting/', include('apps.accounting.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('portals/', include('apps.portals.urls')),
    path('tiers/', include('apps.tiers.urls')),
    path('syndic/', include('apps.syndic.urls')),
    path('api/', include('apps.api.urls')),
    
    # Page d'accueil (connexion)
    path('', home_view, name='home'),
]

# ✅ MEDIA FILES EN DÉVELOPPEMENT
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)