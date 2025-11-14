from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from apps.core.models import BaseModel
from apps.notifications.models.message import MessageTemplate, SMSMessage, WhatsAppMessage

User = get_user_model()


class Notification(BaseModel):
    """Modèle pour les notifications envoyées"""
    
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_recues',
        verbose_name="Destinataire"
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
            ('system_alert', 'Alerte système'),
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
            ('app', 'Application'),
        ],
        verbose_name="Canal utilisé"
    )
    
    # Coordonnées de contact
    telephone = models.CharField(
        max_length=20,
        verbose_name="Numéro de téléphone",
        blank=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{8,15}$',
            message="Numéro de téléphone invalide"
        )]
    )
    
    email = models.EmailField(
        verbose_name="Adresse email",
        blank=True
    )
    
    # Contenu du message
    sujet = models.CharField(
        max_length=200,
        verbose_name="Sujet",
        blank=True
    )
    
    message = models.TextField(
        verbose_name="Message"
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=15,
        choices=[
            ('en_attente', 'En attente'),
            ('programme', 'Programmé'),
            ('envoye', 'Envoyé'),
            ('echec', 'Échec'),
            ('lu', 'Lu'),
        ],
        default='en_attente',
        verbose_name="Statut"
    )
    
    date_programmee = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date programmée"
    )
    
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'envoi"
    )
    
    date_lecture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )
    
    # Gestion des tentatives
    tentatives = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de tentatives"
    )
    
    max_tentatives = models.PositiveIntegerField(
        default=3,
        verbose_name="Maximum de tentatives"
    )
    
    # Réponse du service
    response_id = models.CharField(
        max_length=100,
        verbose_name="ID de réponse du service",
        blank=True,
        help_text="ID retourné par le service (WhatsApp/SMS)"
    )
    
    erreur_message = models.TextField(
        verbose_name="Message d'erreur",
        blank=True
    )
    
    # Métadonnées
    template_utilise = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Template utilisé"
    )
    
    variables_utilisees = models.JSONField(
        default=dict,
        verbose_name="Variables utilisées",
        blank=True
    )
    
    envoye_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_envoyees',
        verbose_name="Envoyé par"
    )
    
    # Relation avec d'autres objets
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Type d'objet lié"
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID de l'objet lié"
    )
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['destinataire', 'statut']),
            models.Index(fields=['type_notification']),
            models.Index(fields=['date_programmee']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"{self.get_type_notification_display()} pour {self.destinataire.username} - {self.get_statut_display()}"
    
    def mark_as_sent(self, response_id=None):
        """Marque la notification comme envoyée"""
        from django.utils import timezone
        
        self.statut = 'envoye'
        self.date_envoi = timezone.now()
        if response_id:
            self.response_id = response_id
        self.save(update_fields=['statut', 'date_envoi', 'response_id'])
    
    def mark_as_failed(self, error_message=""):
        """Marque la notification comme échouée"""
        self.statut = 'echec'
        self.erreur_message = error_message
        self.tentatives += 1
        self.save(update_fields=['statut', 'erreur_message', 'tentatives'])
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        from django.utils import timezone
        
        if self.statut == 'envoye':
            self.statut = 'lu'
            self.date_lecture = timezone.now()
            self.save(update_fields=['statut', 'date_lecture'])
    
    def can_retry(self):
        """Vérifie si on peut réessayer d'envoyer la notification"""
        return (
            self.statut == 'echec' and 
            self.tentatives < self.max_tentatives
        )
    
    def retry(self):
        """Remet la notification en attente pour un nouvel essai"""
        if self.can_retry():
            self.statut = 'en_attente'
            self.erreur_message = ""
            self.save(update_fields=['statut', 'erreur_message'])
            return True
        return False


class NotificationConfig(BaseModel):
    """Modèle pour la configuration des notifications par utilisateur"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_config',
        verbose_name="Utilisateur"
    )
    
    # Préférences de canal
    receive_sms = models.BooleanField(
        default=True,
        verbose_name="Recevoir les SMS"
    )
    
    receive_whatsapp = models.BooleanField(
        default=True,
        verbose_name="Recevoir les WhatsApp"
    )
    
    receive_email = models.BooleanField(
        default=True,
        verbose_name="Recevoir les emails"
    )
    
    receive_app_notifications = models.BooleanField(
        default=True,
        verbose_name="Recevoir les notifications app"
    )
    
    # Préférences par type de notification
    rappel_paiement = models.BooleanField(
        default=True,
        verbose_name="Rappels de paiement"
    )
    
    rappel_paiement_jours = models.PositiveIntegerField(
        default=3,
        verbose_name="Rappel X jours avant échéance"
    )
    
    interventions = models.BooleanField(
        default=True,
        verbose_name="Notifications d'interventions"
    )
    
    contrats = models.BooleanField(
        default=True,
        verbose_name="Notifications de contrats"
    )
    
    taches = models.BooleanField(
        default=True,
        verbose_name="Notifications de tâches"
    )
    
    # Préférences linguistiques
    langue_preference = models.CharField(
        max_length=5,
        choices=[
            ('fr', 'Français'),
            ('wo', 'Wolof'),
            ('en', 'Anglais'),
        ],
        default='fr',
        verbose_name="Langue préférée"
    )
    
    # Heures de notification
    heure_debut_notifications = models.TimeField(
        default='08:00',
        verbose_name="Heure de début des notifications"
    )
    
    heure_fin_notifications = models.TimeField(
        default='20:00',
        verbose_name="Heure de fin des notifications"
    )
    
    # Jours de la semaine
    notifications_weekend = models.BooleanField(
        default=False,
        verbose_name="Notifications le weekend"
    )
    
    class Meta:
        verbose_name = "Configuration notification"
        verbose_name_plural = "Configurations notifications"
    
    def __str__(self):
        return f"Config notifications - {self.user.username}"
    
    def can_receive_notification(self, canal, type_notification=None, heure=None):
        """Vérifie si l'utilisateur peut recevoir une notification"""
        from django.utils import timezone
        
        # Vérifier le canal
        if canal == 'sms' and not self.receive_sms:
            return False
        elif canal == 'whatsapp' and not self.receive_whatsapp:
            return False
        elif canal == 'email' and not self.receive_email:
            return False
        elif canal == 'app' and not self.receive_app_notifications:
            return False
        
        # Vérifier le type de notification
        if type_notification == 'payment_reminder' and not self.rappel_paiement:
            return False
        elif type_notification in ['intervention_assigned', 'intervention_completed'] and not self.interventions:
            return False
        elif type_notification == 'contract_expiry' and not self.contrats:
            return False
        elif type_notification == 'task_assigned' and not self.taches:
            return False
        
        # Vérifier l'heure
        if heure is None:
            heure = timezone.now().time()
        
        if not (self.heure_debut_notifications <= heure <= self.heure_fin_notifications):
            return False
        
        # Vérifier le weekend
        if not self.notifications_weekend:
            today = timezone.now().weekday()
            if today >= 5:  # Samedi = 5, Dimanche = 6
                return False
        
        return True


class NotificationQueue(BaseModel):
    """Modèle pour la file d'attente des notifications"""
    
    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name='queue_item',
        verbose_name="Notification"
    )
    
    priorite = models.CharField(
        max_length=10,
        choices=[
            ('basse', 'Basse'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
            ('urgente', 'Urgente'),
        ],
        default='normale',
        verbose_name="Priorité"
    )
    
    date_traitement_prevue = models.DateTimeField(
        verbose_name="Date de traitement prévue"
    )
    
    en_cours_traitement = models.BooleanField(
        default=False,
        verbose_name="En cours de traitement"
    )
    
    worker_id = models.CharField(
        max_length=50,
        verbose_name="ID du worker",
        blank=True,
        help_text="ID du processus qui traite la notification"
    )
    
    date_debut_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Début du traitement"
    )
    
    class Meta:
        verbose_name = "File d'attente notification"
        verbose_name_plural = "File d'attente notifications"
        ordering = ['-priorite', 'date_traitement_prevue']
        indexes = [
            models.Index(fields=['date_traitement_prevue']),
            models.Index(fields=['priorite']),
            models.Index(fields=['en_cours_traitement']),
        ]
    
    def __str__(self):
        return f"Queue: {self.notification} (Priorité: {self.priorite})"
    
    def start_processing(self, worker_id):
        """Démarre le traitement de la notification"""
        from django.utils import timezone
        
        self.en_cours_traitement = True
        self.worker_id = worker_id
        self.date_debut_traitement = timezone.now()
        self.save(update_fields=['en_cours_traitement', 'worker_id', 'date_debut_traitement'])
    
    def finish_processing(self):
        """Termine le traitement et supprime de la queue"""
        self.delete()


