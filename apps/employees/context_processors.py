# apps/employees/context_processors.py
from django.conf import settings

def mobile_context(request):
    """Context processor pour ajouter des variables mobile globales"""
    
    # Détecter si c'est un appareil mobile
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_mobile = any(agent in user_agent for agent in [
        'mobile', 'android', 'iphone', 'ipad', 'windows phone'
    ])
    
    # Informations PWA
    pwa_info = {
        'name': 'Seyni Employés',
        'short_name': 'Seyni Emp',
        'theme_color': '#23456b',
        'background_color': '#ffffff',
        'start_url': '/employees/mobile/',
        'scope': '/employees/',
        'display': 'standalone'
    }
    
    return {
        'is_mobile': is_mobile,
        'is_pwa': request.GET.get('pwa') == '1',
        'pwa_info': pwa_info,
        'app_version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'support_phone': getattr(settings, 'SUPPORT_PHONE', '+221 XX XXX XX XX'),
    }
