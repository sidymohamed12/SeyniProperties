from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounting.models.expenses import Expense
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference

User = get_user_model()

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
                    ).aggregate(sum('montant'))['montant__sum'] or Decimal('0.00')
                    
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

