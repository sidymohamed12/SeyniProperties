"""
Script de migration des donnees Intervention vers Travail
A executer une seule fois pour migrer les interventions existantes
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()

from apps.maintenance.models.intervention import Intervention
from apps.maintenance.models.travail import Travail
from django.db import transaction

def migrate_interventions_to_travail():
    """Migre toutes les interventions existantes vers le modele Travail unifie"""

    interventions = Intervention.objects.all()
    count = interventions.count()

    if count == 0:
        print("[OK] Aucune intervention a migrer")
        return

    print(f"[INFO] {count} intervention(s) trouvee(s) a migrer")

    migrated = 0
    errors = 0

    with transaction.atomic():
        for intervention in interventions:
            try:
                # Mapper les champs de Intervention vers Travail
                travail_data = {
                    # Identification
                    'numero_travail': intervention.numero_intervention,
                    'titre': intervention.titre,
                    'description': intervention.description or '',

                    # Caracteristiques
                    'nature': 'reactif',  # Les interventions sont reactives par defaut
                    'type_travail': intervention.type_intervention,
                    'priorite': intervention.priorite,

                    # Localisation
                    'appartement': intervention.appartement,

                    # Assignation
                    'assigne_a': intervention.technicien,

                    # Dates
                    'date_signalement': intervention.date_signalement,
                    'date_prevue': intervention.date_planifiee if hasattr(intervention, 'date_planifiee') else None,
                    'date_debut': intervention.date_debut if hasattr(intervention, 'date_debut') else None,
                    'date_fin': intervention.date_fin if hasattr(intervention, 'date_fin') else None,

                    # Statut
                    'statut': intervention.statut,

                    # Couts
                    'cout_estime': intervention.cout_estime if hasattr(intervention, 'cout_estime') else None,
                    'cout_reel': intervention.cout_final if hasattr(intervention, 'cout_final') else None,

                    # Timestamps
                    'created_at': intervention.created_at,
                    'updated_at': intervention.updated_at,
                }

                # Creer le nouveau Travail
                travail = Travail.objects.create(**travail_data)

                print(f"  [OK] Migre: {intervention.numero_intervention} -> {travail.numero_travail}")
                migrated += 1

            except Exception as e:
                print(f"  [ERROR] Erreur pour {intervention.numero_intervention}: {e}")
                errors += 1

    print(f"\n[RESULTATS]")
    print(f"  Migres: {migrated}")
    print(f"  Erreurs: {errors}")
    print(f"  Total: {count}")

    if migrated > 0:
        print(f"\n[ATTENTION]")
        print(f"  - Les {migrated} interventions ont ete copiees vers la table Travail")
        print(f"  - Les anciennes donnees Intervention existent toujours")
        print(f"  - Apres verification, vous pouvez supprimer les anciennes donnees")

if __name__ == '__main__':
    print("="*60)
    print("MIGRATION INTERVENTION -> TRAVAIL")
    print("="*60)

    response = input("\nCette operation va copier les Interventions vers Travail. Continuer? (oui/non): ")

    if response.lower() in ['oui', 'yes', 'o', 'y']:
        migrate_interventions_to_travail()
    else:
        print("[ANNULE] Migration annulee")
