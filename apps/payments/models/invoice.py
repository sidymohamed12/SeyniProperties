from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference

User = get_user_model()


class Invoice(BaseModel):
    """Modèle pour les factures - Étendu avec nouveaux types"""
    
    # Nouveaux types de factures étendus
    TYPE_FACTURE_CHOICES = [
        ('loyer', 'Facture de Loyer'),
        ('syndic', 'Facture Syndic de Copropriété'),
        ('demande_achat', 'Facture Demande d\'Achat'),
        ('prestataire', 'Facture Prestataire'),
        ('charges', 'Charges'),
        ('penalites', 'Pénalités'),
        ('autres', 'Autres'),
    ]
    
    numero_facture = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de facture",
        help_text="Généré automatiquement"
    )
    
    # Contrat - Optionnel maintenant (null=True pour factures manuelles)
    contrat = models.ForeignKey(
        'contracts.RentalContract',
        on_delete=models.CASCADE,
        related_name='factures',
        verbose_name="Contrat",
        null=True,
        blank=True,
        help_text="Laisser vide pour factures manuelles (syndic, prestataire, etc.)"
    )
    
    type_facture = models.CharField(
        max_length=20,
        choices=TYPE_FACTURE_CHOICES,
        default='loyer',
        verbose_name="Type de facture"
    )
    
    # Périodes - Optionnelles pour certains types
    periode_debut = models.DateField(
        verbose_name="Début de période",
        null=True,
        blank=True
    )
    
    periode_fin = models.DateField(
        verbose_name="Fin de période",
        null=True,
        blank=True
    )
    
    # Informations client/destinataire (pour factures manuelles)
    destinataire_nom = models.CharField(
        max_length=200,
        verbose_name="Nom du destinataire",
        blank=True,
        help_text="Pour factures syndic/prestataire"
    )
    
    destinataire_adresse = models.TextField(
        verbose_name="Adresse du destinataire",
        blank=True
    )
    
    destinataire_email = models.EmailField(
        verbose_name="Email du destinataire",
        blank=True
    )
    
    destinataire_telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone du destinataire",
        blank=True
    )
    
    # Montants
    montant_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant HT"
    )
    
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Taux TVA (%)"
    )
    
    montant_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant TTC"
    )
    
    # Dates
    date_emission = models.DateField(
        verbose_name="Date d'émission"
    )
    
    date_echeance = models.DateField(
        verbose_name="Date d'échéance"
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20,
        choices=[
            ('brouillon', 'Brouillon'),
            ('emise', 'Émise'),
            ('payee', 'Payée'),
            ('en_retard', 'En retard'),
            ('annulee', 'Annulée'),
        ],
        default='brouillon',
        verbose_name="Statut"
    )
    
    # Description et notes
    description = models.TextField(
        verbose_name="Description",
        blank=True,
        help_text="Description détaillée de la facture"
    )
    
    notes = models.TextField(
        verbose_name="Notes internes",
        blank=True
    )
    
    # Champs spécifiques selon le type
    # Pour Syndic
    reference_copropriete = models.CharField(
        max_length=100,
        verbose_name="Référence copropriété",
        blank=True
    )
    
    trimestre = models.CharField(
        max_length=10,
        choices=[
            ('T1', 'Trimestre 1 (Jan-Mar)'),
            ('T2', 'Trimestre 2 (Avr-Jui)'),
            ('T3', 'Trimestre 3 (Jul-Sep)'),
            ('T4', 'Trimestre 4 (Oct-Déc)'),
        ],
        verbose_name="Trimestre",
        blank=True
    )
    
    # Pour Prestataire
    fournisseur_nom = models.CharField(
        max_length=200,
        verbose_name="Nom du fournisseur/prestataire",
        blank=True
    )
    
    fournisseur_reference = models.CharField(
        max_length=100,
        verbose_name="Référence fournisseur",
        blank=True
    )
    
    type_prestation = models.CharField(
        max_length=50,
        choices=[
            ('plomberie', 'Plomberie'),
            ('electricite', 'Électricité'),
            ('menuiserie', 'Menuiserie'),
            ('peinture', 'Peinture'),
            ('nettoyage', 'Nettoyage'),
            ('jardinage', 'Jardinage'),
            ('securite', 'Sécurité'),
            ('autre', 'Autre'),
        ],
        verbose_name="Type de prestation",
        blank=True
    )
    
    # Pour Demande d'achat
    numero_bon_commande = models.CharField(
        max_length=100,
        verbose_name="Numéro de bon de commande",
        blank=True
    )
    
    categorie_achat = models.CharField(
        max_length=50,
        choices=[
            ('materiel', 'Matériel'),
            ('fournitures', 'Fournitures'),
            ('equipement', 'Équipement'),
            ('consommables', 'Consommables'),
            ('autre', 'Autre'),
        ],
        verbose_name="Catégorie d'achat",
        blank=True
    )
    
    # Documents
    fichier_pdf = models.FileField(
        upload_to='invoices/pdf/%Y/%m/',
        verbose_name="Fichier PDF",
        blank=True,
        null=True
    )
    
    fichier_pdf_nom = models.CharField(
        max_length=255,
        verbose_name="Nom personnalisé du fichier PDF",
        blank=True,
        help_text="Nom pour le fichier PDF (sans extension)"
    )
    
    # Métadonnées
    creee_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='factures_creees',
        verbose_name="Créée par"
    )
    
    is_manual = models.BooleanField(
        default=False,
        verbose_name="Facture manuelle",
        help_text="True si créée manuellement (pas liée à un contrat)"
    )

    # 🆕 MODULE 8 : Gestion documents et relances pour bailleur
    etat_loyer_genere = models.BooleanField(
        default=False,
        verbose_name="État de loyer généré",
        help_text="True si l'état de loyer a été généré pour le propriétaire"
    )

    date_generation_etat_loyer = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date génération état loyer"
    )

    fichier_etat_loyer = models.FileField(
        upload_to='invoices/etats_loyer/%Y/%m/',
        verbose_name="Fichier état de loyer",
        blank=True,
        null=True,
        help_text="PDF de l'état de loyer pour le propriétaire"
    )

    quittance_generee = models.BooleanField(
        default=False,
        verbose_name="Quittance générée",
        help_text="True si la quittance a été générée pour le locataire"
    )

    date_generation_quittance = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date génération quittance"
    )

    fichier_quittance = models.FileField(
        upload_to='invoices/quittances/%Y/%m/',
        verbose_name="Fichier quittance",
        blank=True,
        null=True,
        help_text="PDF de la quittance pour le locataire"
    )

    date_derniere_relance = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date dernière relance",
        help_text="Date du dernier rappel de paiement automatique"
    )

    nombre_relances = models.IntegerField(
        default=0,
        verbose_name="Nombre de relances",
        help_text="Compteur de relances envoyées pour cette facture"
    )

    # ========== MODULE 4: WORKFLOW DES DEMANDES D'ACHAT ==========
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
        verbose_name="Étape du workflow",
        blank=True,
        help_text="Pour demandes d'achat uniquement"
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
    date_reception = models.DateTimeField(
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
        related_name='demandes_achat',
        verbose_name="Travail lié",
        help_text="Travail pour lequel cette demande d'achat a été créée"
    )

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission', '-created_at']
        indexes = [
            models.Index(fields=['numero_facture']),
            models.Index(fields=['type_facture']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_emission']),
            models.Index(fields=['date_echeance']),
        ]
    
    def save(self, *args, **kwargs):
        # Génération automatique du numéro de facture
        if not self.numero_facture:
            # Préfixe selon le type
            prefix_map = {
                'loyer': 'FLOY',
                'syndic': 'FSYN',
                'demande_achat': 'FACH',
                'prestataire': 'FPRE',
                'charges': 'FCHA',
                'penalites': 'FPEN',
                'autres': 'FAUT',
            }
            prefix = prefix_map.get(self.type_facture, 'FACT')
            self.numero_facture = generate_unique_reference(prefix)
        
        # Calcul automatique du TTC si non défini
        if self.montant_ht and self.taux_tva is not None:
            tva_amount = (self.montant_ht * self.taux_tva) / Decimal('100')
            self.montant_ttc = self.montant_ht + tva_amount
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_facture} - {self.get_type_facture_display()} - {self.montant_ttc} FCFA"
    
    @property
    def is_overdue(self):
        """Vérifie si la facture est en retard"""
        from django.utils import timezone
        return (
            self.statut in ['emise'] and 
            self.date_echeance < timezone.now().date()
        )
    
    @property
    def solde_restant(self):
        """Calcule le solde restant à payer"""
        total_paye = sum(
            p.montant for p in self.paiements.filter(statut='valide')
        )
        return self.montant_ttc - total_paye
    
    @property
    def montant_paye(self):
        """Calcule le montant déjà payé"""
        return sum(
            p.montant for p in self.paiements.filter(statut='valide')
        )
    
    @property
    def is_fully_paid(self):
        """Vérifie si la facture est entièrement payée"""
        return self.solde_restant <= Decimal('0.00')
    
    def get_client_info(self):
        """Retourne les infos du client selon le type de facture"""
        if self.contrat and self.contrat.locataire:
            # Pour les factures avec contrat
            locataire = self.contrat.locataire

            # Utiliser les attributs directs du Tiers (architecture mise à jour)
            # Le champ 'user' est nullable dans le modèle Tiers
            telephone = locataire.telephone or ''
            email = locataire.email or ''

            # Si le Tiers a un user et que l'email n'est pas renseigné, utiliser l'email du user
            if not email and locataire.user:
                email = locataire.user.email or ''

            return {
                'nom': locataire.nom_complet,  # Utiliser nom_complet du Tiers
                'adresse': f"{self.contrat.appartement.residence.adresse}, {self.contrat.appartement.residence.ville}",
                'email': email,
                'telephone': telephone,
            }
        else:
            # Pour les factures manuelles
            return {
                'nom': self.destinataire_nom or '',
                'adresse': self.destinataire_adresse or '',
                'email': self.destinataire_email or '',
                'telephone': self.destinataire_telephone or '',
            }
