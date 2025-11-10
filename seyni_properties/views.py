# seyni_properties/views.py - Vues globales pour healthcheck

from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
import sys


def health_check(request):
    """Vue de healthcheck pour Railway"""
    try:
        # Test de connexion à la base de données
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Test des applications critiques
        from django.apps import apps
        critical_apps = [
            'accounts', 'properties', 'dashboard', 
            'employees', 'maintenance'
        ]
        
        for app_name in critical_apps:
            if not apps.is_installed(f'apps.{app_name}'):
                return JsonResponse({
                    'status': 'error',
                    'message': f'App {app_name} not installed'
                }, status=503)
        
        return JsonResponse({
            'status': 'healthy',
            'version': '1.0.0',
            'django_version': sys.version,
            'database': 'connected',
            'debug': settings.DEBUG
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=503)


def root_redirect(request):
    """Redirection depuis la racine vers le login"""
    from django.shortcuts import redirect
    from django.contrib import messages
    
    if request.user.is_authenticated:
        # Rediriger selon le type d'utilisateur
        if request.user.user_type == 'manager':
            return redirect('dashboard:index')
        elif request.user.user_type in ['field_agent', 'technician', 'technicien', 'agent_terrain']:
            return redirect('employees_mobile:dashboard')
        else:
            return redirect('dashboard:index')
    else:
        messages.info(request, "Bienvenue sur Seyni Properties")
        return redirect('accounts:login')


def simple_health(request):
    """Healthcheck simple pour Railway"""
    return HttpResponse("OK", content_type="text/plain")