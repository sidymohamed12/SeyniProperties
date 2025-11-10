# settings/mobile.py - Configuration spécifique mobile
MOBILE_SETTINGS = {
    # PWA Configuration
    'PWA_MANIFEST': {
        'name': 'Seyni Properties - Employés',
        'short_name': 'Seyni Employés',
        'description': 'Application mobile pour les employés de Seyni Properties',
        'theme_color': '#23456b',
        'background_color': '#ffffff',
        'display': 'standalone',
        'orientation': 'portrait-primary',
        'start_url': '/employees/mobile/',
        'scope': '/employees/',
        'icons': [
            {
                'src': '/static/img/icons/icon-192x192.png',
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any maskable'
            },
            {
                'src': '/static/img/icons/icon-512x512.png',
                'sizes': '512x512',
                'type': 'image/png'
            }
        ],
        'shortcuts': [
            {
                'name': 'Mes tâches',
                'short_name': 'Tâches',
                'description': 'Voir mes tâches du jour',
                'url': '/employees/mobile/tasks/',
                'icons': [{'src': '/static/img/icons/tasks-96x96.png', 'sizes': '96x96'}]
            },
            {
                'name': 'Interventions',
                'short_name': 'Interventions',
                'description': 'Mes interventions assignées',
                'url': '/employees/mobile/interventions/',
                'icons': [{'src': '/static/img/icons/tools-96x96.png', 'sizes': '96x96'}]
            }
        ]
    },
    
    # Upload Configuration
    'MAX_PHOTO_SIZE': 10 * 1024 * 1024,  # 10MB
    'MAX_AUDIO_SIZE': 25 * 1024 * 1024,  # 25MB
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/png', 'image/webp'],
    'ALLOWED_AUDIO_TYPES': ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/webm'],
    
    # Cache Configuration
    'CACHE_TIMEOUT': {
        'tasks': 300,  # 5 minutes
        'stats': 600,  # 10 minutes
        'schedule': 900,  # 15 minutes
    },
    
    # Notification Configuration
    'PUSH_NOTIFICATIONS': {
        'enabled': True,
        'vapid_public_key': 'YOUR_VAPID_PUBLIC_KEY',
        'vapid_private_key': 'YOUR_VAPID_PRIVATE_KEY',
        'vapid_subject': 'mailto:admin@seyniproperties.com'
    },
    
    # Offline Configuration
    'OFFLINE_CACHE': {
        'version': '1.0.0',
        'cache_name': 'seyni-employees-v1',
        'cache_urls': [
            '/employees/mobile/',
            '/employees/mobile/tasks/',
            '/employees/mobile/schedule/',
            '/static/css/mobile.css',
            '/static/js/mobile.js',
            '/static/img/icons/',
        ]
    }
}

# Ajouter aux settings principaux
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'seyni_mobile',
        'TIMEOUT': 300,
    }
}

# Configuration des sessions pour mobile
SESSION_COOKIE_AGE = 86400 * 7  # 7 jours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

