#!/bin/bash
# deploy.sh - Script de déploiement Railway

set -e  # Arrêter en cas d'erreur

echo "🚀 Début du déploiement"

# Vérification de l'environnement
echo "📝 Variables d'environnement:"
echo "DATABASE_URL présent: $([[ -n "$DATABASE_URL" ]] && echo "✅ OUI" || echo "❌ NON")"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"

# Test de connexion DB
echo "🔌 Test de connexion à la base de données..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Connexion DB OK')
except Exception as e:
    print(f'❌ Erreur DB: {e}')
    exit(1)
"

# Vérification Django
echo "🔧 Vérification de la configuration Django..."
python manage.py check --verbosity=2

# Création des migrations
echo "📋 Génération des migrations..."
python manage.py makemigrations --verbosity=2

# Application des migrations
echo "🔄 Application des migrations..."
python manage.py migrate --verbosity=2

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --verbosity=2

# Création d'un superuser si nécessaire
echo "👤 Vérification du superuser..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()

# Vérifier s'il existe déjà un superuser
if User.objects.filter(is_superuser=True).exists():
    print('✅ Superuser existe déjà')
else:
    # Créer un superuser avec des variables d'environnement ou des valeurs par défaut
    username = os.environ.get('SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('SUPERUSER_EMAIL', 'admin@seyniproperties.com')
    password = os.environ.get('SUPERUSER_PASSWORD', 'admin123456')
    
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        user_type='manager'
    )
    print(f'✅ Superuser créé: {username} / {email}')
    print('🔐 Mot de passe par défaut: admin123456 (à changer!)')
"

echo "✅ Déploiement terminé avec succès!"

# Lancement du serveur
echo "🌐 Lancement du serveur..."
exec gunicorn seyni_properties.wsgi:application --bind 0.0.0.0:$PORT --log-level info