class NotificationStatistics(BaseModel):
    """Modèle pour les statistiques des notifications"""
    
    date_stats = models.DateField(
        unique=True,
        verbose_name="Date des statistiques"
    )
    
    # Statistiques par canal
    sms_envoyes = models.PositiveIntegerField(
        default=0,
        verbose_name="SMS envoyés"
    )
    
    sms_delivres = models.PositiveIntegerField(
        default=0,
        verbose_name="SMS livrés"
    )
    
    whatsapp_envoyes = models.PositiveIntegerField(
        default=0,
        verbose_name="WhatsApp envoyés"
    )
    
    whatsapp_delivres = models.PositiveIntegerField(
        default=0,
        verbose_name="WhatsApp livrés"
    )
    
    whatsapp_lus = models.PositiveIntegerField(
        default=0,
        verbose_name="WhatsApp lus"
    )
    
    emails_envoyes = models.PositiveIntegerField(
        default=0,
        verbose_name="Emails envoyés"
    )
    
    # Statistiques par type
    welcomes_envoyes = models.PositiveIntegerField(
        default=0,
        verbose_name="Messages de bienvenue"
    )
    
    rappels_paiement = models.PositiveIntegerField(
        default=0,
        verbose_name="Rappels de paiement"
    )
    
    notifications_interventions = models.PositiveIntegerField(
        default=0,
        verbose_name="Notifications d'interventions"
    )
    
    # Statistiques d'échec
    total_echecs = models.PositiveIntegerField(
        default=0,
        verbose_name="Total échecs"
    )
    
    # Coûts
    cout_total_sms = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Coût total SMS"
    )
    
    class Meta:
        verbose_name = "Statistiques notifications"
        verbose_name_plural = "Statistiques notifications"
        ordering = ['-date_stats']
    
    def __str__(self):
        return f"Stats notifications du {self.date_stats}"
    
    @classmethod
    def generate_daily_stats(cls, date=None):
        """Génère les statistiques pour une date donnée"""
        from django.utils import timezone
        from django.db.models import Count, Sum
        
        if not date:
            date = timezone.now().date()
        
        # Compter les notifications par canal et statut
        notifications = Notification.objects.filter(
            date_envoi__date=date
        )
        
        stats = {
            'sms_envoyes': notifications.filter(canal='sms', statut__in=['envoye', 'lu']).count(),
            'whatsapp_envoyes': notifications.filter(canal='whatsapp', statut__in=['envoye', 'lu']).count(),
            'emails_envoyes': notifications.filter(canal='email', statut__in=['envoye', 'lu']).count(),
            'total_echecs': notifications.filter(statut='echec').count(),
        }
        
        # Statistiques WhatsApp détaillées
        whatsapp_messages = WhatsAppMessage.objects.filter(
            notification__date_envoi__date=date
        )
        stats['whatsapp_delivres'] = whatsapp_messages.filter(statut_whatsapp='delivered').count()
        stats['whatsapp_lus'] = whatsapp_messages.filter(statut_whatsapp='read').count()
        
        # Statistiques SMS détaillées
        sms_messages = SMSMessage.objects.filter(
            notification__date_envoi__date=date
        )
        stats['sms_delivres'] = sms_messages.filter(statut_sms='delivered').count()
        
        # Coût total SMS
        cout_sms = sms_messages.aggregate(
            total=Sum('cout')
        )['total'] or 0
        stats['cout_total_sms'] = cout_sms
        
        # Statistiques par type
        stats['welcomes_envoyes'] = notifications.filter(
            type_notification='welcome',
            statut__in=['envoye', 'lu']
        ).count()
        
        stats['rappels_paiement'] = notifications.filter(
            type_notification='payment_reminder',
            statut__in=['envoye', 'lu']
        ).count()
        
        stats['notifications_interventions'] = notifications.filter(
            type_notification__in=['intervention_assigned', 'intervention_completed'],
            statut__in=['envoye', 'lu']
        ).count()
        
        # Créer ou mettre à jour les statistiques
        obj, created = cls.objects.update_or_create(
            date_stats=date,
            defaults=stats
        )
        
        return obj


class NotificationLog(BaseModel):
    """Modèle pour les logs détaillés des notifications"""
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name="Notification"
    )
    
    action = models.CharField(
        max_length=20,
        choices=[
            ('created', 'Créée'),
            ('queued', 'Mise en file'),
            ('processing', 'En traitement'),
            ('sent', 'Envoyée'),
            ('delivered', 'Livrée'),
            ('read', 'Lue'),
            ('failed', 'Échec'),
            ('retry', 'Nouvelle tentative'),
        ],
        verbose_name="Action"
    )
    
    message = models.TextField(
        verbose_name="Message de log"
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name="Métadonnées",
        blank=True
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    
    class Meta:
        verbose_name = "Log notification"
        verbose_name_plural = "Logs notifications"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['notification', 'timestamp']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.notification.id} - {self.get_action_display()} - {self.timestamp}"