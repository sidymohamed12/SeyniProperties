"""
Modèle pour la gestion des copropriétés.
Une copropriété est liée à une résidence dont Imany assure le syndic.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import TimestampedModel


class Copropriete(TimestampedModel):
    """
    Représente une copropriété gérée par Imany en tant que syndic.
    """
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
    ]

    residence = models.OneToOneField(
        'properties.Residence',
        on_delete=models.CASCADE,
        related_name='copropriete',
        verbose_name='Résidence'
    )

    # Tantièmes (parts de copropriété)
    nombre_tantiemes_total = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Nombre total de tantièmes dans la copropriété (ex: 10000)"
    )

    # Périodicité des cotisations
    periode_cotisation = models.CharField(
        max_length=20,
        choices=PERIODE_CHOICES,
        default='trimestriel',
        verbose_name='Période de cotisation'
    )

    # Budget annuel prévisionnel
    budget_annuel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Budget annuel prévisionnel pour l'entretien des parties communes"
    )

    # Date de début de gestion
    date_debut_gestion = models.DateField(
        verbose_name='Date de début de gestion',
        help_text="Date à laquelle Imany a commencé la gestion de cette copropriété"
    )

    # Compte bancaire dédié (optionnel)
    compte_bancaire = models.CharField(
        max_length=34,
        blank=True,
        null=True,
        help_text="IBAN du compte bancaire de la copropriété"
    )

    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name='Active'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes internes sur la copropriété"
    )

    class Meta:
        verbose_name = "Copropriété"
        verbose_name_plural = "Copropriétés"
        ordering = ['residence__nom']
        indexes = [
            models.Index(fields=['is_active', 'date_debut_gestion']),
        ]

    def __str__(self):
        return f"Copropriété {self.residence.nom}"

    @property
    def nombre_coproprietaires(self):
        """Retourne le nombre de copropriétaires."""
        return self.coproprietaires.count()

    @property
    def cotisation_par_periode(self):
        """Calcule le montant total de cotisation par période."""
        periodes_par_an = {
            'mensuel': 12,
            'trimestriel': 4,
            'semestriel': 2,
            'annuel': 1,
        }
        return self.budget_annuel / periodes_par_an.get(self.periode_cotisation, 4)

    def calcul_cotisation_pour_tantiemes(self, nombre_tantiemes):
        """
        Calcule le montant de cotisation pour un nombre de tantièmes donné.
        """
        from decimal import Decimal
        if self.nombre_tantiemes_total == 0:
            return 0
        quote_part = Decimal(str(nombre_tantiemes / self.nombre_tantiemes_total))
        return self.cotisation_par_periode * quote_part

    def get_tantiemes_attribues(self):
        """Retourne le nombre total de tantièmes déjà attribués aux copropriétaires."""
        return self.coproprietaires.aggregate(
            total=models.Sum('nombre_tantiemes')
        )['total'] or 0

    def get_tantiemes_disponibles(self):
        """Retourne le nombre de tantièmes non encore attribués."""
        return self.nombre_tantiemes_total - self.get_tantiemes_attribues()
