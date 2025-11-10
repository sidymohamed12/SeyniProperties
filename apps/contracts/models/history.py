# apps/contracts/models/history.py

from django.db import models
from django.urls import reverse
from apps.core.models import TimestampedModel


class HistoriqueWorkflow(TimestampedModel):
    """
    Historique des transitions du workflow PMO
    Assure la traçabilité complète du processus
    """

    workflow = models.ForeignKey(
        'contracts.ContractWorkflow',
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name="Workflow"
    )

    etape_precedente = models.CharField(
        max_length=30,
        verbose_name="Étape précédente"
    )

    etape_suivante = models.CharField(
        max_length=30,
        verbose_name="Étape suivante"
    )

    effectue_par = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Effectué par"
    )

    date_transition = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de transition"
    )

    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    class Meta:
        verbose_name = "Historique workflow"
        verbose_name_plural = "Historiques workflow"
        ordering = ['-date_transition']
        indexes = [
            models.Index(fields=['workflow', '-date_transition']),
            models.Index(fields=['effectue_par']),
        ]

    def __str__(self):
        return f"{self.etape_precedente} → {self.etape_suivante} ({self.date_transition.strftime('%d/%m/%Y %H:%M')})"

    def get_absolute_url(self):
        """URL de retour vers le workflow"""
        return self.workflow.get_absolute_url()
