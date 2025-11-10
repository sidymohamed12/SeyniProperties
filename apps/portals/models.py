from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel

User = get_user_model()


class PortalConfiguration(BaseModel):
    """Configuration générale des portails"""
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du widget"
    )
    
    portal_type = models.CharField(
        max_length=20,
        choices=[
            ('tenant', 'Portail locataire'),
            ('landlord', 'Portail bailleur'),
            ('employee', 'Portail employé'),
            ('manager', 'Portail manager'),
        ],
        verbose_name="Type de portail"
    )
    
    widget_type = models.CharField(
        max_length=30,
        choices=[
            ('quick_stats', 'Statistiques rapides'),
            ('recent_payments', 'Paiements récents'),
            ('pending_tasks', 'Tâches en attente'),
            ('upcoming_events', 'Événements à venir'),
            ('notifications', 'Notifications'),
            ('quick_actions', 'Actions rapides'),
            ('document_list', 'Liste de documents'),
            ('calendar', 'Calendrier'),
            ('chart', 'Graphique'),
            ('news_feed', 'Fil d\'actualités'),
        ],
        verbose_name="Type de widget"
    )
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        verbose_name="Configuration du widget"
    )
    
    # Permissions
    roles_autorises = models.JSONField(
        default=list,
        verbose_name="Rôles autorisés",
        help_text="Liste des rôles pouvant voir ce widget"
    )
    
    # Affichage
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    colonne = models.PositiveIntegerField(
        default=1,
        choices=[
            (1, 'Colonne 1'),
            (2, 'Colonne 2'),
            (3, 'Colonne 3'),
        ],
        verbose_name="Colonne"
    )
    
    hauteur = models.CharField(
        max_length=10,
        choices=[
            ('small', 'Petit'),
            ('medium', 'Moyen'),
            ('large', 'Grand'),
            ('auto', 'Automatique'),
        ],
        default='medium',
        verbose_name="Hauteur"
    )
    
    # État
    is_active = models.BooleanField(
        default=True,
        verbose_name="Widget actif"
    )
    
    is_collapsible = models.BooleanField(
        default=True,
        verbose_name="Peut être réduit"
    )
    
    is_removable = models.BooleanField(
        default=True,
        verbose_name="Peut être supprimé"
    )
    
    # Cache
    cache_duration_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Durée du cache (minutes)"
    )
    
    class Meta:
        verbose_name = "Widget portail"
        verbose_name_plural = "Widgets portails"
        ordering = ['portal_type', 'ordre']
        unique_together = [['portal_type', 'nom']]
    
    def __str__(self):
        return f"{self.nom} ({self.get_portal_type_display()})"
    
    def can_be_viewed_by(self, user):
        """Vérifie si l'utilisateur peut voir ce widget"""
        if not self.is_active:
            return False
        
        if not self.roles_autorises:
            return True
        
        user_roles = []
        if hasattr(user, 'user_type'):
            user_roles.append(user.user_type)
        
        if hasattr(user, 'groups'):
            user_roles.extend([group.name for group in user.groups.all()])
        
        return any(role in self.roles_autorises for role in user_roles)


