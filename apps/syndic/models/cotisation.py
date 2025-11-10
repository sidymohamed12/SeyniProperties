"""
Modèles pour les cotisations syndic et leurs paiements.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.core.models import TimestampedModel
from apps.core.utils import generate_unique_reference


class CotisationSyndic(TimestampedModel):
    """
    Représente un appel de fonds (cotisation) pour un copropriétaire.
    """
    STATUT_CHOICES = [
        ('a_venir', 'À venir'),
        ('en_cours', 'En cours'),
        ('paye', 'Payé'),
        ('impaye', 'Impayé'),
        ('annule', 'Annulé'),
    ]

    reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='Référence'
    )

    coproprietaire = models.ForeignKey(
        'Coproprietaire',
        on_delete=models.PROTECT,
        related_name='cotisations',
        verbose_name='Copropriétaire'
    )

    # Période concernée
    periode = models.CharField(
        max_length=20,
        verbose_name='Période',
        help_text="Format: 2025-Q1, 2025-Q2, 2025-M01, etc."
    )

    annee = models.IntegerField(
        verbose_name='Année',
        help_text="Année de la cotisation"
    )

    # Montants
    montant_theorique = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant théorique',
        help_text="Montant calculé selon les tantièmes"
    )

    montant_percu = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        verbose_name='Montant perçu',
        help_text="Montant réellement payé"
    )

    # Dates
    date_emission = models.DateField(
        verbose_name='Date d\'émission',
        help_text="Date de création de la cotisation"
    )

    date_echeance = models.DateField(
        verbose_name='Date d\'échéance',
        help_text="Date limite de paiement"
    )

    date_paiement_complet = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date de paiement complet',
        help_text="Date à laquelle la cotisation a été totalement payée"
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='a_venir',
        verbose_name='Statut'
    )

    # Relance
    nombre_relances = models.IntegerField(
        default=0,
        verbose_name='Nombre de relances'
    )

    date_derniere_relance = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Date dernière relance'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes internes sur cette cotisation"
    )

    class Meta:
        verbose_name = "Cotisation syndic"
        verbose_name_plural = "Cotisations syndic"
        ordering = ['-annee', '-periode', 'coproprietaire__tiers__nom']
        unique_together = [['coproprietaire', 'periode', 'annee']]
        indexes = [
            models.Index(fields=['statut', 'date_echeance']),
            models.Index(fields=['coproprietaire', 'statut']),
            models.Index(fields=['annee', 'periode']),
        ]

    def __str__(self):
        return f"{self.reference} - {self.coproprietaire.tiers.nom_complet} - {self.periode}"

    def save(self, *args, **kwargs):
        """Génère automatiquement la référence si elle n'existe pas."""
        if not self.reference:
            # Format: COT-2025-Q1-001
            prefix = f"COT-{self.annee}-{self.periode}"
            self.reference = generate_unique_reference(prefix=prefix)

        # Mettre à jour le statut automatiquement
        self.update_statut()

        super().save(*args, **kwargs)

    def update_statut(self):
        """Met à jour le statut en fonction des paiements et dates."""
        if self.statut == 'annule':
            return

        now = timezone.now().date()

        if self.montant_percu >= self.montant_theorique:
            self.statut = 'paye'
            if not self.date_paiement_complet:
                self.date_paiement_complet = now
        elif now < self.date_emission:
            self.statut = 'a_venir'
        elif now < self.date_echeance:
            self.statut = 'en_cours'
        else:
            self.statut = 'impaye'

    @property
    def montant_restant(self):
        """Retourne le montant restant à payer."""
        return max(Decimal('0.00'), self.montant_theorique - self.montant_percu)

    @property
    def pourcentage_paye(self):
        """Retourne le pourcentage payé."""
        if self.montant_theorique == 0:
            return 100
        return (self.montant_percu / self.montant_theorique) * 100

    @property
    def est_en_retard(self):
        """Vérifie si la cotisation est en retard."""
        if self.statut == 'paye':
            return False
        return timezone.now().date() > self.date_echeance

    @property
    def jours_retard(self):
        """Retourne le nombre de jours de retard."""
        if not self.est_en_retard:
            return 0
        return (timezone.now().date() - self.date_echeance).days

    def enregistrer_paiement(self, montant, mode_paiement, date_paiement=None, reference_paiement=None):
        """
        Enregistre un paiement pour cette cotisation.
        """
        if date_paiement is None:
            date_paiement = timezone.now().date()

        paiement = PaiementCotisation.objects.create(
            cotisation=self,
            montant=montant,
            mode_paiement=mode_paiement,
            date_paiement=date_paiement,
            reference_paiement=reference_paiement
        )

        # Mettre à jour le montant perçu
        self.montant_percu += montant
        self.update_statut()
        self.save()

        return paiement


class PaiementCotisation(TimestampedModel):
    """
    Représente un paiement effectué pour une cotisation.
    Une cotisation peut avoir plusieurs paiements (paiements partiels).
    """
    MODE_PAIEMENT_CHOICES = [
        ('cash', 'Espèces'),
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('orange_money', 'Orange Money'),
        ('wave', 'Wave'),
        ('autre', 'Autre'),
    ]

    cotisation = models.ForeignKey(
        'CotisationSyndic',
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name='Cotisation'
    )

    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant'
    )

    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT_CHOICES,
        verbose_name='Mode de paiement'
    )

    date_paiement = models.DateField(
        verbose_name='Date de paiement'
    )

    reference_paiement = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Référence de paiement',
        help_text="Numéro de chèque, référence virement, etc."
    )

    # Reçu
    recu_genere = models.BooleanField(
        default=False,
        verbose_name='Reçu généré'
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes sur ce paiement"
    )

    class Meta:
        verbose_name = "Paiement cotisation"
        verbose_name_plural = "Paiements cotisations"
        ordering = ['-date_paiement']
        indexes = [
            models.Index(fields=['cotisation', 'date_paiement']),
            models.Index(fields=['mode_paiement', 'date_paiement']),
        ]

    def __str__(self):
        return f"Paiement {self.montant} FCFA - {self.cotisation.reference} - {self.date_paiement}"

    def save(self, *args, **kwargs):
        """Met à jour automatiquement le montant perçu de la cotisation."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Mettre à jour le montant perçu et le statut de la cotisation
            self.cotisation.montant_percu += self.montant
            self.cotisation.update_statut()
            self.cotisation.save()
