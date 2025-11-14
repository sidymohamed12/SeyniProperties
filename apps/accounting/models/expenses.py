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