class PortalNotification(BaseModel):
    """Notifications spécifiques aux portails (dans l'app)"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portal_notifications',
        verbose_name="Utilisateur"
    )
    
    portal_type = models.CharField(
        max_length=20,
        choices=[
            ('tenant', 'Portail locataire'),
            ('landlord', 'Portail bailleur'),
            ('employee', 'Portail employé'),
            ('manager', 'Portail manager'),
        ],
        verbose_name="Type de portail"
    )
    
    # Contenu
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    message = models.TextField(
        verbose_name="Message"
    )
    
    type_notification = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Information'),
            ('success', 'Succès'),
            ('warning', 'Avertissement'),
            ('error', 'Erreur'),
            ('update', 'Mise à jour'),
        ],
        default='info',
        verbose_name="Type"
    )
    
    # Action associée
    action_url = models.CharField(
        max_length=500,
        verbose_name="URL d'action",
        blank=True,
        help_text="URL vers laquelle rediriger lors du clic"
    )
    
    action_text = models.CharField(
        max_length=50,
        verbose_name="Texte du bouton d'action",
        blank=True
    )
    
    # État
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lu"
    )
    
    date_read = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )
    
    # Expiration
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'expiration"
    )
    
    # Affichage
    is_sticky = models.BooleanField(
        default=False,
        verbose_name="Épinglé",
        help_text="Reste affiché même après lecture"
    )
    
    show_popup = models.BooleanField(
        default=False,
        verbose_name="Affichage popup"
    )
    
    class Meta:
        verbose_name = "Notification portail"
        verbose_name_plural = "Notifications portails"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['portal_type']),
            models.Index(fields=['date_expiration']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.user.username}"
    
    @property
    def is_expired(self):
        """Vérifie si la notification a expiré"""
        if not self.date_expiration:
            return False
        
        from django.utils import timezone
        return timezone.now() > self.date_expiration
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        from django.utils import timezone
        
        if not self.is_read:
            self.is_read = True
            self.date_read = timezone.now()
            self.save(update_fields=['is_read', 'date_read'])


class PortalFeedback(BaseModel):
    """Modèle pour les retours utilisateurs sur les portails"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portal_feedbacks',
        verbose_name="Utilisateur"
    )
    
    portal_type = models.CharField(
        max_length=20,
        choices=[
            ('tenant', 'Portail locataire'),
            ('landlord', 'Portail bailleur'),
            ('employee', 'Portail employé'),
            ('manager', 'Portail manager'),
        ],
        verbose_name="Type de portail"
    )
    
    # Type de feedback
    feedback_type = models.CharField(
        max_length=20,
        choices=[
            ('bug', 'Bug/Problème'),
            ('suggestion', 'Suggestion'),
            ('feature_request', 'Demande de fonctionnalité'),
            ('compliment', 'Compliment'),
            ('complaint', 'Plainte'),
            ('question', 'Question'),
        ],
        verbose_name="Type de retour"
    )
    
    # Évaluation
    satisfaction_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        choices=[
            (1, 'Très insatisfait'),
            (2, 'Insatisfait'),
            (3, 'Neutre'),
            (4, 'Satisfait'),
            (5, 'Très satisfait'),
        ],
        verbose_name="Note de satisfaction"
    )
    
    # Contenu
    sujet = models.CharField(
        max_length=200,
        verbose_name="Sujet"
    )
    
    message = models.TextField(
        verbose_name="Message"
    )
    
    # Page concernée
    page_url = models.CharField(
        max_length=500,
        verbose_name="URL de la page",
        blank=True
    )
    
    # Informations techniques
    browser_info = models.JSONField(
        default=dict,
        verbose_name="Informations navigateur",
        blank=True
    )
    
    screenshot = models.ImageField(
        upload_to='portals/feedback/screenshots/',
        verbose_name="Capture d'écran",
        blank=True,
        null=True
    )
    
    # Traitement
    statut = models.CharField(
        max_length=20,
        choices=[
            ('nouveau', 'Nouveau'),
            ('en_cours', 'En cours de traitement'),
            ('resolu', 'Résolu'),
            ('ferme', 'Fermé'),
            ('reporte', 'Reporté'),
        ],
        default='nouveau',
        verbose_name="Statut"
    )
    
    assigne_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedbacks_assignes',
        verbose_name="Assigné à"
    )
    
    reponse = models.TextField(
        verbose_name="Réponse",
        blank=True
    )
    
    date_reponse = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de réponse"
    )
    
    class Meta:
        verbose_name = "Retour portail"
        verbose_name_plural = "Retours portails"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback_type']),
            models.Index(fields=['statut']),
            models.Index(fields=['portal_type']),
        ]
    
    def __str__(self):
        return f"{self.get_feedback_type_display()} - {self.sujet} ({self.user.username})"
    
    def assign_to(self, user):
        """Assigne le feedback à un utilisateur"""
        self.assigne_a = user
        if self.statut == 'nouveau':
            self.statut = 'en_cours'
        self.save(update_fields=['assigne_a', 'statut'])
    
    def resolve(self, response_message=""):
        """Marque le feedback comme résolu"""
        from django.utils import timezone
        
        self.statut = 'resolu'
        if response_message:
            self.reponse = response_message
        self.date_reponse = timezone.now()
        self.save(update_fields=['statut', 'reponse', 'date_reponse'])


