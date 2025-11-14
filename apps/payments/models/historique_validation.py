from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference
from apps.payments.models.invoice import Invoice

User = get_user_model()


class HistoriqueValidation(BaseModel):
    """
    Historique complet des validations d'une demande d'achat/facture
    Permet de tracer qui a fait quoi et quand
    """

    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('soumission', 'Soumission pour validation'),
        ('validation_responsable', 'Validation par responsable'),
        ('refus_responsable', 'Refus par responsable'),
        ('traitement_comptable', 'Traitement comptable'),
        ('preparation_cheque', 'Préparation chèque'),
        ('validation_dg', 'Validation par DG'),
        ('refus_dg', 'Refus par DG'),
        ('approbation', 'Approbation finale'),
        ('achat', 'Achat effectué'),
        ('reception', 'Réception marchandise'),
        ('paiement', 'Paiement effectué'),
        ('annulation', 'Annulation'),
        ('modification', 'Modification'),
    ]

    demande = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='historique_validations',
        verbose_name="Demande"
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name="Action"
    )

    effectue_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions_validation',
        verbose_name="Effectué par"
    )

    date_action = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de l'action"
    )

    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    ancienne_valeur = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ancienne valeur",
        help_text="Pour les modifications"
    )

    nouvelle_valeur = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Nouvelle valeur",
        help_text="Pour les modifications"
    )

    def __str__(self):
        return f"{self.get_action_display()} - {self.demande.numero_facture} - {self.date_action.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Historique de validation"
        verbose_name_plural = "Historiques de validations"
        ordering = ['-date_action']