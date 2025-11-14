from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounting.models.expenses import Expense
from apps.core.models import BaseModel

User = get_user_model()

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
        from apps.payments.models.payment import Payment
        
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