class PortalAnnouncement(BaseModel):
    """Modèle pour les annonces dans les portails"""
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    contenu = models.TextField(
        verbose_name="Contenu"
    )
    
    # Ciblage
    portal_types = models.JSONField(
        default=list,
        verbose_name="Types de portails ciblés"
    )
    
    user_types = models.JSONField(
        default=list,
        verbose_name="Types d'utilisateurs ciblés"
    )
    
    users_specifiques = models.ManyToManyField(
        User,
        blank=True,
        verbose_name="Utilisateurs spécifiques"
    )
    
    # Type et priorité
    type_annonce = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Information'),
            ('maintenance', 'Maintenance'),
            ('nouveaute', 'Nouveauté'),
            ('urgent', 'Urgent'),
            ('evenement', 'Événement'),
        ],
        default='info',
        verbose_name="Type d'annonce"
    )
    
    priorite = models.CharField(
        max_length=10,
        choices=[
            ('basse', 'Basse'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
        ],
        default='normale',
        verbose_name="Priorité"
    )
    
    # Dates
    date_debut = models.DateTimeField(
        verbose_name="Date de début d'affichage"
    )
    
    date_fin = models.DateTimeField(
        verbose_name="Date de fin d'affichage"
    )
    
    # Affichage
    is_active = models.BooleanField(
        default=True,
        verbose_name="Annonce active"
    )
    
    affichage_popup = models.BooleanField(
        default=False,
        verbose_name="Affichage en popup"
    )
    
    affichage_banniere = models.BooleanField(
        default=True,
        verbose_name="Affichage en bannière"
    )
    
    # Création
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='annonces_creees',
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Annonce portail"
        verbose_name_plural = "Annonces portails"
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['is_active']),
            models.Index(fields=['type_annonce']),
        ]
    
    def __str__(self):
        return self.titre
    
    @property
    def is_current(self):
        """Vérifie si l'annonce est actuellement visible"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.date_debut <= now <= self.date_fin
        )
    
    def is_visible_for_user(self, user):
        """Vérifie si l'annonce est visible pour un utilisateur donné"""
        if not self.is_current:
            return False
        
        # Vérifier les utilisateurs spécifiques
        if self.users_specifiques.exists():
            return self.users_specifiques.filter(id=user.id).exists()
        
        # Vérifier le type d'utilisateur
        if self.user_types and hasattr(user, 'user_type'):
            if user.user_type not in self.user_types:
                return False
        
        return True


