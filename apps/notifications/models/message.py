from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel
from apps.notifications.models.notification import Notification

User = get_user_model()

class MessageTemplate(BaseModel):
    """Modèle pour les templates de messages"""
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code du template",
        help_text="Identifiant unique (ex: WELCOME_TENANT)"
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du template"
    )
    
    type_notification = models.CharField(
        max_length=30,
        choices=[
            ('welcome', 'Bienvenue'),
            ('payment_reminder', 'Rappel de paiement'),
            ('contract_expiry', 'Expiration contrat'),
            ('intervention_assigned', 'Intervention assignée'),
            ('intervention_completed', 'Intervention terminée'),
            ('task_assigned', 'Tâche assignée'),
            ('account_created', 'Compte créé'),
            ('password_reset', 'Réinitialisation mot de passe'),
            ('maintenance_scheduled', 'Maintenance programmée'),
            ('invoice_generated', 'Facture générée'),
            ('payment_received', 'Paiement reçu'),
            ('autres', 'Autres'),
        ],
        verbose_name="Type de notification"
    )
    
    canal = models.CharField(
        max_length=15,
        choices=[
            ('sms', 'SMS'),
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
        ],
        verbose_name="Canal de communication"
    )
    
    sujet_template = models.CharField(
        max_length=200,
        verbose_name="Template du sujet",
        blank=True,
        help_text="Utilisé pour les emails"
    )
    
    message_template = models.TextField(
        verbose_name="Template du message",
        help_text="Utilisez {{variable}} pour les variables dynamiques"
    )
    
    variables_disponibles = models.JSONField(
        default=list,
        verbose_name="Variables disponibles",
        help_text="Liste des variables utilisables dans le template"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Template actif"
    )
    
    langue = models.CharField(
        max_length=5,
        choices=[
            ('fr', 'Français'),
            ('wo', 'Wolof'),
            ('en', 'Anglais'),
        ],
        default='fr',
        verbose_name="Langue"
    )
    
    class Meta:
        verbose_name = "Template de message"
        verbose_name_plural = "Templates de messages"
        ordering = ['nom']
        unique_together = [['code', 'langue']]
    
    def __str__(self):
        return f"{self.nom} ({self.get_canal_display()}) - {self.get_langue_display()}"
    
    def render_message(self, variables=None):
        """Rend le message avec les variables fournies"""
        if not variables:
            variables = {}
        
        # Remplacer les variables dans le message
        message = self.message_template
        sujet = self.sujet_template
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            message = message.replace(placeholder, str(value))
            if sujet:
                sujet = sujet.replace(placeholder, str(value))
        
        return {
            'sujet': sujet,
            'message': message
        }
    
    @classmethod
    def get_template(cls, code, canal, langue='fr'):
        """Récupère un template par son code"""
        try:
            return cls.objects.get(
                code=code,
                canal=canal,
                langue=langue,
                is_active=True
            )
        except cls.DoesNotExist:
            # Fallback sur le français si la langue demandée n'existe pas
            if langue != 'fr':
                try:
                    return cls.objects.get(
                        code=code,
                        canal=canal,
                        langue='fr',
                        is_active=True
                    )
                except cls.DoesNotExist:
                    pass
            return None


class WhatsAppMessage(BaseModel):
    """Modèle pour tracker les messages WhatsApp"""
    
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='whatsapp_message',
        verbose_name="Notification"
    )
    
    whatsapp_id = models.CharField(
        max_length=100,
        verbose_name="ID WhatsApp",
        help_text="ID du message retourné par l'API WhatsApp"
    )
    
    statut_whatsapp = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Envoyé'),
            ('delivered', 'Livré'),
            ('read', 'Lu'),
            ('failed', 'Échec'),
        ],
        default='sent',
        verbose_name="Statut WhatsApp"
    )
    
    date_delivered = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de livraison"
    )
    
    date_read = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )
    
    webhook_data = models.JSONField(
        default=dict,
        verbose_name="Données webhook",
        blank=True
    )
    
    class Meta:
        verbose_name = "Message WhatsApp"
        verbose_name_plural = "Messages WhatsApp"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"WhatsApp {self.whatsapp_id} - {self.statut_whatsapp}"
    
    def update_status(self, new_status, webhook_data=None):
        """Met à jour le statut du message WhatsApp"""
        from django.utils import timezone
        
        self.statut_whatsapp = new_status
        
        if webhook_data:
            self.webhook_data.update(webhook_data)
        
        now = timezone.now()
        
        if new_status == 'delivered' and not self.date_delivered:
            self.date_delivered = now
        elif new_status == 'read' and not self.date_read:
            self.date_read = now
            # Marquer aussi la notification comme lue
            self.notification.mark_as_read()
        elif new_status == 'failed':
            self.notification.mark_as_failed("Échec WhatsApp")
        
        self.save()


class SMSMessage(BaseModel):
    """Modèle pour tracker les messages SMS"""
    
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='sms_message',
        verbose_name="Notification"
    )
    
    sms_id = models.CharField(
        max_length=100,
        verbose_name="ID SMS",
        help_text="ID du message retourné par l'API SMS"
    )
    
    provider = models.CharField(
        max_length=20,
        choices=[
            ('orange', 'Orange SMS API'),
            ('tigo', 'Tigo SMS API'),
            ('bulk_sms', 'Bulk SMS'),
            ('twilio', 'Twilio'),
        ],
        verbose_name="Fournisseur SMS"
    )
    
    statut_sms = models.CharField(
        max_length=20,
        choices=[
            ('sent', 'Envoyé'),
            ('delivered', 'Livré'),
            ('failed', 'Échec'),
            ('expired', 'Expiré'),
        ],
        default='sent',
        verbose_name="Statut SMS"
    )
    
    date_delivered = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de livraison"
    )
    
    cout = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Coût du SMS"
    )
    
    callback_data = models.JSONField(
        default=dict,
        verbose_name="Données callback",
        blank=True
    )
    
    class Meta:
        verbose_name = "Message SMS"
        verbose_name_plural = "Messages SMS"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SMS {self.sms_id} via {self.provider} - {self.statut_sms}"
    
    def update_status(self, new_status, callback_data=None):
        """Met à jour le statut du message SMS"""
        from django.utils import timezone
        
        self.statut_sms = new_status
        
        if callback_data:
            self.callback_data.update(callback_data)
        
        if new_status == 'delivered' and not self.date_delivered:
            self.date_delivered = timezone.now()
        elif new_status == 'failed':
            self.notification.mark_as_failed("Échec SMS")
        
        self.save()
