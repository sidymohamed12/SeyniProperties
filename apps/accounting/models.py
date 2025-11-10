from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference

User = get_user_model()


class Expense(BaseModel):
    """Modèle pour les dépenses"""
    
    numero_expense = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de dépense",
        help_text="Généré automatiquement"
    )
    
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name="Bien concerné",
        help_text="Laisser vide pour les dépenses générales"
    )
    
    categorie = models.CharField(
        max_length=30,
        choices=[
            ('maintenance', 'Maintenance'),
            ('reparation', 'Réparation'),
            ('amenagement', 'Aménagement'),
            ('marketing', 'Marketing'),
            ('assurance', 'Assurance'),
            ('taxes', 'Taxes et impôts'),
            ('fournitures', 'Fournitures'),
            ('transport', 'Transport'),
            ('communication', 'Communication'),
            ('salaires', 'Salaires'),
            ('autres', 'Autres'),
        ],
        verbose_name="Catégorie"
    )
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de la dépense"
    )
    
    description = models.TextField(
        verbose_name="Description",
        blank=True
    )
    
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant"
    )
    
    date_expense = models.DateField(
        verbose_name="Date de la dépense"
    )
    
    fournisseur = models.CharField(
        max_length=100,
        verbose_name="Fournisseur",
        blank=True
    )
    
    numero_facture_fournisseur = models.CharField(
        max_length=100,
        verbose_name="Numéro facture fournisseur",
        blank=True
    )
    
    moyen_paiement = models.CharField(
        max_length=20,
        choices=[
            ('especes', 'Espèces'),
            ('virement', 'Virement'),
            ('cheque', 'Chèque'),
            ('carte', 'Carte bancaire'),
            ('orange_money', 'Orange Money'),
            ('wave', 'Wave'),
        ],
        verbose_name="Moyen de paiement"
    )
    
    statut = models.CharField(
        max_length=15,
        choices=[
            ('brouillon', 'Brouillon'),
            ('valide', 'Validé'),
            ('paye', 'Payé'),
            ('rembourse', 'Remboursé'),
        ],
        default='brouillon',
        verbose_name="Statut"
    )
    
    # Fichiers justificatifs
    facture_fichier = models.FileField(
        upload_to='expenses/invoices/',
        verbose_name="Facture",
        blank=True,
        null=True
    )
    
    recu_paiement = models.FileField(
        upload_to='expenses/receipts/',
        verbose_name="Reçu de paiement",
        blank=True,
        null=True
    )
    
    # Validation
    saisie_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='expenses_saisies',
        verbose_name="Saisi par"
    )
    
    valide_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses_validees',
        verbose_name="Validé par"
    )
    
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    
    # Comptabilité
    is_deductible = models.BooleanField(
        default=True,
        verbose_name="Déductible fiscalement"
    )
    
    notes = models.TextField(
        verbose_name="Notes",
        blank=True
    )
    
    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-date_expense', '-created_at']
        indexes = [
            models.Index(fields=['numero_expense']),
            models.Index(fields=['categorie']),
            models.Index(fields=['date_expense']),
            models.Index(fields=['statut']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.numero_expense:
            self.numero_expense = generate_unique_reference('EXP')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_expense} - {self.titre} - {self.montant}€"
    
    def validate_expense(self, validated_by):
        """Valide la dépense"""
        from django.utils import timezone
        
        self.statut = 'valide'
        self.valide_par = validated_by
        self.date_validation = timezone.now()
        self.save()


class LandlordStatement(BaseModel):
    """Modèle pour les relevés de compte des bailleurs"""
    
    numero_releve = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de relevé",
        help_text="Généré automatiquement"
    )
    
    proprietaire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='releves',
        verbose_name="Propriétaire",
        limit_choices_to={'type_tiers': 'proprietaire'}
    )
    
    # Période
    periode_debut = models.DateField(
        verbose_name="Début de période"
    )
    
    periode_fin = models.DateField(
        verbose_name="Fin de période"
    )
    
    # Totaux
    total_encaisse = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total encaissé"
    )
    
    commission_agence = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Commission agence"
    )
    
    total_depenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total dépenses"
    )
    
    montant_a_verser = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant à verser"
    )
    
    nb_biens_concernes = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de biens concernés"
    )
    
    # Statut
    statut = models.CharField(
        max_length=15,
        choices=[
            ('brouillon', 'Brouillon'),
            ('envoye', 'Envoyé'),
            ('paye', 'Payé'),
        ],
        default='brouillon',
        verbose_name="Statut"
    )
    
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'envoi"
    )
    
    moyen_envoi = models.CharField(
        max_length=15,
        choices=[
            ('email', 'Email'),
            ('whatsapp', 'WhatsApp'),
            ('sms', 'SMS'),
        ],
        blank=True,
        verbose_name="Moyen d'envoi"
    )
    
    # Fichier PDF généré
    fichier_pdf = models.FileField(
        upload_to='statements/pdf/',
        verbose_name="Fichier PDF",
        blank=True,
        null=True
    )
    
    # Métadonnées
    genere_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='releves_generes',
        verbose_name="Généré par"
    )
    
    notes = models.TextField(
        verbose_name="Notes",
        blank=True
    )
    
    class Meta:
        verbose_name = "Relevé propriétaire"
        verbose_name_plural = "Relevés propriétaires"
        ordering = ['-periode_fin', '-created_at']
        unique_together = [['proprietaire', 'periode_debut', 'periode_fin']]
        indexes = [
            models.Index(fields=['numero_releve']),
            models.Index(fields=['periode_debut', 'periode_fin']),
            models.Index(fields=['statut']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.numero_releve:
            self.numero_releve = generate_unique_reference('REL')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_releve} - {self.proprietaire.nom_complet} ({self.periode_debut} au {self.periode_fin})"
    
    def calculate_totals(self):
        """Calcule les totaux du relevé"""
        from django.db.models import Sum
        from apps.payments.models import Payment
        from apps.contracts.models import RentalContract
        
        # Récupérer tous les biens du bailleur
        biens = self.bailleur.biens.all()
        self.nb_biens_concernes = biens.count()
        
        # Calculer le total encaissé
        total_encaisse = Payment.objects.filter(
            facture__contrat__bien__in=biens,
            facture__contrat__bien__bailleur=self.bailleur,
            date_paiement__range=[self.periode_debut, self.periode_fin],
            statut='valide'
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
        
        self.total_encaisse = total_encaisse
        
        # Calculer les dépenses liées aux biens du bailleur
        total_depenses = Expense.objects.filter(
            bien__in=biens,
            date_expense__range=[self.periode_debut, self.periode_fin],
            statut='valide'
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
        
        self.total_depenses = total_depenses
        
        # Calculer la commission (exemple: 10%)
        taux_commission = self.bailleur.taux_commission or Decimal('10.00')
        self.commission_agence = (self.total_encaisse * taux_commission) / 100
        
        # Calculer le montant à verser
        self.montant_a_verser = self.total_encaisse - self.commission_agence - self.total_depenses
        
        self.save()
    
    def generate_details(self):
        """Génère les détails du relevé"""
        from apps.payments.models import Payment
        from apps.contracts.models import RentalContract
        
        # Supprimer les anciens détails
        self.details.all().delete()
        
        # Créer les détails pour chaque bien
        for bien in self.bailleur.biens.all():
            contrats = RentalContract.objects.filter(
                bien=bien,
                date_debut__lte=self.periode_fin,
                date_fin__gte=self.periode_debut
            )
            
            for contrat in contrats:
                # Calculer les paiements pour ce contrat
                paiements = Payment.objects.filter(
                    facture__contrat=contrat,
                    date_paiement__range=[self.periode_debut, self.periode_fin],
                    statut='valide'
                )
                
                if paiements.exists():
                    montant_loyer = sum(p.montant for p in paiements if p.facture.type_facture == 'loyer')
                    montant_charges = sum(p.montant for p in paiements if p.facture.type_facture == 'charges')
                    
                    # Calculer les dépenses pour ce bien
                    depenses_bien = Expense.objects.filter(
                        bien=bien,
                        date_expense__range=[self.periode_debut, self.periode_fin],
                        statut='valide'
                    ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
                    
                    # Calculer la commission
                    total_bien = montant_loyer + montant_charges
                    taux_commission = self.bailleur.taux_commission or Decimal('10.00')
                    commission_bien = (total_bien * taux_commission) / 100
                    
                    # Créer le détail
                    LandlordStatementDetail.objects.create(
                        releve=self,
                        bien=bien,
                        contrat=contrat,
                        montant_loyer=montant_loyer,
                        montant_charges=montant_charges,
                        total_depenses=depenses_bien,
                        commission_pourcentage=taux_commission,
                        commission_montant=commission_bien,
                        net_bailleur=total_bien - commission_bien - depenses_bien
                    )


class LandlordStatementDetail(BaseModel):
    """Modèle pour les détails des relevés bailleurs"""
    
    releve = models.ForeignKey(
        LandlordStatement,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name="Relevé"
    )
    
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        verbose_name="Bien"
    )
    
    contrat = models.ForeignKey(
        'contracts.RentalContract',
        on_delete=models.CASCADE,
        verbose_name="Contrat"
    )
    
    # Montants
    montant_loyer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant loyer"
    )
    
    montant_charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant charges"
    )
    
    total_depenses = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total dépenses"
    )
    
    commission_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Commission (%)"
    )
    
    commission_montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Commission (montant)"
    )
    
    net_bailleur = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Net bailleur"
    )
    
    class Meta:
        verbose_name = "Détail relevé bailleur"
        verbose_name_plural = "Détails relevés bailleurs"
        ordering = ['bien__reference']  # Changé de 'bien__nom' vers 'bien__reference'
    
    def __str__(self):
        return f"{self.releve.numero_releve} - {self.bien.nom}"
    
    @property
    def total_encaisse(self):
        """Total encaissé pour ce bien"""
        return self.montant_loyer + self.montant_charges


