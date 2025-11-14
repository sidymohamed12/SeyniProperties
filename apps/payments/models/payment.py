from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference
from apps.payments.models.invoice import Invoice

User = get_user_model()


class Payment(BaseModel):
    """Modèle pour les paiements (inchangé)"""
    
    numero_paiement = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de paiement",
        help_text="Généré automatiquement"
    )
    
    facture = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name="Facture"
    )
    
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Montant payé"
    )
    
    date_paiement = models.DateField(
        verbose_name="Date de paiement"
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
            ('autre', 'Autre'),
        ],
        verbose_name="Moyen de paiement"
    )
    
    reference_transaction = models.CharField(
        max_length=100,
        verbose_name="Référence de transaction",
        blank=True
    )
    
    statut = models.CharField(
        max_length=15,
        choices=[
            ('en_attente', 'En attente'),
            ('valide', 'Validé'),
            ('refuse', 'Refusé'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name="Statut"
    )
    
    valide_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        verbose_name="Validé par"
    )
    
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation"
    )
    
    commentaire = models.TextField(
        verbose_name="Commentaire",
        blank=True
    )
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement', '-created_at']
        indexes = [
            models.Index(fields=['numero_paiement']),
            models.Index(fields=['date_paiement']),
            models.Index(fields=['statut']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.numero_paiement:
            self.numero_paiement = generate_unique_reference('PAY')
        super().save(*args, **kwargs)

    def validate_payment(self, user):
        """Valide le paiement"""
        from django.utils import timezone

        if self.statut != 'en_attente':
            raise ValueError("Seuls les paiements en attente peuvent être validés")

        self.statut = 'valide'
        self.valide_par = user
        self.date_validation = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.numero_paiement} - {self.montant} FCFA - {self.facture.numero_facture}"


class PaymentReminder(BaseModel):
    """Modèle pour les rappels de paiement (inchangé)"""
    
    facture = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='rappels',
        verbose_name="Facture"
    )
    
    date_envoi = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'envoi"
    )
    
    type_rappel = models.CharField(
        max_length=15,
        choices=[
            ('automatique', 'Automatique'),
            ('manuel', 'Manuel'),
        ],
        default='automatique',
        verbose_name="Type de rappel"
    )
    
    moyen_envoi = models.CharField(
        max_length=15,
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
        ],
        verbose_name="Moyen d'envoi"
    )
    
    message = models.TextField(
        verbose_name="Message envoyé"
    )
    
    statut = models.CharField(
        max_length=15,
        choices=[
            ('envoye', 'Envoyé'),
            ('echec', 'Échec'),
        ],
        default='envoye',
        verbose_name="Statut"
    )
    
    envoye_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Envoyé par"
    )
    
    class Meta:
        verbose_name = "Rappel de paiement"
        verbose_name_plural = "Rappels de paiement"
        ordering = ['-date_envoi']
    
    def __str__(self):
        return f"Rappel {self.facture.numero_facture} - {self.date_envoi.strftime('%d/%m/%Y')}"

