# apps/payments/models_extensions.py
"""
Extensions pour le modèle Invoice: workflow d'approbation et demandes d'achat
Ces champs seront ajoutés au modèle Invoice via une migration
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from apps.core.models import BaseModel

User = get_user_model()


# ========== CHAMPS À AJOUTER AU MODÈLE INVOICE ==========
"""
Ces champs seront ajoutés au modèle Invoice existant via une migration:

# ========== WORKFLOW D'APPROBATION ==========
etape_workflow = models.CharField(
    max_length=25,
    choices=[
        ('brouillon', 'Brouillon'),
        ('en_attente', 'En attente de validation'),
        ('valide_responsable', 'Validé par responsable'),
        ('comptable', 'En traitement comptable'),
        ('validation_dg', 'En attente validation DG'),
        ('approuve', 'Approuvé - En attente achat'),
        ('en_cours_achat', 'Achat en cours'),
        ('recue', 'Marchandise reçue'),
        ('paye', 'Payé'),
        ('refuse', 'Refusé'),
        ('annule', 'Annulé'),
    ],
    default='brouillon',
    verbose_name="Étape du workflow"
)

# ========== DEMANDEUR (pour demandes d'achat) ==========
demandeur = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='demandes_achat_effectuees',
    verbose_name="Demandeur"
)

date_demande = models.DateField(
    null=True,
    blank=True,
    verbose_name="Date de la demande"
)

service_fonction = models.CharField(
    max_length=100,
    blank=True,
    verbose_name="Service/Fonction"
)

motif_principal = models.TextField(
    blank=True,
    verbose_name="Motif principal de la demande"
)

# ========== APPROBATION RESPONSABLE ==========
signature_demandeur_date = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Date signature demandeur"
)

valide_par_responsable = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='demandes_validees_responsable',
    verbose_name="Validé par (responsable)"
)

date_validation_responsable = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Date validation responsable"
)

commentaire_responsable = models.TextField(
    blank=True,
    verbose_name="Commentaire du responsable"
)

# ========== TRAITEMENT COMPTABLE ==========
traite_par_comptable = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='factures_traitees_comptable',
    verbose_name="Traité par (comptable)"
)

date_traitement_comptable = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Date traitement comptable"
)

commentaire_comptable = models.TextField(
    blank=True,
    verbose_name="Commentaire du comptable"
)

# ========== CHÈQUE ==========
numero_cheque = models.CharField(
    max_length=50,
    blank=True,
    verbose_name="Numéro de chèque"
)

banque_cheque = models.CharField(
    max_length=100,
    blank=True,
    verbose_name="Banque émettrice du chèque"
)

date_emission_cheque = models.DateField(
    null=True,
    blank=True,
    verbose_name="Date d'émission du chèque"
)

beneficiaire_cheque = models.CharField(
    max_length=200,
    blank=True,
    verbose_name="Bénéficiaire du chèque"
)

# ========== VALIDATION DIRECTION GÉNÉRALE ==========
valide_par_dg = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='factures_validees_dg',
    verbose_name="Validé par (Direction Générale)"
)

date_validation_dg = models.DateTimeField(
    null=True,
    blank=True,
    verbose_name="Date validation DG"
)

commentaire_dg = models.TextField(
    blank=True,
    verbose_name="Commentaire de la DG"
)

# ========== RÉCEPTION MARCHANDISE ==========
date_reception = models.DateField(
    null=True,
    blank=True,
    verbose_name="Date de réception de la marchandise"
)

receptionne_par = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='receptions_marchandises',
    verbose_name="Réceptionné par"
)

remarques_reception = models.TextField(
    blank=True,
    verbose_name="Remarques sur la réception"
)

# ========== LIEN AVEC TRAVAIL ==========
travail_lie = models.ForeignKey(
    'maintenance.Travail',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='demandes_achat_liees',
    verbose_name="Travail lié"
)
"""


# ========== NOUVEAU MODÈLE: LIGNE DE DEMANDE D'ACHAT ==========
class LigneDemandeAchat(BaseModel):
    """
    Ligne d'article dans une demande d'achat
    Permet de détailler chaque article/matériel demandé
    """

    demande = models.ForeignKey(
        'payments.Invoice',
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


# ========== HISTORIQUE DES VALIDATIONS ==========
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
        'payments.Invoice',
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