class AccountingPeriod(BaseModel):
    """Modèle pour les périodes comptables"""
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la période"
    )
    
    date_debut = models.DateField(
        verbose_name="Date de début"
    )
    
    date_fin = models.DateField(
        verbose_name="Date de fin"
    )
    
    is_closed = models.BooleanField(
        default=False,
        verbose_name="Période clôturée"
    )
    
    date_cloture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de clôture"
    )
    
    cloture_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Clôturé par"
    )
    
    # Totaux de la période
    total_revenus = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total revenus"
    )
    
    total_depenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total dépenses"
    )
    
    resultat_net = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Résultat net"
    )
    
    notes = models.TextField(
        verbose_name="Notes",
        blank=True
    )
    
    class Meta:
        verbose_name = "Période comptable"
        verbose_name_plural = "Périodes comptables"
        ordering = ['-date_debut']
        unique_together = [['date_debut', 'date_fin']]
    
    def __str__(self):
        return f"{self.nom} ({self.date_debut} au {self.date_fin})"
    
    def calculate_totals(self):
        """Calcule les totaux de la période"""
        from django.db.models import Sum
        from apps.payments.models import Payment
        
        # Calculer les revenus (paiements validés)
        self.total_revenus = Payment.objects.filter(
            date_paiement__range=[self.date_debut, self.date_fin],
            statut='valide'
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
        
        # Calculer les dépenses
        self.total_depenses = Expense.objects.filter(
            date_expense__range=[self.date_debut, self.date_fin],
            statut='valide'
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
        
        # Calculer le résultat net
        self.resultat_net = self.total_revenus - self.total_depenses
        
        self.save()
    
    def close_period(self, closed_by):
        """Clôture la période comptable"""
        from django.utils import timezone
        
        if self.is_closed:
            return False
        
        # Calculer les totaux finaux
        self.calculate_totals()
        
        # Marquer comme clôturée
        self.is_closed = True
        self.date_cloture = timezone.now()
        self.cloture_par = closed_by
        self.save()
        
        return True


class TaxDeclaration(BaseModel):
    """Modèle pour les déclarations fiscales"""
    
    periode = models.ForeignKey(
        AccountingPeriod,
        on_delete=models.CASCADE,
        related_name='declarations_fiscales',
        verbose_name="Période comptable"
    )
    
    type_declaration = models.CharField(
        max_length=25,  # Augmenté de 20 à 25
        choices=[
            ('tva', 'TVA'),
            ('impot_societe', 'Impôt sur les sociétés'),
            ('contribution_fonciere', 'Contribution foncière'),
            ('autres', 'Autres'),
        ],
        verbose_name="Type de déclaration"
    )
    
    montant_du = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Montant dû"
    )
    
    date_echeance = models.DateField(
        verbose_name="Date d'échéance"
    )
    
    statut = models.CharField(
        max_length=15,
        choices=[
            ('calcule', 'Calculé'),
            ('declare', 'Déclaré'),
            ('paye', 'Payé'),
            ('en_retard', 'En retard'),
        ],
        default='calcule',
        verbose_name="Statut"
    )
    
    date_paiement = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de paiement"
    )
    
    reference_paiement = models.CharField(
        max_length=100,
        verbose_name="Référence de paiement",
        blank=True
    )
    
    fichier_declaration = models.FileField(
        upload_to='tax/declarations/',
        verbose_name="Fichier de déclaration",
        blank=True,
        null=True
    )
    
    notes = models.TextField(
        verbose_name="Notes",
        blank=True
    )
    
    class Meta:
        verbose_name = "Déclaration fiscale"
        verbose_name_plural = "Déclarations fiscales"
        ordering = ['-date_echeance']
        unique_together = [['periode', 'type_declaration']]
    
    def __str__(self):
        return f"{self.type_declaration} - {self.periode.nom} - {self.montant_du}€"
    
    @property
    def is_overdue(self):
        """Vérifie si la déclaration est en retard"""
        from django.utils import timezone
        return (
            self.statut in ['calcule', 'declare'] and 
            self.date_echeance < timezone.now().date()
        )