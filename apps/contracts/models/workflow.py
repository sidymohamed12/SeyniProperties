# apps/contracts/models/workflow.py

from django.db import models
from django.urls import reverse
from django.utils import timezone
from apps.core.models import TimestampedModel


class ContractWorkflow(TimestampedModel):
    """
    Gère le workflow PMO pour le cycle de vie d'un contrat
    De la vérification des dossiers à la remise des clés
    """

    ETAPE_CHOICES = [
        ('verification_dossier', 'Vérification des dossiers'),
        ('attente_facture', 'En attente de facture'),
        ('facture_validee', 'Facture validée'),
        ('redaction_contrat', 'Rédaction du contrat'),
        ('visite_entree', 'Visite d\'entrée et état des lieux'),
        ('remise_cles', 'Remise des clés'),
        ('termine', 'Terminé - Contrat actif'),
    ]

    STATUT_DOSSIER_CHOICES = [
        ('en_cours', 'En cours de vérification'),
        ('incomplet', 'Dossier incomplet'),
        ('complet', 'Dossier complet'),
    ]

    # Relation avec le contrat
    contrat = models.OneToOneField(
        'contracts.RentalContract',
        on_delete=models.CASCADE,
        related_name='workflow',
        verbose_name="Contrat"
    )

    # Étape actuelle du workflow
    etape_actuelle = models.CharField(
        max_length=30,
        choices=ETAPE_CHOICES,
        default='verification_dossier',
        verbose_name="Étape actuelle"
    )

    # Statut du dossier
    statut_dossier = models.CharField(
        max_length=15,
        choices=STATUT_DOSSIER_CHOICES,
        default='en_cours',
        verbose_name="Statut du dossier"
    )

    # Responsable PMO
    responsable_pmo = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='workflows_pmo',
        verbose_name="Responsable PMO"
    )

    # Lien avec la facture (créée par Finance)
    facture = models.ForeignKey(
        'payments.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflow_contrat',
        verbose_name="Facture associée"
    )

    facture_validee_le = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation de la facture"
    )

    # Visite d'entrée et état des lieux
    date_visite_entree = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de la visite d'entrée"
    )

    lieu_rdv_visite = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Lieu de rendez-vous pour la visite"
    )

    rapport_etat_lieux = models.FileField(
        upload_to='pmo/etat_lieux/%Y/%m/',
        blank=True,
        verbose_name="Rapport d'état des lieux (PDF)"
    )

    # Remise des clés
    date_remise_cles = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de remise des clés"
    )

    nombre_cles = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre de clés remises"
    )

    cles_remises_par = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remises_cles',
        verbose_name="Clés remises par"
    )

    # Notes et observations
    notes_pmo = models.TextField(
        blank=True,
        verbose_name="Notes internes PMO"
    )

    observations_visite = models.TextField(
        blank=True,
        verbose_name="Observations lors de la visite"
    )

    # Dates importantes
    date_envoi_finance = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'envoi au service Finance"
    )

    date_debut_redaction = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début de rédaction"
    )

    class Meta:
        verbose_name = "Workflow PMO"
        verbose_name_plural = "Workflows PMO"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['etape_actuelle']),
            models.Index(fields=['statut_dossier']),
            models.Index(fields=['responsable_pmo']),
            models.Index(fields=['date_visite_entree']),
        ]

    def __str__(self):
        return f"Workflow PMO - {self.contrat.numero_contrat} ({self.get_etape_actuelle_display()})"

    def get_absolute_url(self):
        """URL du détail du workflow PMO"""
        return reverse('contracts:pmo_detail', kwargs={'pk': self.pk})

    @property
    def progression_pourcentage(self):
        """Calcule le pourcentage de progression du workflow"""
        etapes = dict(self.ETAPE_CHOICES)
        etapes_list = list(etapes.keys())

        if self.etape_actuelle not in etapes_list:
            return 0

        index_actuel = etapes_list.index(self.etape_actuelle)
        total_etapes = len(etapes_list)

        return round((index_actuel + 1) / total_etapes * 100)

    @property
    def peut_avancer(self):
        """Vérifie si le workflow peut avancer à l'étape suivante"""
        if self.etape_actuelle == 'verification_dossier':
            return self.statut_dossier == 'complet'
        elif self.etape_actuelle == 'attente_facture':
            return self.facture is not None and self.facture_validee_le is not None
        elif self.etape_actuelle == 'facture_validee':
            # La facture est payée, on peut passer à la rédaction du contrat
            return True
        elif self.etape_actuelle == 'redaction_contrat':
            # Le contrat doit être signé pour passer à la visite
            return self.contrat.fichier_contrat and self.contrat.signe_par_locataire and self.contrat.signe_par_bailleur
        elif self.etape_actuelle == 'visite_entree':
            # L'état des lieux doit être uploadé pour passer à la remise des clés
            return bool(self.rapport_etat_lieux)
        elif self.etape_actuelle == 'remise_cles':
            # La remise des clés doit être enregistrée pour terminer
            return self.date_remise_cles is not None
        return False

    def passer_etape_suivante(self):
        """Fait avancer le workflow à l'étape suivante"""
        from .history import HistoriqueWorkflow
        from datetime import timedelta

        etapes_list = [e[0] for e in self.ETAPE_CHOICES]

        if self.etape_actuelle not in etapes_list:
            return False

        index_actuel = etapes_list.index(self.etape_actuelle)

        if index_actuel < len(etapes_list) - 1:
            etape_precedente = self.etape_actuelle
            self.etape_actuelle = etapes_list[index_actuel + 1]

            # Mettre à jour les dates selon l'étape
            if self.etape_actuelle == 'attente_facture':
                self.date_envoi_finance = timezone.now()

                # 🆕 Créer la facture automatiquement
                from apps.payments.models import Invoice
                from apps.core.utils import generate_unique_reference

                # Calculer le montant de la facture initiale
                # = Dépôt de garantie + 1er mois de loyer + charges
                montant_total = (
                    self.contrat.depot_garantie +
                    self.contrat.loyer_mensuel +
                    (self.contrat.charges_mensuelles or 0)
                )

                # Créer la facture
                facture = Invoice.objects.create(
                    numero_facture=generate_unique_reference('INV'),
                    type_facture='loyer',
                    contrat=self.contrat,
                    montant_ht=montant_total,
                    taux_tva=0,  # Pas de TVA sur les loyers
                    montant_ttc=montant_total,
                    description=f"Dépôt de garantie ({self.contrat.depot_garantie:,.0f} FCFA) + 1er mois de loyer ({self.contrat.loyer_mensuel:,.0f} FCFA)",
                    statut='en_attente',
                    date_emission=timezone.now().date(),
                    date_echeance=timezone.now().date() + timedelta(days=7)
                )

                # Lier la facture au workflow
                self.facture = facture

            elif self.etape_actuelle == 'redaction_contrat':
                self.date_debut_redaction = timezone.now()
            elif self.etape_actuelle == 'termine':
                # Activer le contrat
                self.contrat.statut = 'actif'
                self.contrat.save()

            self.save()

            # Créer une entrée dans l'historique
            HistoriqueWorkflow.objects.create(
                workflow=self,
                etape_precedente=etape_precedente,
                etape_suivante=self.etape_actuelle,
                effectue_par=self.responsable_pmo if self.responsable_pmo else self.contrat.cree_par
            )

            return True

        return False
