# apps/contracts/models/contract.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from apps.core.models import TimestampedModel
from apps.core.utils import generate_unique_reference


class RentalContract(TimestampedModel):
    """
    Contrat de location entre un locataire et un appartement
    """

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('resilie', 'Résilié'),
        ('suspendu', 'Suspendu'),
        ('renouvele', 'Renouvelé'),
    ]

    TYPE_CONTRAT_CHOICES = [
        ('location_simple', 'Location simple'),
        ('location_meublee', 'Location meublée'),
        ('bail_commercial', 'Bail commercial'),
        ('sous_location', 'Sous-location'),
    ]

    TYPE_CONTRAT_USAGE_CHOICES = [
        ('habitation', 'Contrat à Usage d\'Habitation'),
        ('professionnel', 'Contrat à Usage Professionnel'),
    ]

    # Identification
    numero_contrat = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de contrat",
        help_text="Numéro unique du contrat (ex: CTR-2025-001)"
    )

    # Relations principales
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        related_name='contrats',
        verbose_name="Appartement loué"
    )

    locataire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='contrats',
        verbose_name="Locataire",
        limit_choices_to={'type_tiers': 'locataire'}
    )

    # Type et caractéristiques
    type_contrat = models.CharField(
        max_length=20,
        choices=TYPE_CONTRAT_CHOICES,
        default='location_simple',
        verbose_name="Type de contrat"
    )

    type_contrat_usage = models.CharField(
        max_length=20,
        choices=TYPE_CONTRAT_USAGE_CHOICES,
        default='habitation',
        verbose_name="Usage du contrat",
        help_text="Détermine les clauses applicables au contrat"
    )

    # Dates du contrat
    date_debut = models.DateField(
        verbose_name="Date de début"
    )

    date_fin = models.DateField(
        verbose_name="Date de fin"
    )

    duree_mois = models.PositiveIntegerField(
        verbose_name="Durée en mois",
        validators=[MinValueValidator(1), MaxValueValidator(120)]
    )

    # Montants financiers
    loyer_mensuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Loyer mensuel (FCFA)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    charges_mensuelles = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Charges mensuelles (FCFA)"
    )

    depot_garantie = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Dépôt de garantie (FCFA)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    frais_agence = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Frais d'agence (FCFA)",
        help_text="Frais d'agence ajustables - peut être modifié manuellement"
    )

    travaux_realises = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Travaux réalisés (FCFA)",
        help_text="Coût des travaux de rénovation ou d'aménagement avant la location"
    )

    # TVA (pour contrats professionnels)
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Taux de TVA (%)",
        help_text="TVA applicable (18% pour contrats professionnels, 0% pour habitation)"
    )

    montant_tva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant TVA (FCFA)",
        help_text="Montant de la TVA calculé automatiquement"
    )

    # État et renouvellement
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='brouillon',
        verbose_name="Statut"
    )

    is_renouvelable = models.BooleanField(
        default=True,
        verbose_name="Renouvelable automatiquement"
    )

    preavis_mois = models.PositiveIntegerField(
        default=1,
        verbose_name="Préavis en mois",
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )

    # Documents et conditions
    conditions_particulieres = models.TextField(
        blank=True,
        verbose_name="Conditions particulières"
    )

    fichier_contrat = models.FileField(
        upload_to='contrats/pdf/%Y/%m/',
        blank=True,
        verbose_name="Fichier PDF du contrat"
    )

    # Suivi des signatures
    date_signature = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de signature"
    )

    signe_par_locataire = models.BooleanField(
        default=False,
        verbose_name="Signé par le locataire"
    )

    signe_par_bailleur = models.BooleanField(
        default=False,
        verbose_name="Signé par le bailleur"
    )

    # Informations de suivi
    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes"
    )

    cree_par = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='contrats_crees',
        verbose_name="Créé par"
    )

    class Meta:
        verbose_name = "Contrat de location"
        verbose_name_plural = "Contrats de location"
        ordering = ['-date_debut', '-created_at']
        indexes = [
            models.Index(fields=['numero_contrat']),
            models.Index(fields=['appartement', 'statut']),
            models.Index(fields=['locataire', 'statut']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['statut']),
        ]

    def save(self, *args, **kwargs):
        if not self.numero_contrat:
            self.numero_contrat = generate_unique_reference('CTR')

        # Calculer la durée si non fournie
        if not self.duree_mois and self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            self.duree_mois = max(1, round(delta.days / 30))

        # Appliquer automatiquement la TVA de 18% pour les contrats professionnels
        if self.type_contrat_usage == 'professionnel':
            self.taux_tva = Decimal('18.00')
        else:
            # Contrats d'habitation : pas de TVA
            self.taux_tva = Decimal('0.00')

        # Calculer le montant de la TVA sur le loyer mensuel
        if self.loyer_mensuel and self.taux_tva:
            self.montant_tva = (self.loyer_mensuel * self.taux_tva / Decimal('100.00')).quantize(Decimal('0.01'))
        else:
            self.montant_tva = Decimal('0.00')

        super().save(*args, **kwargs)

        # Mettre à jour le statut de l'appartement
        if self.statut == 'actif':
            self.appartement.statut_occupation = 'occupe'
            self.appartement.save()

    def __str__(self):
        locataire_nom = self.locataire.nom_complet if self.locataire else "Sans locataire"
        return f"{self.numero_contrat} - {locataire_nom} - {self.appartement}"

    def get_absolute_url(self):
        """URL du détail du contrat"""
        return reverse('contracts:detail', kwargs={'pk': self.pk})

    @property
    def montant_total_mensuel(self):
        """Calcule le montant total mensuel (loyer + charges + TVA pour contrats professionnels)"""
        loyer = self.loyer_mensuel or Decimal('0.00')
        charges = self.charges_mensuelles or Decimal('0.00')
        tva = self.montant_tva or Decimal('0.00')
        return loyer + charges + tva

    @property
    def loyer_ht(self):
        """Loyer mensuel hors taxes"""
        return self.loyer_mensuel or Decimal('0.00')

    @property
    def loyer_ttc(self):
        """Loyer mensuel toutes taxes comprises (avec TVA si applicable)"""
        loyer = self.loyer_mensuel or Decimal('0.00')
        tva = self.montant_tva or Decimal('0.00')
        return loyer + tva

    # ============================================================================
    # CALCULS FINANCIERS - TOM + FRAIS D'AGENCE
    # ============================================================================

    # Constantes pour les calculs
    TAUX_TOM = Decimal('0.036')  # 3,6%
    TAUX_FRAIS_AGENCE_DEFAUT = Decimal('0.05')  # 5% par défaut

    @property
    def montant_tom(self):
        """
        Calcule la Taxe d'Ordures Ménagères (TOM)
        TOM = Loyer mensuel × 3,6%
        """
        if self.loyer_mensuel:
            return (self.loyer_mensuel * self.TAUX_TOM).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def montant_frais_agence_calcule(self):
        """
        Calcule les frais d'agence suggérés (5% du loyer)
        Cette valeur est indicative - le champ frais_agence peut être modifié manuellement
        """
        if self.loyer_mensuel:
            return (self.loyer_mensuel * self.TAUX_FRAIS_AGENCE_DEFAUT).quantize(Decimal('0.01'))
        return Decimal('0.00')

    @property
    def montant_frais_agence_effectif(self):
        """
        Retourne les frais d'agence effectifs (valeur du champ frais_agence)
        Utilise le montant saisi manuellement, ou 0 si non renseigné
        """
        return self.frais_agence or Decimal('0.00')

    @property
    def total_deductions(self):
        """
        Total des déductions (TOM + Frais d'agence effectifs)
        """
        return self.montant_tom + self.montant_frais_agence_effectif

    @property
    def loyer_net_proprietaire(self):
        """
        Loyer net versé au propriétaire après déductions
        Loyer net = Loyer brut - TOM - Frais d'agence
        """
        if self.loyer_mensuel:
            return self.loyer_mensuel - self.total_deductions
        return Decimal('0.00')

    @property
    def details_financiers(self):
        """
        Retourne un dictionnaire avec tous les détails financiers
        """
        return {
            'loyer_ht': self.loyer_mensuel,
            'taux_tva': self.taux_tva,
            'montant_tva': self.montant_tva,
            'loyer_ttc': self.loyer_ttc,
            'charges': self.charges_mensuelles or Decimal('0.00'),
            'tom': self.montant_tom,
            'frais_agence': self.montant_frais_agence_effectif,
            'frais_agence_suggere': self.montant_frais_agence_calcule,
            'total_deductions': self.total_deductions,
            'loyer_net_proprietaire': self.loyer_net_proprietaire,
            'total_locataire': self.montant_total_mensuel,
            'travaux_realises': self.travaux_realises or Decimal('0.00'),
            'montant_global': self.montant_global,
        }

    @property
    def montant_global(self):
        """
        Calcule le montant global initial du contrat
        Montant global = Loyer TTC + Frais d'agence + Charges mensuelles + Travaux réalisés

        Ce montant représente l'investissement total nécessaire au démarrage du contrat
        """
        loyer_ttc = self.loyer_ttc  # Inclut la TVA pour contrats professionnels
        frais = self.montant_frais_agence_effectif
        charges = self.charges_mensuelles or Decimal('0.00')
        travaux = self.travaux_realises or Decimal('0.00')

        return loyer_ttc + frais + charges + travaux

    @property
    def bailleur(self):
        """Accès au bailleur via l'appartement et la résidence"""
        return self.appartement.residence.proprietaire

    @property
    def is_active(self):
        """Vérifie si le contrat est actif à la date actuelle"""
        if self.statut != 'actif':
            return False

        today = timezone.now().date()
        return self.date_debut <= today <= self.date_fin

    @property
    def jours_restants(self):
        """Nombre de jours restants avant la fin du contrat"""
        if not self.date_fin:
            return None

        today = timezone.now().date()
        if self.date_fin <= today:
            return 0

        return (self.date_fin - today).days

    @property
    def arrive_a_echeance(self):
        """Vérifie si le contrat arrive à échéance dans les 30 jours"""
        jours = self.jours_restants
        return jours is not None and 0 <= jours <= 30

    def renouveler(self, nouvelle_date_fin, nouveau_loyer=None):
        """
        Renouvelle le contrat avec une nouvelle date de fin
        """
        if nouveau_loyer:
            self.loyer_mensuel = nouveau_loyer

        self.date_fin = nouvelle_date_fin

        # Recalculer la durée
        delta = self.date_fin - self.date_debut
        self.duree_mois = max(1, round(delta.days / 30))

        self.statut = 'actif'
        self.save()

    def resilier(self, date_resiliation=None, motif=""):
        """
        Résilie le contrat
        """
        if not date_resiliation:
            date_resiliation = timezone.now().date()

        self.date_fin = date_resiliation
        self.statut = 'resilie'

        if motif:
            self.notes_internes += f"\nRésiliation le {date_resiliation}: {motif}"

        # Libérer l'appartement
        self.appartement.statut_occupation = 'libre'
        self.appartement.save()

        self.save()
