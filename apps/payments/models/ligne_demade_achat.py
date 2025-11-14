from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference
from apps.payments.models.invoice import Invoice

User = get_user_model()


class LigneDemandeAchat(BaseModel):
    """
    Ligne d'article dans une demande d'achat
    Permet de détailler chaque article/matériel demandé
    """

    demande = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='lignes_achat',
        verbose_name="Demande d'achat",
        limit_choices_to={'type_facture': 'demande_achat'}
    )

    designation = models.CharField(
        max_length=255,
        verbose_name="Désignation de l'article"
    )

    quantite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Quantité"
    )

    unite = models.CharField(
        max_length=50,
        default='unité',
        verbose_name="Unité",
        help_text="Ex: unité, mètre, kg, litre, boîte"
    )

    fournisseur = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Fournisseur/Partenaire"
    )

    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix unitaire estimé (FCFA)"
    )

    prix_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix total (FCFA)",
        help_text="Calculé automatiquement: quantité × prix unitaire"
    )

    motif = models.TextField(
        verbose_name="Motif/Justification pour cet article"
    )

    # Pour suivi de réception
    quantite_recue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Quantité réellement reçue"
    )

    prix_reel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Prix réel payé"
    )

    def save(self, *args, **kwargs):
        # Calculer automatiquement le prix total
        if self.quantite and self.prix_unitaire:
            self.prix_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    @property
    def ecart_quantite(self):
        """Écart entre quantité demandée et reçue"""
        if self.quantite_recue:
            return self.quantite_recue - self.quantite
        return None

    @property
    def ecart_prix(self):
        """Écart entre prix estimé et réel"""
        if self.prix_reel:
            return self.prix_reel - self.prix_total
        return None

    def __str__(self):
        return f"{self.designation} - {self.quantite} {self.unite}"

    class Meta:
        verbose_name = "Ligne de demande d'achat"
        verbose_name_plural = "Lignes de demandes d'achat"
        ordering = ['id']
