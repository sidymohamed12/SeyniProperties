"""
Modèles pour la gestion du budget prévisionnel de la copropriété.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimestampedModel


class BudgetPrevisionnel(TimestampedModel):
    """
    Budget prévisionnel annuel d'une copropriété.
    Obligatoire légalement, voté en assemblée générale.
    """
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('propose', 'Proposé'),
        ('vote', 'Voté'),
        ('en_cours', 'En cours d\'exécution'),
        ('cloture', 'Clôturé'),
    ]

    copropriete = models.ForeignKey(
        'Copropriete',
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='Copropriété'
    )

    annee = models.IntegerField(
        verbose_name='Année',
        help_text="Année du budget prévisionnel"
    )

    montant_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant total',
        help_text="Montant total du budget"
    )

    # Assemblée générale
    date_ag = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date AG',
        help_text="Date de l'assemblée générale de vote"
    )

    date_vote = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date de vote',
        help_text="Date de vote du budget"
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='brouillon',
        verbose_name='Statut'
    )

    # Notes et documents
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes et observations"
    )

    document = models.FileField(
        upload_to='syndic/budgets/',
        blank=True,
        null=True,
        verbose_name='Document',
        help_text="PV d'AG, budget détaillé, etc."
    )

    class Meta:
        verbose_name = "Budget prévisionnel"
        verbose_name_plural = "Budgets prévisionnels"
        ordering = ['-annee']
        unique_together = [['copropriete', 'annee']]
        indexes = [
            models.Index(fields=['copropriete', 'annee']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Budget {self.annee} - {self.copropriete.residence.nom}"

    @property
    def montant_depense(self):
        """Retourne le montant total dépensé."""
        return sum(
            ligne.montant_realise or 0
            for ligne in self.lignes.all()
        )

    @property
    def taux_execution(self):
        """Retourne le taux d'exécution du budget en pourcentage."""
        if self.montant_total == 0:
            return 0
        return (self.montant_depense / self.montant_total) * 100

    @property
    def montant_restant(self):
        """Retourne le montant restant du budget."""
        return self.montant_total - self.montant_depense


class LigneBudget(TimestampedModel):
    """
    Ligne de dépense dans un budget prévisionnel.
    """
    CATEGORIE_CHOICES = [
        ('entretien_courant', 'Entretien courant'),
        ('jardinage', 'Jardinage'),
        ('nettoyage', 'Nettoyage'),
        ('gardiennage', 'Gardiennage'),
        ('electricite', 'Électricité'),
        ('eau', 'Eau'),
        ('assurance', 'Assurance'),
        ('reparations', 'Réparations'),
        ('travaux', 'Travaux'),
        ('honoraires_syndic', 'Honoraires syndic'),
        ('charges_bancaires', 'Charges bancaires'),
        ('provisions', 'Provisions'),
        ('autre', 'Autre'),
    ]

    budget = models.ForeignKey(
        'BudgetPrevisionnel',
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name='Budget'
    )

    categorie = models.CharField(
        max_length=30,
        choices=CATEGORIE_CHOICES,
        verbose_name='Catégorie'
    )

    description = models.CharField(
        max_length=255,
        verbose_name='Description'
    )

    montant_prevu = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant prévu'
    )

    montant_realise = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Montant réalisé',
        help_text="Montant réellement dépensé"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes sur cette ligne budgétaire"
    )

    class Meta:
        verbose_name = "Ligne de budget"
        verbose_name_plural = "Lignes de budget"
        ordering = ['categorie', 'description']
        indexes = [
            models.Index(fields=['budget', 'categorie']),
        ]

    def __str__(self):
        return f"{self.categorie} - {self.description} ({self.montant_prevu} FCFA)"

    @property
    def ecart(self):
        """Retourne l'écart entre prévu et réalisé."""
        return self.montant_prevu - self.montant_realise

    @property
    def taux_realisation(self):
        """Retourne le taux de réalisation en pourcentage."""
        if self.montant_prevu == 0:
            return 0
        return (self.montant_realise / self.montant_prevu) * 100