class UserPortalPreference(BaseModel):
    """Préférences utilisateur pour les portails"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='portal_preferences',
        verbose_name="Utilisateur"
    )
    
    # Préférences d'affichage
    theme = models.CharField(
        max_length=10,
        choices=[
            ('light', 'Clair'),
            ('dark', 'Sombre'),
            ('auto', 'Automatique'),
        ],
        default='light',
        verbose_name="Thème"
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
    
    # Layout et widgets
    dashboard_layout = models.JSONField(
        default=dict,
        verbose_name="Configuration du dashboard"
    )
    
    widgets_favoris = models.JSONField(
        default=list,
        verbose_name="Widgets favoris"
    )
    
    # Préférences de notification
    notifications_desktop = models.BooleanField(
        default=True,
        verbose_name="Notifications desktop"
    )
    
    notifications_son = models.BooleanField(
        default=False,
        verbose_name="Son des notifications"
    )
    
    # Préférences de navigation
    menu_collapsed = models.BooleanField(
        default=False,
        verbose_name="Menu réduit par défaut"
    )
    
    page_accueil_personnalisee = models.CharField(
        max_length=50,
        verbose_name="Page d'accueil personnalisée",
        blank=True,
        help_text="URL de la page d'accueil préférée"
    )
    
    # Autres préférences
    elements_par_page = models.PositiveIntegerField(
        default=25,
        choices=[
            (10, '10'),
            (25, '25'),
            (50, '50'),
            (100, '100'),
        ],
        verbose_name="Éléments par page"
    )
    
    timezone = models.CharField(
        max_length=50,
        default='Africa/Dakar',
        verbose_name="Fuseau horaire"
    )
    
    class Meta:
        verbose_name = "Préférence portail utilisateur"
        verbose_name_plural = "Préférences portail utilisateurs"
    
    def __str__(self):
        return f"Préférences de {self.user.username}"


class PortalAccess(BaseModel):
    """Modèle pour tracker les accès aux portails"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portal_accesses',
        verbose_name="Utilisateur"
    )
    
    portal_type = models.CharField(
        max_length=20,
        choices=[
            ('tenant', 'Portail locataire'),
            ('landlord', 'Portail bailleur'),
            ('employee', 'Portail employé'),
            ('manager', 'Portail manager'),
        ],
        verbose_name="Type de portail"
    )
    
    # Informations de connexion
    date_connexion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de connexion"
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name="Adresse IP",
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        verbose_name="User Agent",
        blank=True
    )
    
    # Informations de session
    session_key = models.CharField(
        max_length=40,
        verbose_name="Clé de session",
        blank=True
    )
    
    date_deconnexion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de déconnexion"
    )
    
    duree_session_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Durée de session (minutes)"
    )
    
    # Activité
    pages_visitees = models.PositiveIntegerField(
        default=0,
        verbose_name="Pages visitées"
    )
    
    actions_effectuees = models.PositiveIntegerField(
        default=0,
        verbose_name="Actions effectuées"
    )
    
    # Géolocalisation (optionnel)
    pays = models.CharField(
        max_length=50,
        verbose_name="Pays",
        blank=True
    )
    
    ville = models.CharField(
        max_length=100,
        verbose_name="Ville",
        blank=True
    )
    
    class Meta:
        verbose_name = "Accès portail"
        verbose_name_plural = "Accès portails"
        ordering = ['-date_connexion']
        indexes = [
            models.Index(fields=['user', 'date_connexion']),
            models.Index(fields=['portal_type']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_portal_type_display()} - {self.date_connexion}"
    
    def end_session(self):
        """Termine la session"""
        from django.utils import timezone
        
        if not self.date_deconnexion:
            self.date_deconnexion = timezone.now()
            
            # Calculer la durée de session
            delta = self.date_deconnexion - self.date_connexion
            self.duree_session_minutes = int(delta.total_seconds() / 60)
            
            self.save(update_fields=['date_deconnexion', 'duree_session_minutes'])


class PortalActivity(BaseModel):
    """Modèle pour tracker l'activité détaillée dans les portails"""
    
    access_session = models.ForeignKey(
        PortalAccess,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Session d'accès"
    )
    
    action_type = models.CharField(
        max_length=30,
        choices=[
            ('page_view', 'Vue de page'),
            ('form_submit', 'Soumission formulaire'),
            ('download', 'Téléchargement'),
            ('upload', 'Upload'),
            ('search', 'Recherche'),
            ('filter', 'Filtrage'),
            ('export', 'Export'),
            ('print', 'Impression'),
            ('api_call', 'Appel API'),
        ],
        verbose_name="Type d'action"
    )
    
    page_url = models.CharField(
        max_length=500,
        verbose_name="URL de la page"
    )
    
    page_title = models.CharField(
        max_length=200,
        verbose_name="Titre de la page",
        blank=True
    )
    
    # Détails de l'action
    action_details = models.JSONField(
        default=dict,
        verbose_name="Détails de l'action",
        blank=True
    )
    
    # Timing
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Temps de réponse (ms)"
    )
    
    # Résultat
    success = models.BooleanField(
        default=True,
        verbose_name="Succès"
    )
    
    error_message = models.TextField(
        verbose_name="Message d'erreur",
        blank=True
    )
    
    class Meta:
        verbose_name = "Activité portail"
        verbose_name_plural = "Activités portails"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['access_session', 'timestamp']),
            models.Index(fields=['action_type']),
            models.Index(fields=['page_url']),
        ]
    
    def __str__(self):
        return f"{self.access_session.user.username} - {self.get_action_type_display()} - {self.page_url}"


