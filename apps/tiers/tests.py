"""
Tests pour le module de gestion des tiers
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import Tiers, TiersBien
from apps.properties.models import Residence, Appartement

User = get_user_model()


class TiersModelTest(TestCase):
    """Tests pour le modèle Tiers"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            user_type='manager'
        )

    def test_create_tiers(self):
        """Test de création d'un tiers"""
        tiers = Tiers.objects.create(
            nom='Diop',
            prenom='Moussa',
            type_tiers='proprietaire',
            telephone='+221771234567',
            email='moussa.diop@example.com',
            adresse='123 Rue Test',
            ville='Dakar',
            statut='actif',
            cree_par=self.user
        )

        self.assertEqual(tiers.nom, 'Diop')
        self.assertEqual(tiers.prenom, 'Moussa')
        self.assertTrue(tiers.reference.startswith('TIER-'))
        self.assertEqual(str(tiers), 'Diop Moussa (Propriétaire)')

    def test_nom_complet_property(self):
        """Test de la propriété nom_complet"""
        tiers = Tiers.objects.create(
            nom='Fall',
            prenom='Awa',
            type_tiers='locataire',
            telephone='+221771234568',
            email='awa.fall@example.com',
            adresse='456 Avenue Test',
            ville='Dakar',
            cree_par=self.user
        )

        self.assertEqual(tiers.nom_complet, 'Fall Awa')

    def test_tiers_without_prenom(self):
        """Test d'un tiers sans prénom (entreprise)"""
        tiers = Tiers.objects.create(
            nom='Entreprise SARL',
            type_tiers='partenaire',
            telephone='+221771234569',
            email='contact@entreprise.sn',
            adresse='789 Boulevard Test',
            ville='Dakar',
            cree_par=self.user
        )

        self.assertEqual(tiers.nom_complet, 'Entreprise SARL')


class TiersBienModelTest(TestCase):
    """Tests pour le modèle TiersBien"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            user_type='manager'
        )

        self.tiers = Tiers.objects.create(
            nom='Sow',
            prenom='Cheikh',
            type_tiers='proprietaire',
            telephone='+221771234570',
            email='cheikh.sow@example.com',
            adresse='111 Rue Propriétaire',
            ville='Dakar',
            cree_par=self.user
        )

        self.residence = Residence.objects.create(
            nom='Résidence Test',
            adresse='222 Avenue Résidence',
            quartier='Plateau',
            ville='Dakar',
            nb_etages=3,
            nb_appartements_total=12
        )

    def test_create_tiers_bien_with_residence(self):
        """Test de création d'une liaison tiers-résidence"""
        tiers_bien = TiersBien.objects.create(
            tiers=self.tiers,
            residence=self.residence,
            type_contrat='gestion',
            type_mandat='exclusif',
            date_debut=date.today(),
            statut='en_cours',
            cree_par=self.user
        )

        self.assertEqual(tiers_bien.tiers, self.tiers)
        self.assertEqual(tiers_bien.residence, self.residence)
        self.assertEqual(tiers_bien.type_contrat, 'gestion')

    def test_duree_jours_property(self):
        """Test de la propriété duree_jours"""
        date_debut = date.today() - timedelta(days=30)
        date_fin = date.today() + timedelta(days=30)

        tiers_bien = TiersBien.objects.create(
            tiers=self.tiers,
            residence=self.residence,
            type_contrat='vente',
            date_debut=date_debut,
            date_fin=date_fin,
            cree_par=self.user
        )

        self.assertEqual(tiers_bien.duree_jours, 60)


class TiersViewsTest(TestCase):
    """Tests pour les vues du module tiers"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            user_type='manager'
        )

        self.tiers = Tiers.objects.create(
            nom='Ndiaye',
            prenom='Fatou',
            type_tiers='locataire',
            telephone='+221771234571',
            email='fatou.ndiaye@example.com',
            adresse='333 Rue Locataire',
            ville='Dakar',
            cree_par=self.user
        )

    def test_tiers_liste_view_requires_login(self):
        """Test que la vue liste nécessite une authentification"""
        response = self.client.get(reverse('tiers:tiers_liste'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_tiers_liste_view_authenticated(self):
        """Test de la vue liste avec authentification"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tiers:tiers_liste'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gestion des Tiers')

    def test_tiers_detail_view(self):
        """Test de la vue détail"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('tiers:tiers_detail', kwargs={'pk': self.tiers.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tiers.nom_complet)

    def test_tiers_ajouter_view_get(self):
        """Test d'accès au formulaire d'ajout"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tiers:tiers_ajouter'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ajouter un Tiers')

    def test_tiers_ajouter_view_post(self):
        """Test de création d'un tiers via le formulaire"""
        self.client.login(username='testuser', password='testpass123')

        data = {
            'nom': 'Sarr',
            'prenom': 'Ibrahima',
            'type_tiers': 'prestataire',
            'telephone': '+221771234572',
            'email': 'ibrahima.sarr@example.com',
            'adresse': '444 Rue Prestataire',
            'ville': 'Dakar',
            'statut': 'actif',
        }

        response = self.client.post(reverse('tiers:tiers_ajouter'), data)

        # Devrait rediriger après création
        self.assertEqual(response.status_code, 302)

        # Vérifier que le tiers a été créé
        tiers = Tiers.objects.get(email='ibrahima.sarr@example.com')
        self.assertEqual(tiers.nom, 'Sarr')
        self.assertEqual(tiers.prenom, 'Ibrahima')

    def test_tiers_search(self):
        """Test de la recherche de tiers"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('tiers:tiers_liste'),
            {'search': 'Ndiaye'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ndiaye')

    def test_tiers_search_api(self):
        """Test de l'API de recherche"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(
            reverse('tiers:tiers_search_api'),
            {'q': 'Ndiaye'}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('results' in data)
        self.assertTrue(len(data['results']) > 0)
