#!/usr/bin/env python
"""
Script pour corriger l'historique des migrations dans Railway
Résout le conflit: accounting.0002_initial appliqué avant tiers.0001_initial
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()

from django.db import connection

def fix_migration_history():
    """
    Corrige l'ordre des migrations dans django_migrations
    en s'assurant que tiers.0001_initial est marqué comme appliqué
    avant accounting.0002_initial
    """
    with connection.cursor() as cursor:
        print("🔍 Vérification de l'historique des migrations...")

        # Vérifier si tiers.0001_initial existe
        cursor.execute("""
            SELECT id, applied
            FROM django_migrations
            WHERE app = 'tiers' AND name = '0001_initial'
        """)
        tiers_migration = cursor.fetchone()

        # Vérifier accounting.0002_initial
        cursor.execute("""
            SELECT id, applied
            FROM django_migrations
            WHERE app = 'accounting' AND name = '0002_initial'
        """)
        accounting_migration = cursor.fetchone()

        if not tiers_migration:
            print("❌ Migration tiers.0001_initial n'existe pas dans la base")
            print("   Création de l'enregistrement...")

            # Insérer la migration tiers avec une date antérieure
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('tiers', '0001_initial', NOW() - INTERVAL '1 day')
            """)
            print("✅ Migration tiers.0001_initial enregistrée")

        elif accounting_migration and tiers_migration:
            tiers_id, tiers_date = tiers_migration
            acc_id, acc_date = accounting_migration

            print(f"   tiers.0001_initial: ID={tiers_id}, Applied={tiers_date}")
            print(f"   accounting.0002_initial: ID={acc_id}, Applied={acc_date}")

            # Si accounting est plus ancien, corriger la date de tiers
            if tiers_date > acc_date:
                print("⚠️  Ordre incorrect détecté!")
                print("   Correction de la date de tiers.0001_initial...")

                cursor.execute("""
                    UPDATE django_migrations
                    SET applied = %s - INTERVAL '1 hour'
                    WHERE app = 'tiers' AND name = '0001_initial'
                """, [acc_date])

                print("✅ Ordre corrigé: tiers.0001_initial est maintenant avant accounting.0002_initial")
            else:
                print("✅ Ordre correct: tiers.0001_initial est avant accounting.0002_initial")

        # Vérifier les autres migrations tiers
        cursor.execute("""
            SELECT name FROM django_migrations
            WHERE app = 'tiers'
            ORDER BY applied
        """)
        tiers_migrations = cursor.fetchall()

        if not tiers_migrations or len(tiers_migrations) == 0:
            print("\n📝 Enregistrement de toutes les migrations tiers...")
            tiers_migration_files = [
                '0001_initial',
                '0002_ficherenseignement',
                '0003_tiers_compte_active_tiers_date_creation_compte_and_more'
            ]

            for i, migration_name in enumerate(tiers_migration_files):
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('tiers', %s, NOW() - INTERVAL '%s days')
                    ON CONFLICT DO NOTHING
                """, [migration_name, len(tiers_migration_files) - i])
                print(f"   ✓ {migration_name}")

        print("\n✅ Historique des migrations corrigé!")

if __name__ == '__main__':
    try:
        fix_migration_history()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
