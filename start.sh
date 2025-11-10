#!/bin/bash
# start.sh - Script de démarrage Railway avec Dockerfile

set -e

echo "🚀 Démarrage de Seyni Properties"
echo "📊 Variables d'environnement:"
echo "   DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "   RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "   PORT: $PORT"

# Attendre que la base de données soit prête
echo "⏳ Test de connexion à la base de données..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os, django, psycopg2
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Base de données accessible')
    exit(0)
except Exception as e:
    print(f'❌ Tentative {attempt}/{max_attempts}: {e}')
    exit(1)
"; then
        echo "✅ Connexion DB établie"
        break
    else
        echo "⏳ Tentative $attempt/$max_attempts - Attente de la DB..."
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Impossible de se connecter à la base de données après $max_attempts tentatives"
    exit 1
fi

echo "🔧 Vérification de l'état de la base de données..."
# Check if database needs reset due to old schema incompatible with Tiers refactoring
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()
from django.db import connection

def table_exists(cursor, table_name):
    cursor.execute('''
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = %s
    ''', [table_name])
    return cursor.fetchone()[0] > 0

with connection.cursor() as cursor:
    has_tiers = table_exists(cursor, 'tiers_tiers')
    has_old_bailleur = table_exists(cursor, 'accounts_bailleur')
    has_old_locataire = table_exists(cursor, 'accounts_locataire')
    has_django_migrations = table_exists(cursor, 'django_migrations')

    if has_django_migrations and not has_tiers and (has_old_bailleur or has_old_locataire):
        print('🚨 ÉTAT CRITIQUE: Ancien schéma détecté (Bailleur/Locataire)')
        print('   La base doit être réinitialisée pour la refonte Tiers')
        print('')
        print('🗑️  Réinitialisation de la base de données...')

        # Drop all tables and recreate clean schema
        cursor.execute('DROP SCHEMA public CASCADE;')
        cursor.execute('CREATE SCHEMA public;')
        cursor.execute('GRANT ALL ON SCHEMA public TO postgres;')
        cursor.execute('GRANT ALL ON SCHEMA public TO public;')
        connection.commit()

        print('✅ Base de données réinitialisée')
        print('   Les migrations seront appliquées maintenant')
    elif has_tiers:
        print('✅ Base de données compatible avec architecture Tiers')
    else:
        print('✅ Nouvelle base de données - migrations seront appliquées')
" || echo "⚠️  Vérification ignorée"

echo "🔄 Génération des migrations..."
python manage.py makemigrations --noinput

echo "🔄 Application des migrations..."
python manage.py migrate --noinput

echo "👤 Création du superuser..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.environ.get('SUPERUSER_USERNAME', 'Admin'),
        email=os.environ.get('SUPERUSER_EMAIL', 'admin@seyniproperties.com'),
        password=os.environ.get('SUPERUSER_PASSWORD', 'Admin0000'),
        user_type='manager',
        first_name='Admin',
        last_name='System'
    )
    print('✅ Superuser créé: Admin / Admin0000')
else:
    print('✅ Superuser existe déjà')
"

echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "🌐 Démarrage du serveur sur le port $PORT..."
exec gunicorn seyni_properties.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info