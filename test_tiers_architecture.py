#!/usr/bin/env python
"""
Script de test pour valider l'architecture Tiers
Phase 2 : Tests et Validation
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seyni_properties.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.tiers.models import Tiers
from apps.properties.models import Residence, Appartement
from apps.contracts.models import RentalContract
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_success(message):
    """Affiche un message de succès"""
    print(f"✅ {message}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"❌ {message}")

def print_info(message):
    """Affiche une information"""
    print(f"ℹ️  {message}")


def test_1_tiers_proprietaire():
    """Test 1 : Créer des Tiers propriétaires"""
    print_section("TEST 1 : Création de Tiers Propriétaires")

    try:
        # Propriétaire 1 : Particulier AVEC compte utilisateur
        user1 = User.objects.create_user(
            username='amad.diop',
            email='amad.diop@example.com',
            password='test123',
            first_name='Amad',
            last_name='Diop',
            user_type='landlord'
        )

        proprietaire1 = Tiers.objects.create(
            nom='Diop',
            prenom='Amad',
            email='amad.diop@example.com',
            telephone='+221771234567',
            type_tiers='proprietaire',
            statut='actif',
            user=user1,  # Compte utilisateur lié
            type_bailleur='particulier',
            adresse='Rue 10, Almadies',
            ville='Dakar'
        )
        print_success(f"Propriétaire créé : {proprietaire1.nom_complet}")
        print_info(f"  → Avec compte utilisateur : {proprietaire1.has_user_account}")
        print_info(f"  → Email : {proprietaire1.email}")
        print_info(f"  → Téléphone : {proprietaire1.telephone}")

        # Propriétaire 2 : Société SANS compte utilisateur
        proprietaire2 = Tiers.objects.create(
            nom='Sarr',
            prenom='Fatou',
            email='contact@immosenegal.sn',
            telephone='+221775555555',
            type_tiers='proprietaire',
            statut='actif',
            user=None,  # Pas de compte utilisateur
            type_bailleur='societe',
            entreprise='Immo Sénégal SARL',
            numero_siret='SN123456789',
            adresse='Avenue Cheikh Anta Diop',
            ville='Dakar'
        )
        print_success(f"Propriétaire créé : {proprietaire2.nom_complet}")
        print_info(f"  → Entreprise : {proprietaire2.entreprise}")
        print_info(f"  → Avec compte utilisateur : {proprietaire2.has_user_account}")

        # Propriétaire 3 : Particulier SANS compte utilisateur
        proprietaire3 = Tiers.objects.create(
            nom='Fall',
            prenom='Moussa',
            email='moussa.fall@gmail.com',
            telephone='+221776666666',
            type_tiers='proprietaire',
            statut='actif',
            user=None,
            type_bailleur='particulier',
            adresse='Mermoz',
            ville='Dakar'
        )
        print_success(f"Propriétaire créé : {proprietaire3.nom_complet}")
        print_info(f"  → Avec compte utilisateur : {proprietaire3.has_user_account}")

        print("\n📊 Statistiques Propriétaires:")
        print(f"   Total propriétaires : {Tiers.objects.filter(type_tiers='proprietaire').count()}")
        print(f"   Avec compte utilisateur : {Tiers.objects.filter(type_tiers='proprietaire', user__isnull=False).count()}")
        print(f"   Sans compte utilisateur : {Tiers.objects.filter(type_tiers='proprietaire', user__isnull=True).count()}")

        return True

    except Exception as e:
        print_error(f"Erreur : {str(e)}")
        return False


def test_2_tiers_locataire():
    """Test 2 : Créer des Tiers locataires"""
    print_section("TEST 2 : Création de Tiers Locataires")

    try:
        # Locataire 1 : AVEC compte utilisateur
        user1 = User.objects.create_user(
            username='marie.sow',
            email='marie.sow@example.com',
            password='test123',
            first_name='Marie',
            last_name='Sow',
            user_type='tenant'
        )

        locataire1 = Tiers.objects.create(
            nom='Sow',
            prenom='Marie',
            email='marie.sow@example.com',
            telephone='+221779999999',
            type_tiers='locataire',
            statut='actif',
            user=user1,
            date_entree=date.today(),
            piece_identite_numero='CNI123456',
            situation_pro='salarie',
            garant_nom='Sow Papa',
            garant_tel='+221770000000'
        )
        print_success(f"Locataire créé : {locataire1.nom_complet}")
        print_info(f"  → Avec compte utilisateur : {locataire1.has_user_account}")
        print_info(f"  → Situation pro : {locataire1.get_situation_pro_display()}")

        # Locataire 2 : SANS compte utilisateur
        locataire2 = Tiers.objects.create(
            nom='Ndiaye',
            prenom='Ousmane',
            email='ousmane.ndiaye@yahoo.fr',
            telephone='+221778888888',
            type_tiers='locataire',
            statut='actif',
            user=None,
            date_entree=date.today(),
            piece_identite_numero='CNI789012',
            situation_pro='independant'
        )
        print_success(f"Locataire créé : {locataire2.nom_complet}")
        print_info(f"  → Avec compte utilisateur : {locataire2.has_user_account}")

        # Locataire 3 : AVEC compte utilisateur
        user2 = User.objects.create_user(
            username='aicha.ba',
            email='aicha.ba@example.com',
            password='test123',
            first_name='Aïcha',
            last_name='Ba',
            user_type='tenant'
        )

        locataire3 = Tiers.objects.create(
            nom='Ba',
            prenom='Aïcha',
            email='aicha.ba@example.com',
            telephone='+221777777777',
            type_tiers='locataire',
            statut='actif',
            user=user2,
            date_entree=date.today() - timedelta(days=30),
            piece_identite_numero='CNI345678',
            situation_pro='salarie'
        )
        print_success(f"Locataire créé : {locataire3.nom_complet}")

        print("\n📊 Statistiques Locataires:")
        print(f"   Total locataires : {Tiers.objects.filter(type_tiers='locataire').count()}")
        print(f"   Avec compte utilisateur : {Tiers.objects.filter(type_tiers='locataire', user__isnull=False).count()}")
        print(f"   Sans compte utilisateur : {Tiers.objects.filter(type_tiers='locataire', user__isnull=True).count()}")

        return True

    except Exception as e:
        print_error(f"Erreur : {str(e)}")
        return False


def test_3_residences():
    """Test 3 : Créer des résidences"""
    print_section("TEST 3 : Création de Résidences")

    try:
        proprietaires = Tiers.objects.filter(type_tiers='proprietaire')

        if not proprietaires.exists():
            print_error("Aucun propriétaire trouvé ! Exécutez d'abord test_1_tiers_proprietaire()")
            return False

        # Résidence 1
        residence1 = Residence.objects.create(
            nom='Les Jardins d\'Almadies',
            proprietaire=proprietaires[0],
            adresse='Rue 10, Zone résidentielle',
            quartier='Almadies',
            ville='Dakar',
            code_postal='12000',
            type_residence='immeuble',
            nb_etages=4,
            nb_appartements_total=16,
            statut='active',
            description='Résidence moderne avec piscine et sécurité 24h/24'
        )
        print_success(f"Résidence créée : {residence1.nom}")
        print_info(f"  → Propriétaire : {residence1.proprietaire.nom_complet}")
        print_info(f"  → Quartier : {residence1.quartier}")

        # Résidence 2
        if proprietaires.count() > 1:
            residence2 = Residence.objects.create(
                nom='Mermoz Premium',
                proprietaire=proprietaires[1],
                adresse='Avenue Bourguiba',
                quartier='Mermoz',
                ville='Dakar',
                code_postal='11000',
                type_residence='immeuble',
                nb_etages=5,
                nb_appartements_total=20,
                statut='active'
            )
            print_success(f"Résidence créée : {residence2.nom}")
            print_info(f"  → Propriétaire : {residence2.proprietaire.nom_complet}")

        # Résidence 3
        if proprietaires.count() > 2:
            residence3 = Residence.objects.create(
                nom='Point E Résidence',
                proprietaire=proprietaires[2],
                adresse='Boulevard du Général de Gaulle',
                quartier='Point E',
                ville='Dakar',
                code_postal='10000',
                type_residence='immeuble',
                nb_etages=3,
                nb_appartements_total=12,
                statut='active'
            )
            print_success(f"Résidence créée : {residence3.nom}")
            print_info(f"  → Propriétaire : {residence3.proprietaire.nom_complet}")

        print("\n📊 Statistiques Résidences:")
        print(f"   Total résidences : {Residence.objects.count()}")
        for proprio in proprietaires:
            nb = proprio.residences.count()
            print(f"   {proprio.nom_complet} : {nb} résidence(s)")

        return True

    except Exception as e:
        print_error(f"Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_4_appartements():
    """Test 4 : Créer des appartements"""
    print_section("TEST 4 : Création d'Appartements")

    try:
        residences = Residence.objects.all()

        if not residences.exists():
            print_error("Aucune résidence trouvée ! Exécutez d'abord test_3_residences()")
            return False

        appartements_crees = 0

        for residence in residences:
            # Créer 3 appartements par résidence
            for i in range(1, 4):
                appt = Appartement.objects.create(
                    nom=f"Appt {i}0{i}",
                    residence=residence,
                    type_bien='appartement',
                    etage=i,
                    superficie=Decimal('75.5'),
                    nb_pieces=3,
                    nb_chambres=2,
                    nb_sdb=1,
                    loyer_base=Decimal('350000'),
                    charges=Decimal('25000'),
                    depot_garantie=Decimal('700000'),
                    statut_occupation='libre',
                    description=f'Appartement F3 au {i}ème étage'
                )
                appartements_crees += 1

                if i == 1:  # Afficher seulement le premier de chaque résidence
                    print_success(f"Appartement créé : {residence.nom} - {appt.nom}")
                    print_info(f"  → Loyer : {appt.loyer_base} FCFA")
                    print_info(f"  → Statut : {appt.get_statut_occupation_display()}")

        print(f"\n✅ {appartements_crees} appartements créés au total")

        print("\n📊 Statistiques Appartements:")
        print(f"   Total appartements : {Appartement.objects.count()}")
        print(f"   Disponibles : {Appartement.objects.filter(statut_occupation='libre').count()}")
        print(f"   Occupés : {Appartement.objects.filter(statut_occupation='occupe').count()}")

        return True

    except Exception as e:
        print_error(f"Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_5_contrats():
    """Test 5 : Créer des contrats de location"""
    print_section("TEST 5 : Création de Contrats de Location")

    try:
        locataires = Tiers.objects.filter(type_tiers='locataire')
        appartements_libres = Appartement.objects.filter(statut_occupation='libre')

        if not locataires.exists():
            print_error("Aucun locataire trouvé ! Exécutez d'abord test_2_tiers_locataire()")
            return False

        if not appartements_libres.exists():
            print_error("Aucun appartement libre trouvé ! Exécutez d'abord test_4_appartements()")
            return False

        admin_user = User.objects.filter(is_superuser=True).first()

        # Créer 3 contrats
        nb_contrats = min(3, locataires.count(), appartements_libres.count())

        for i in range(nb_contrats):
            locataire = locataires[i]
            appartement = appartements_libres[i]

            date_debut = date.today()
            date_fin = date_debut + timedelta(days=365)

            contrat = RentalContract.objects.create(
                numero_contrat=f'CNT-2025-{1000+i}',
                appartement=appartement,
                locataire=locataire,
                date_debut=date_debut,
                date_fin=date_fin,
                duree_mois=12,
                loyer_mensuel=appartement.loyer_base,
                charges_mensuelles=appartement.charges,
                depot_garantie=appartement.depot_garantie,
                statut='actif',
                cree_par=admin_user
            )

            # Mettre à jour le statut de l'appartement
            appartement.statut_occupation = 'occupe'
            appartement.save()

            print_success(f"Contrat créé : {contrat.numero_contrat}")
            print_info(f"  → Locataire : {locataire.nom_complet}")
            print_info(f"  → Appartement : {appartement.residence.nom} - {appartement.nom}")
            print_info(f"  → Loyer : {contrat.loyer_mensuel} FCFA/mois")
            print_info(f"  → Durée : {date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")

        print("\n📊 Statistiques Contrats:")
        print(f"   Total contrats : {RentalContract.objects.count()}")
        print(f"   Contrats actifs : {RentalContract.objects.filter(statut='actif').count()}")
        print(f"   Appartements occupés : {Appartement.objects.filter(statut_occupation='occupe').count()}")
        print(f"   Appartements libres : {Appartement.objects.filter(statut_occupation='libre').count()}")

        return True

    except Exception as e:
        print_error(f"Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_6_queries():
    """Test 6 : Tester les requêtes de l'architecture Tiers"""
    print_section("TEST 6 : Validation des Requêtes")

    try:
        print("\n🔍 Test des requêtes simplifiées:")

        # Requête 1 : Tous les propriétaires actifs
        proprietaires = Tiers.objects.filter(type_tiers='proprietaire', statut='actif')
        print_success(f"Propriétaires actifs : {proprietaires.count()}")
        for p in proprietaires:
            print_info(f"  → {p.nom_complet} ({p.email})")

        # Requête 2 : Tous les locataires avec contrat actif
        print("\n🔍 Locataires avec contrat actif:")
        locataires_actifs = Tiers.objects.filter(
            type_tiers='locataire',
            contrats__statut='actif'
        ).distinct()
        print_success(f"Locataires avec contrat : {locataires_actifs.count()}")
        for l in locataires_actifs:
            contrat = l.contrats.filter(statut='actif').first()
            if contrat:
                print_info(f"  → {l.nom_complet} : {contrat.appartement.residence.nom} - {contrat.appartement.nom}")

        # Requête 3 : Propriétaires avec leurs résidences
        print("\n🔍 Propriétaires et leurs biens:")
        for proprio in Tiers.objects.filter(type_tiers='proprietaire'):
            nb_residences = proprio.residences.count()
            nb_appartements = Appartement.objects.filter(residence__proprietaire=proprio).count()
            print_success(f"{proprio.nom_complet}")
            print_info(f"  → {nb_residences} résidence(s), {nb_appartements} appartement(s)")

        # Requête 4 : Test des propriétés calculées
        print("\n🔍 Test des propriétés calculées:")
        tiers_test = Tiers.objects.first()
        if tiers_test:
            print_success(f"Tiers : {tiers_test.reference}")
            print_info(f"  → nom_complet : {tiers_test.nom_complet}")
            print_info(f"  → has_user_account : {tiers_test.has_user_account}")
            print_info(f"  → Type : {tiers_test.get_type_tiers_display()}")
            print_info(f"  → Statut : {tiers_test.get_statut_display()}")

        return True

    except Exception as e:
        print_error(f"Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Exécuter tous les tests"""
    print("\n" + "🚀"*35)
    print(" "*20 + "TESTS ARCHITECTURE TIERS")
    print("🚀"*35)

    results = {
        "Test 1 - Propriétaires": test_1_tiers_proprietaire(),
        "Test 2 - Locataires": test_2_tiers_locataire(),
        "Test 3 - Résidences": test_3_residences(),
        "Test 4 - Appartements": test_4_appartements(),
        "Test 5 - Contrats": test_5_contrats(),
        "Test 6 - Requêtes": test_6_queries(),
    }

    print_section("RÉSULTATS FINAUX")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print("\n" + "="*70)
    print(f"  BILAN : {passed}/{total} tests réussis ({passed*100//total}%)")
    print("="*70)

    if passed == total:
        print("\n🎉 Tous les tests sont passés ! L'architecture Tiers fonctionne parfaitement.")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")

    print("\n📊 Statistiques globales:")
    print(f"   Total Tiers : {Tiers.objects.count()}")
    print(f"   - Propriétaires : {Tiers.objects.filter(type_tiers='proprietaire').count()}")
    print(f"   - Locataires : {Tiers.objects.filter(type_tiers='locataire').count()}")
    print(f"   - Avec compte utilisateur : {Tiers.objects.filter(user__isnull=False).count()}")
    print(f"   - Sans compte utilisateur : {Tiers.objects.filter(user__isnull=True).count()}")
    print(f"   Total Résidences : {Residence.objects.count()}")
    print(f"   Total Appartements : {Appartement.objects.count()}")
    print(f"   Total Contrats : {RentalContract.objects.count()}")


if __name__ == '__main__':
    run_all_tests()
