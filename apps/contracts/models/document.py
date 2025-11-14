# apps/contracts/models/document.py

from django.db import models
from django.utils import timezone
from apps.core.models import TimestampedModel


class DocumentContrat(TimestampedModel):
    """
    Documents requis et fournis pour un contrat
    Gère les pièces justificatives nécessaires selon le type de contrat
    """

    TYPE_DOC_CHOICES = [
        # Documents pour location
        ('piece_identite', 'Pièce d\'identité'),
        ('quittance_loyer', 'Quittance de loyer'),
        ('bail_precedent', 'Bail précédent'),
        ('justificatif_revenus', 'Justificatif de revenus'),
        ('attestation_employeur', 'Attestation employeur'),
        ('rib', 'RIB'),
        ('etat_lieux_entree', 'État des lieux d\'entrée'),

        # Documents professionnels (pour contrats à usage professionnel)
        ('ninea', 'Document NINEA'),
        ('rccm', 'Document RCCM'),

        # Documents pour vente
        ('titre_propriete', 'Titre de propriété'),
        ('plan_cadastral', 'Plan cadastral'),
        ('compromis_vente', 'Compromis de vente'),
        ('diagnostic_technique', 'Diagnostic technique'),

        # Autres
        ('autre', 'Autre document'),
    ]

    STATUT_CHOICES = [
        ('attendu', 'En attente'),
        ('recu', 'Reçu'),
        ('verifie', 'Vérifié'),
        ('refuse', 'Refusé'),
    ]

    # Relation avec le workflow
    workflow = models.ForeignKey(
        'contracts.ContractWorkflow',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Workflow"
    )

    # Type de document
    type_document = models.CharField(
        max_length=30,
        choices=TYPE_DOC_CHOICES,
        verbose_name="Type de document"
    )

    # Fichier
    fichier = models.FileField(
        upload_to='pmo/documents/%Y/%m/',
        blank=True,
        verbose_name="Fichier"
    )

    # Statut de vérification
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='attendu',
        verbose_name="Statut"
    )

    verifie_par = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_verifies',
        verbose_name="Vérifié par"
    )

    date_verification = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de vérification"
    )

    # Observations
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    obligatoire = models.BooleanField(
        default=True,
        verbose_name="Document obligatoire"
    )

    class Meta:
        verbose_name = "Document de contrat"
        verbose_name_plural = "Documents de contrat"
        ordering = ['workflow', 'type_document']
        indexes = [
            models.Index(fields=['workflow', 'statut']),
            models.Index(fields=['type_document']),
        ]

    def __str__(self):
        return f"{self.get_type_document_display()} - {self.workflow.contrat.numero_contrat}"

    def get_absolute_url(self):
        """URL de retour vers le workflow"""
        return self.workflow.get_absolute_url()

    def marquer_comme_verifie(self, user):
        """Marque le document comme vérifié"""
        self.statut = 'verifie'
        self.verifie_par = user
        self.date_verification = timezone.now()
        self.save()

        # Vérifier si tous les documents obligatoires sont vérifiés
        workflow = self.workflow
        docs_obligatoires = workflow.documents.filter(obligatoire=True)
        tous_verifies = all(doc.statut == 'verifie' for doc in docs_obligatoires)

        if tous_verifies:
            workflow.statut_dossier = 'complet'
            workflow.save()
