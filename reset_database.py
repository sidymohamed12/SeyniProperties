#!/usr/bin/env python
"""
Script pour réinitialiser complètement la base de données Railway
Supprime toutes les tables et repart de zéro
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()

from django.db import connection

def reset_database():
    """
    Supprime toutes les tables de la base de données
    """
    with connection.cursor() as cursor:
        print("🚨 ATTENTION: Réinitialisation complète de la base de données")
        print("")

        # Get all tables
        cursor.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()

        if not tables:
            print("✅ Aucune table à supprimer")
            return

        print(f"📋 {len(tables)} tables trouvées:")
        for table in tables:
            print(f"   - {table[0]}")

        print("")
        print("🗑️  Suppression de toutes les tables...")

        # Drop all tables
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")
        cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;")

        connection.commit()

        print("✅ Base de données réinitialisée avec succès!")
        print("")
        print("Prochaines étapes:")
        print("1. Les migrations seront appliquées au démarrage")
        print("2. Un nouveau superuser sera créé:")
        print("   - Username: Admin")
        print("   - Password: Admin0000")

if __name__ == '__main__':
    try:
        reset_database()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
