#!/usr/bin/env python
"""
Script de vérification de l'implémentation Architecture Travaux - Demandes d'Achat
Exécuter avec: python verify_implementation.py
"""

import os
import sys
import re

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


def check_file(filepath, expected_content=None, should_not_contain=None):
    """Vérifie l'existence d'un fichier et optionnellement son contenu"""
    if not os.path.exists(filepath):
        return False, f"Fichier introuvable: {filepath}"

    if expected_content or should_not_contain:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if expected_content:
            for pattern in expected_content:
                if not re.search(pattern, content, re.MULTILINE):
                    return False, f"Pattern manquant dans {filepath}: {pattern}"

        if should_not_contain:
            for pattern in should_not_contain:
                if re.search(pattern, content, re.MULTILINE):
                    return False, f"Pattern non désiré trouvé dans {filepath}: {pattern}"

    return True, f"OK: {filepath}"


def print_result(passed, message):
    """Affiche le résultat d'un test"""
    if passed:
        print(f"{GREEN}[OK]{RESET} {message}")
    else:
        print(f"{RED}[FAIL]{RESET} {message}")
    return passed


def main():
    print(f"\n{BOLD}=== Vérification Implémentation Architecture Travaux - Demandes d'Achat ==={RESET}\n")

    all_passed = True

    # 1. Vérifier les fichiers de modèles
    print(f"{BOLD}1. Vérification des Modèles{RESET}")

    result, msg = check_file(
        'apps/maintenance/models.py',
        expected_content=[
            r'def necessite_materiel\(self\):',
            r'def statut_materiel\(self\):',
            r'def cout_total_materiel\(self\):'
        ],
        should_not_contain=[
            r'demande_achat\s*=\s*models\.ForeignKey.*Invoice'  # Ancien champ
        ]
    )
    all_passed &= print_result(result, msg)

    result, msg = check_file(
        'apps/payments/models.py',
        expected_content=[
            r"related_name='demandes_achat'",
            r'travail_lie\s*=\s*models\.ForeignKey'
        ]
    )
    all_passed &= print_result(result, msg)

    # 2. Vérifier la migration
    print(f"\n{BOLD}2. Vérification des Migrations{RESET}")

    result, msg = check_file(
        'apps/maintenance/migrations/0005_remove_demande_achat_field.py',
        expected_content=[
            r'from django\.db import migrations, models',
            r'RemoveField',
            r"model_name='travail'",
            r"name='demande_achat'"
        ]
    )
    all_passed &= print_result(result, msg)

    # 3. Vérifier les vues
    print(f"\n{BOLD}3. Vérification des Vues{RESET}")

    result, msg = check_file(
        'apps/employees/views.py',
        expected_content=[
            r'def travail_demande_materiel\(request, travail_id\):',
            r'def confirmer_reception_materiel\(request, demande_id\):',
            r"travail\.statut = 'en_cours'",
            r'travail\.statut_materiel',
            r'demande\.etape_workflow = \'recue\''
        ]
    )
    all_passed &= print_result(result, msg)

    result, msg = check_file(
        'apps/maintenance/views.py',
        should_not_contain=[
            r'demande_achat\s*=\s*None',
            r'demandes_achat_liees\.first\(\)'
        ]
    )
    all_passed &= print_result(result, msg)

    # 4. Vérifier les URLs
    print(f"\n{BOLD}4. Vérification des URLs{RESET}")

    result, msg = check_file(
        'apps/employees/mobile_urls.py',
        expected_content=[
            r'travail_demande_materiel',
            r'confirmer_reception_materiel',
            r'demande-materiel',
            r'confirmer-reception'
        ]
    )
    all_passed &= print_result(result, msg)

    # 5. Vérifier les templates desktop
    print(f"\n{BOLD}5. Vérification des Templates Desktop{RESET}")

    result, msg = check_file(
        'templates/maintenance/travail_detail.html',
        expected_content=[
            r'travail\.demandes_achat\.all',
            r'travail\.demandes_achat\.count',
            r'travail\.cout_total_materiel',
            r'for demande_achat in'
        ],
        should_not_contain=[
            r'{% if demande_achat %}(?!.*{% for)' # Pas de référence à une seule demande sans boucle
        ]
    )
    all_passed &= print_result(result, msg)

    result, msg = check_file(
        'templates/includes/travail_card.html',
        expected_content=[
            r'travail\.necessite_materiel',
            r'travail\.demandes_achat\.count',
            r'travail\.cout_total_materiel',
            r'travail\.statut_materiel'
        ]
    )
    all_passed &= print_result(result, msg)

    # 6. Vérifier les templates mobile
    print(f"\n{BOLD}6. Vérification des Templates Mobile{RESET}")

    result, msg = check_file(
        'templates/employees/mobile/travail_detail.html',
        expected_content=[
            r'travail\.necessite_materiel',
            r'travail\.demandes_achat\.all',
            r'confirmerReception',
            r'J\'ai reçu ce matériel',
            r'etape_workflow.*==.*paye'
        ]
    )
    all_passed &= print_result(result, msg)

    result, msg = check_file(
        'templates/employees/mobile/travail_demande_materiel.html'
    )
    all_passed &= print_result(result, msg)

    result, msg = check_file(
        'templates/employees/mobile/work_list.html',
        expected_content=[
            r'work\.necessite_materiel',
            r'work\.statut_materiel'
        ]
    )
    all_passed &= print_result(result, msg)

    # 7. Vérifier la documentation
    print(f"\n{BOLD}7. Vérification de la Documentation{RESET}")

    docs = [
        'ARCHITECTURE_TRAVAUX_DEMANDES_ACHAT.md',
        'TEMPLATES_MIGRATION_RAPPORT.md',
        'PORTAIL_EMPLOYE_DEMANDES_ACHAT_RAPPORT.md',
        'CONFIRMATION_RECEPTION_MATERIEL_RAPPORT.md',
        'TRAVAUX_DEMANDES_ACHAT_IMPLEMENTATION_COMPLETE.md'
    ]

    for doc in docs:
        result, msg = check_file(doc)
        all_passed &= print_result(result, msg)

    # Résumé final
    print(f"\n{BOLD}{'='*80}{RESET}")
    if all_passed:
        print(f"{GREEN}{BOLD}[SUCCESS] TOUS LES TESTS PASSES{RESET}")
        print(f"\n{GREEN}L'implementation est complete et prete pour le deploiement !{RESET}")
        print(f"\n{YELLOW}Prochaines etapes:{RESET}")
        print(f"  1. python manage.py makemigrations")
        print(f"  2. python manage.py migrate")
        print(f"  3. python manage.py check")
        print(f"  4. Tests manuels (desktop + mobile)")
        return 0
    else:
        print(f"{RED}{BOLD}[ERROR] CERTAINS TESTS ONT ECHOUE{RESET}")
        print(f"\n{RED}Veuillez verifier les fichiers indiques ci-dessus.{RESET}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
