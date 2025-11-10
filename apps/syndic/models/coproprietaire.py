"""
Modèle pour les copropriétaires.
Lie un Tiers à une Copropriété avec ses tantièmes.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import TimestampedModel


class Coproprietaire(TimestampedModel):
    """
    Représente un copropriétaire dans une copropriété.
    Un Tiers peut être copropriétaire dans plusieurs copropriétés.
    """
    tiers = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='coproprietes',
        limit_choices_to={'type_tiers__contains': 'coproprietaire'},
        verbose_name='Copropriétaire'
    )

    copropriete = models.ForeignKey(
        'Copropriete',
        on_delete=models.CASCADE,
        related_name='coproprietaires',
        verbose_name='Copropriété'
    )

    # Tantièmes possédés
    nombre_tantiemes = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Nombre de tantièmes',
        help_text="Nombre de tantièmes détenus par ce copropriétaire dans cette copropriété"
    )

    # Quote-part calculée automatiquement
    quote_part = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        editable=False,
        verbose_name='Quote-part (%)',
        help_text="Pourcentage de la copropriété détenu (calculé automatiquement)"
    )

    # Lots détenus (optionnel, pour information)
    lots = models.ManyToManyField(
        'properties.Appartement',
        blank=True,
        related_name='coproprietaire',
        verbose_name='Lots',
        help_text="Appartements/lots détenus par ce copropriétaire"
    )

    # Date d'entrée dans la copropriété
    date_entree = models.DateField(
        verbose_name='Date d\'entrée',
        help_text="Date d'acquisition des parts"
    )

    # Date de sortie (optionnel)
    date_sortie = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date de sortie',
        help_text="Date de cession des parts"
    )

    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes internes sur ce copropriétaire"
    )

    class Meta:
        verbose_name = "Copropriétaire"
        verbose_name_plural = "Copropriétaires"
        ordering = ['-quote_part', 'tiers__nom']
        unique_together = [['tiers', 'copropriete']]
        indexes = [
            models.Index(fields=['copropriete', 'is_active']),
            models.Index(fields=['tiers', 'is_active']),
        ]

    def __str__(self):
        return f"{self.tiers.nom_complet} - {self.copropriete.residence.nom} ({self.quote_part}%)"

    def clean(self):
        """Validation personnalisée."""
        super().clean()

        # Vérifier que le tiers a le type 'coproprietaire'
        if self.tiers and 'coproprietaire' not in self.tiers.type_tiers:
            raise ValidationError({
                'tiers': 'Le tiers doit avoir le type "copropriétaire".'
            })

        # Vérifier que les tantièmes ne dépassent pas le total disponible
        if self.copropriete and self.nombre_tantiemes:
            tantiemes_attribues = self.copropriete.get_tantiemes_attribues()
            # Soustraire les tantièmes actuels si on modifie un copropriétaire existant
            if self.pk:
                old_instance = Coproprietaire.objects.get(pk=self.pk)
                tantiemes_attribues -= old_instance.nombre_tantiemes

            if tantiemes_attribues + self.nombre_tantiemes > self.copropriete.nombre_tantiemes_total:
                disponibles = self.copropriete.nombre_tantiemes_total - tantiemes_attribues
                raise ValidationError({
                    'nombre_tantiemes': f'Tantièmes disponibles: {disponibles}. '
                                       f'Total copropriété: {self.copropriete.nombre_tantiemes_total}'
                })

    def save(self, *args, **kwargs):
        """Calcule automatiquement la quote-part avant sauvegarde."""
        if self.copropriete and self.nombre_tantiemes:
            if self.copropriete.nombre_tantiemes_total > 0:
                self.quote_part = (self.nombre_tantiemes / self.copropriete.nombre_tantiemes_total) * 100
            else:
                self.quote_part = 0

        super().save(*args, **kwargs)

    @property
    def cotisation_par_periode(self):
        """Calcule le montant de cotisation pour ce copropriétaire par période."""
        return self.copropriete.calcul_cotisation_pour_tantiemes(self.nombre_tantiemes)

    def get_cotisations_impayees(self):
        """Retourne les cotisations impayées de ce copropriétaire."""
        return self.cotisations.filter(statut__in=['en_cours', 'impaye'])

    def get_total_impaye(self):
        """Retourne le montant total impayé."""
        cotisations_impayees = self.get_cotisations_impayees()
        return sum(
            cot.montant_theorique - cot.montant_percu
            for cot in cotisations_impayees
        )
