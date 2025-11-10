# apps/employees/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
import re

class MobileRedirectMiddleware(MiddlewareMixin):
    """Middleware pour rediriger les employés vers l'interface mobile"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.mobile_user_agents = [
            'Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone',
            'BlackBerry', 'Opera Mini', 'IEMobile'
        ]
        
    def process_request(self, request):
        # Vérifier si l'utilisateur est connecté et est un employé
        if (request.user.is_authenticated and 
            request.user.user_type in ['agent_terrain', 'technicien']):
            
            # Vérifier si c'est un appareil mobile
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            is_mobile = any(agent in user_agent for agent in self.mobile_user_agents)
            
            # URLs à exclure de la redirection
            excluded_paths = [
                '/employees/mobile/',
                '/api/',
                '/admin/',
                '/static/',
                '/media/'
            ]
            
            if (is_mobile and 
                not any(request.path.startswith(path) for path in excluded_paths) and
                not request.GET.get('desktop')):  # Paramètre pour forcer la version desktop
                
                # Rediriger vers l'interface mobile
                if request.path == '/employees/' or request.path.startswith('/employees/tasks'):
                    return redirect('employees:employee_dashboard_mobile')

        return None


class TemporaryPasswordMiddleware(MiddlewareMixin):
    """
    Middleware qui vérifie si l'utilisateur connecté a un mot de passe temporaire.
    Si oui, le redirige vers la page de changement de mot de passe obligatoire.
    """

    def process_request(self, request):
        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Vérifier si l'utilisateur a un mot de passe temporaire
            if hasattr(request.user, 'mot_de_passe_temporaire') and request.user.mot_de_passe_temporaire:
                # URLs à exclure de la vérification
                exempt_paths = [
                    '/accounts/login/',
                    '/accounts/logout/',
                    '/employees/mobile/change-password-required/',
                    '/admin/',
                    '/static/',
                    '/media/',
                ]

                current_path = request.path

                # Vérifier si on n'est pas déjà sur une page exemptée
                is_exempt = any(current_path.startswith(exempt) for exempt in exempt_paths)

                if not is_exempt:
                    # Rediriger vers la page de changement de mot de passe
                    return redirect('employees_mobile:change_password_required')

        return None