class PortalWidget(BaseModel):
    """Modèle pour les widgets spécifiques aux portails"""
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du widget"
    )
    
    portal_type = models.CharField(
        max_length=20,
        choices=[
            ('tenant', 'Portail locataire'),
            ('landlord', 'Portail bailleur'),
            ('employee', 'Portail employé'),
            ('manager', 'Portail manager'),
        ],
        verbose_name="Type de portail"
    )
    
    widget_type = models.CharField(
        max_length=30,
        choices=[
            ('quick_stats', 'Statistiques rapides'),
            ('recent_payments', 'Paiements récents'),
            ('pending_tasks', 'Tâches en attente'),
            ('upcoming_events', 'Événements à venir'),
            ('notifications', 'Notifications'),
            ('quick_actions', 'Actions rapides'),
            ('document_list', 'Liste de documents'),
            ('calendar', 'Calendrier'),
            ('chart', 'Graphique'),
            ('news_feed', 'Fil d\'actualités'),
        ],
        verbose_name="Type de widget"
    )
    
    # Configuration
    configuration = models.JSONField(
        default=dict,
        verbose_name="Configuration du widget"
    )
    
    # Permissions
    roles_autorises = models.JSONField(
        default=list,
        verbose_name="Rôles autorisés",
        help_text="Liste des rôles pouvant voir ce widget"
    )
    
    # Affichage
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    colonne = models.PositiveIntegerField(
        default=1,
        choices=[
            (1, 'Colonne 1'),
            (2, 'Colonne 2'),
            (3, 'Colonne 3'),
        ],
        verbose_name="Colonne"
    )
    
    hauteur = models.CharField(
        max_length=10,
        choices=[
            ('small', 'Petit'),
            ('medium', 'Moyen'),
            ('large', 'Grand'),
            ('auto', 'Automatique'),
        ],
        default='medium',
        verbose_name="Hauteur"
    )
    
    # État
    is_active = models.BooleanField(
        default=True,
        verbose_name="Widget actif"
    )
    
    is_collapsible = models.BooleanField(
        default=True,
        verbose_name="Peut être réduit"
    )
    
    is_removable = models.BooleanField(
        default=True,
        verbose_name="Peut être supprimé"
    )
    
    # Cache
    cache_duration_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Durée du cache (minutes)"
    )
    
    class Meta:
        verbose_name = "Widget portail"
        verbose_name_plural = "Widgets portails"
        ordering = ['portal_type', 'ordre']
        unique_together = [['portal_type', 'nom']]
    
    def __str__(self):
        return f"{self.nom} ({self.get_portal_type_display()})"
    
    def can_be_viewed_by(self, user):
        """Vérifie si l'utilisateur peut voir ce widget"""
        if not self.is_active:
            return False
        
        if not self.roles_autorises:
            return True
        
        user_roles = []
        if hasattr(user, 'user_type'):
            user_roles.append(user.user_type)
        
        if hasattr(user, 'groups'):
            user_roles.extend([group.name for group in user.groups.all()])
        
        return any(role in self.roles_autorises for role in user_roles)