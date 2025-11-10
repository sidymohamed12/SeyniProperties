from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from apps.core.models import BaseModel
import secrets
import string

User = get_user_model()


class APIKey(BaseModel):
    """Modèle pour les clés API"""
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la clé API"
    )
    
    key = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Clé API",
        help_text="Générée automatiquement"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name="Utilisateur"
    )
    
    # Permissions
    permissions = models.JSONField(
        default=list,
        verbose_name="Permissions",
        help_text="Liste des permissions accordées à cette clé"
    )
    
    # Restrictions
    ip_whitelist = models.JSONField(
        default=list,
        verbose_name="Liste blanche IP",
        help_text="Liste des IPs autorisées (vide = toutes)",
        blank=True
    )
    
    rate_limit_per_minute = models.PositiveIntegerField(
        default=60,
        verbose_name="Limite par minute"
    )
    
    rate_limit_per_hour = models.PositiveIntegerField(
        default=1000,
        verbose_name="Limite par heure"
    )
    
    rate_limit_per_day = models.PositiveIntegerField(
        default=10000,
        verbose_name="Limite par jour"
    )
    
    # Dates
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'expiration"
    )
    
    derniere_utilisation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière utilisation"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Clé active"
    )
    
    # Statistiques
    nombre_utilisations = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre d'utilisations"
    )
    
    class Meta:
        verbose_name = "Clé API"
        verbose_name_plural = "Clés API"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_api_key()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nom} ({self.user.username})"
    
    @staticmethod
    def generate_api_key():
        """Génère une clé API unique"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(64))
    
    @property
    def is_expired(self):
        """Vérifie si la clé a expiré"""
        if not self.date_expiration:
            return False
        
        from django.utils import timezone
        return timezone.now() > self.date_expiration
    
    def can_access_ip(self, ip_address):
        """Vérifie si l'IP peut utiliser cette clé"""
        if not self.ip_whitelist:
            return True
        return ip_address in self.ip_whitelist
    
    def has_permission(self, permission):
        """Vérifie si la clé a une permission spécifique"""
        return permission in self.permissions or 'all' in self.permissions
    
    def record_usage(self):
        """Enregistre une utilisation de la clé"""
        from django.utils import timezone
        self.nombre_utilisations += 1
        self.derniere_utilisation = timezone.now()
        self.save(update_fields=['nombre_utilisations', 'derniere_utilisation'])


class APIRequest(BaseModel):
    """Modèle pour logger les requêtes API"""
    
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        verbose_name="Clé API"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_requests',
        verbose_name="Utilisateur"
    )
    
    # Détails de la requête
    method = models.CharField(
        max_length=10,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
            ('DELETE', 'DELETE'),
        ],
        verbose_name="Méthode HTTP"
    )
    
    endpoint = models.CharField(
        max_length=500,
        verbose_name="Endpoint"
    )
    
    query_params = models.JSONField(
        default=dict,
        verbose_name="Paramètres de requête",
        blank=True
    )
    
    request_body = models.TextField(
        verbose_name="Corps de la requête",
        blank=True
    )
    
    # Informations client
    ip_address = models.GenericIPAddressField(
        verbose_name="Adresse IP"
    )
    
    user_agent = models.TextField(
        verbose_name="User Agent",
        blank=True
    )
    
    # Réponse
    status_code = models.PositiveIntegerField(
        verbose_name="Code de statut HTTP"
    )
    
    response_size_bytes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Taille de la réponse (octets)"
    )
    
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Temps de réponse (ms)"
    )
    
    # Erreurs
    error_message = models.TextField(
        verbose_name="Message d'erreur",
        blank=True
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Horodatage"
    )
    
    class Meta:
        verbose_name = "Requête API"
        verbose_name_plural = "Requêtes API"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
    
    @property
    def is_successful(self):
        """Vérifie si la requête a réussi"""
        return 200 <= self.status_code < 300
    
    @property
    def is_client_error(self):
        """Vérifie si c'est une erreur client (4xx)"""
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self):
        """Vérifie si c'est une erreur serveur (5xx)"""
        return self.status_code >= 500


class APIRateLimit(BaseModel):
    """Modèle pour tracker les limites de taux d'API"""
    
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.CASCADE,
        related_name='rate_limits',
        verbose_name="Clé API"
    )
    
    periode = models.CharField(
        max_length=10,
        choices=[
            ('minute', 'Minute'),
            ('hour', 'Heure'),
            ('day', 'Jour'),
        ],
        verbose_name="Période"
    )
    
    date_periode = models.DateTimeField(
        verbose_name="Date de la période"
    )
    
    nombre_requetes = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de requêtes"
    )
    
    limite = models.PositiveIntegerField(
        verbose_name="Limite"
    )
    
    class Meta:
        verbose_name = "Limite de taux API"
        verbose_name_plural = "Limites de taux API"
        unique_together = [['api_key', 'periode', 'date_periode']]
        indexes = [
            models.Index(fields=['api_key', 'periode', 'date_periode']),
        ]
    
    def __str__(self):
        return f"{self.api_key.nom} - {self.periode} - {self.nombre_requetes}/{self.limite}"
    
    @property
    def is_exceeded(self):
        """Vérifie si la limite est dépassée"""
        return self.nombre_requetes >= self.limite
    
    def increment(self):
        """Incrémente le compteur de requêtes"""
        self.nombre_requetes += 1
        self.save(update_fields=['nombre_requetes'])


class WebhookEndpoint(BaseModel):
    """Modèle pour les endpoints de webhook"""
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du webhook"
    )
    
    url = models.URLField(
        verbose_name="URL du webhook"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='webhooks',
        verbose_name="Utilisateur"
    )
    
    # Événements à écouter
    events = models.JSONField(
        default=list,
        verbose_name="Événements",
        help_text="Liste des événements à envoyer via webhook"
    )
    
    # Sécurité
    secret = models.CharField(
        max_length=64,
        verbose_name="Secret",
        help_text="Secret pour signer les requêtes"
    )
    
    # Configuration
    timeout_seconds = models.PositiveIntegerField(
        default=30,
        verbose_name="Timeout (secondes)"
    )
    
    max_retries = models.PositiveIntegerField(
        default=3,
        verbose_name="Nombre maximum de tentatives"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Webhook actif"
    )
    
    derniere_reponse_ok = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière réponse OK"
    )
    
    class Meta:
        verbose_name = "Endpoint Webhook"
        verbose_name_plural = "Endpoints Webhooks"
        ordering = ['nom']
    
    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = APIKey.generate_api_key()[:32]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nom} ({self.url})"
    
    def is_listening_to(self, event):
        """Vérifie si le webhook écoute un événement spécifique"""
        return event in self.events or 'all' in self.events


class WebhookDelivery(BaseModel):
    """Modèle pour les livraisons de webhook"""
    
    webhook = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name="Webhook"
    )
    
    event_type = models.CharField(
        max_length=50,
        verbose_name="Type d'événement"
    )
    
    event_data = models.JSONField(
        verbose_name="Données de l'événement"
    )
    
    # Détails de la livraison
    status_code = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Code de statut"
    )
    
    response_body = models.TextField(
        verbose_name="Corps de la réponse",
        blank=True
    )
    
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Temps de réponse (ms)"
    )
    
    # Tentatives
    attempt_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de tentatives"
    )
    
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Prochaine tentative"
    )
    
    # Résultat
    is_successful = models.BooleanField(
        default=False,
        verbose_name="Livraison réussie"
    )
    
    error_message = models.TextField(
        verbose_name="Message d'erreur",
        blank=True
    )
    
    class Meta:
        verbose_name = "Livraison Webhook"
        verbose_name_plural = "Livraisons Webhooks"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook', 'created_at']),
            models.Index(fields=['event_type']),
            models.Index(fields=['is_successful']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_successful else "✗"
        return f"{status} {self.webhook.nom} - {self.event_type}"
    
    def mark_successful(self, status_code, response_body="", response_time_ms=None):
        """Marque la livraison comme réussie"""
        self.is_successful = True
        self.status_code = status_code
        self.response_body = response_body
        if response_time_ms:
            self.response_time_ms = response_time_ms
        self.save()
        
        # Mettre à jour le webhook parent
        from django.utils import timezone
        self.webhook.derniere_reponse_ok = timezone.now()
        self.webhook.save(update_fields=['derniere_reponse_ok'])
    
    def mark_failed(self, error_message, status_code=None, response_body=""):
        """Marque la livraison comme échouée"""
        self.is_successful = False
        self.error_message = error_message
        if status_code:
            self.status_code = status_code
        if response_body:
            self.response_body = response_body
        
        # Programmer la prochaine tentative si applicable
        if self.attempt_count < self.webhook.max_retries:
            from django.utils import timezone
            from datetime import timedelta
            
            # Backoff exponentiel: 2^attempt_count minutes
            delay_minutes = 2 ** self.attempt_count
            self.next_retry_at = timezone.now() + timedelta(minutes=delay_minutes)
        
        self.save()


class APIToken(BaseModel):
    """Modèle pour les tokens d'authentification JWT"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_tokens',
        verbose_name="Utilisateur"
    )
    
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Hash du token"
    )
    
    # Métadonnées
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du token",
        blank=True
    )
    
    # Informations de création
    ip_creation = models.GenericIPAddressField(
        verbose_name="IP de création",
        null=True,
        blank=True
    )
    
    user_agent_creation = models.TextField(
        verbose_name="User Agent de création",
        blank=True
    )
    
    # Dates
    date_expiration = models.DateTimeField(
        verbose_name="Date d'expiration"
    )
    
    derniere_utilisation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière utilisation"
    )
    
    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name="Token actif"
    )
    
    is_revoked = models.BooleanField(
        default=False,
        verbose_name="Token révoqué"
    )
    
    date_revocation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de révocation"
    )
    
    # Permissions
    scopes = models.JSONField(
        default=list,
        verbose_name="Portées (scopes)",
        help_text="Liste des permissions accordées à ce token"
    )
    
    class Meta:
        verbose_name = "Token API"
        verbose_name_plural = "Tokens API"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash']),
            models.Index(fields=['user']),
            models.Index(fields=['date_expiration']),
            models.Index(fields=['is_active', 'is_revoked']),
        ]
    
    def __str__(self):
        return f"Token {self.nom or 'sans nom'} - {self.user.username}"
    
    @property
    def is_expired(self):
        """Vérifie si le token a expiré"""
        from django.utils import timezone
        return timezone.now() > self.date_expiration
    
    @property
    def is_valid(self):
        """Vérifie si le token est valide"""
        return self.is_active and not self.is_revoked and not self.is_expired
    
    def revoke(self):
        """Révoque le token"""
        from django.utils import timezone
        self.is_revoked = True
        self.date_revocation = timezone.now()
        self.save(update_fields=['is_revoked', 'date_revocation'])
    
    def has_scope(self, scope):
        """Vérifie si le token a une portée spécifique"""
        return scope in self.scopes or 'all' in self.scopes
    
    def record_usage(self):
        """Enregistre une utilisation du token"""
        from django.utils import timezone
        self.derniere_utilisation = timezone.now()
        self.save(update_fields=['derniere_utilisation'])


class APIError(BaseModel):
    """Modèle pour logger les erreurs API"""
    
    # Informations de la requête
    endpoint = models.CharField(
        max_length=500,
        verbose_name="Endpoint"
    )
    
    method = models.CharField(
        max_length=10,
        verbose_name="Méthode HTTP"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur"
    )
    
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Clé API"
    )
    
    # Détails de l'erreur
    error_type = models.CharField(
        max_length=50,
        choices=[
            ('validation', 'Erreur de validation'),
            ('authentication', 'Erreur d\'authentification'),
            ('authorization', 'Erreur d\'autorisation'),
            ('not_found', 'Ressource non trouvée'),
            ('rate_limit', 'Limite de taux dépassée'),
            ('server_error', 'Erreur serveur'),
            ('timeout', 'Timeout'),
            ('other', 'Autre'),
        ],
        verbose_name="Type d'erreur"
    )
    
    status_code = models.PositiveIntegerField(
        verbose_name="Code de statut HTTP"
    )
    
    error_message = models.TextField(
        verbose_name="Message d'erreur"
    )
    
    stack_trace = models.TextField(
        verbose_name="Stack trace",
        blank=True
    )
    
    # Contexte
    request_data = models.JSONField(
        default=dict,
        verbose_name="Données de la requête",
        blank=True
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
    
    # Résolution
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Erreur résolue"
    )
    
    resolution_notes = models.TextField(
        verbose_name="Notes de résolution",
        blank=True
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_api_errors',
        verbose_name="Résolu par"
    )
    
    date_resolution = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de résolution"
    )
    
    class Meta:
        verbose_name = "Erreur API"
        verbose_name_plural = "Erreurs API"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['error_type']),
            models.Index(fields=['status_code']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.get_error_type_display()} - {self.endpoint} ({self.status_code})"
    
    def resolve(self, resolved_by, notes=""):
        """Marque l'erreur comme résolue"""
        from django.utils import timezone
        
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.date_resolution = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_by', 'resolution_notes', 'date_resolution'])


class APIStatistics(BaseModel):
    """Modèle pour les statistiques d'utilisation de l'API"""
    
    date_stats = models.DateField(
        unique=True,
        verbose_name="Date des statistiques"
    )
    
    # Requêtes
    total_requests = models.PositiveIntegerField(
        default=0,
        verbose_name="Total des requêtes"
    )
    
    successful_requests = models.PositiveIntegerField(
        default=0,
        verbose_name="Requêtes réussies"
    )
    
    failed_requests = models.PositiveIntegerField(
        default=0,
        verbose_name="Requêtes échouées"
    )
    
    # Codes de statut
    status_2xx = models.PositiveIntegerField(
        default=0,
        verbose_name="Codes 2xx"
    )
    
    status_4xx = models.PositiveIntegerField(
        default=0,
        verbose_name="Codes 4xx"
    )
    
    status_5xx = models.PositiveIntegerField(
        default=0,
        verbose_name="Codes 5xx"
    )
    
    # Performance
    avg_response_time_ms = models.FloatField(
        default=0.0,
        verbose_name="Temps de réponse moyen (ms)"
    )
    
    max_response_time_ms = models.PositiveIntegerField(
        default=0,
        verbose_name="Temps de réponse max (ms)"
    )
    
    # Endpoints les plus utilisés
    top_endpoints = models.JSONField(
        default=list,
        verbose_name="Top endpoints",
        help_text="Liste des endpoints les plus utilisés"
    )
    
    # Utilisateurs actifs
    active_users = models.PositiveIntegerField(
        default=0,
        verbose_name="Utilisateurs actifs"
    )
    
    active_api_keys = models.PositiveIntegerField(
        default=0,
        verbose_name="Clés API actives"
    )
    
    # Bande passante
    total_bandwidth_bytes = models.BigIntegerField(
        default=0,
        verbose_name="Bande passante totale (octets)"
    )
    
    class Meta:
        verbose_name = "Statistiques API"
        verbose_name_plural = "Statistiques API"
        ordering = ['-date_stats']
    
    def __str__(self):
        return f"Stats API du {self.date_stats}"
    
    @property
    def success_rate(self):
        """Calcule le taux de succès"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @classmethod
    def generate_daily_stats(cls, date=None):
        """Génère les statistiques pour une date donnée"""
        from django.utils import timezone
        from django.db.models import Count, Avg, Max, Sum
        
        if not date:
            date = timezone.now().date()
        
        # Requêtes de la journée
        requests = APIRequest.objects.filter(timestamp__date=date)
        
        total_requests = requests.count()
        successful_requests = requests.filter(status_code__lt=400).count()
        failed_requests = total_requests - successful_requests
        
        # Codes de statut
        status_2xx = requests.filter(status_code__gte=200, status_code__lt=300).count()
        status_4xx = requests.filter(status_code__gte=400, status_code__lt=500).count()
        status_5xx = requests.filter(status_code__gte=500).count()
        
        # Performance
        perf_stats = requests.aggregate(
            avg_time=Avg('response_time_ms'),
            max_time=Max('response_time_ms'),
            total_bandwidth=Sum('response_size_bytes')
        )
        
        # Top endpoints
        top_endpoints = list(
            requests.values('endpoint')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Utilisateurs actifs
        active_users = requests.values('user').distinct().count()
        active_api_keys = requests.values('api_key').distinct().count()
        
        # Créer ou mettre à jour les stats
        stats, created = cls.objects.update_or_create(
            date_stats=date,
            defaults={
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'status_2xx': status_2xx,
                'status_4xx': status_4xx,
                'status_5xx': status_5xx,
                'avg_response_time_ms': perf_stats['avg_time'] or 0.0,
                'max_response_time_ms': perf_stats['max_time'] or 0,
                'total_bandwidth_bytes': perf_stats['total_bandwidth'] or 0,
                'top_endpoints': top_endpoints,
                'active_users': active_users,
                'active_api_keys': active_api_keys,
            }
        )
        
        return stats


class APIDocumentation(BaseModel):
    """Modèle pour la documentation de l'API"""
    
    endpoint = models.CharField(
        max_length=500,
        verbose_name="Endpoint"
    )
    
    method = models.CharField(
        max_length=10,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
            ('DELETE', 'DELETE'),
        ],
        verbose_name="Méthode HTTP"
    )
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        verbose_name="Description"
    )
    
    # Paramètres
    parametres_url = models.JSONField(
        default=list,
        verbose_name="Paramètres URL",
        blank=True
    )
    
    parametres_query = models.JSONField(
        default=list,
        verbose_name="Paramètres de requête",
        blank=True
    )
    
    corps_requete = models.JSONField(
        default=dict,
        verbose_name="Corps de la requête",
        blank=True
    )
    
    # Réponses
    reponses = models.JSONField(
        default=dict,
        verbose_name="Réponses possibles"
    )
    
    # Exemples
    exemples_requete = models.JSONField(
        default=list,
        verbose_name="Exemples de requête",
        blank=True
    )
    
    exemples_reponse = models.JSONField(
        default=list,
        verbose_name="Exemples de réponse",
        blank=True
    )
    
    # Métadonnées
    categorie = models.CharField(
        max_length=50,
        verbose_name="Catégorie",
        blank=True
    )
    
    tags = models.JSONField(
        default=list,
        verbose_name="Tags",
        blank=True
    )
    
    permissions_requises = models.JSONField(
        default=list,
        verbose_name="Permissions requises",
        blank=True
    )
    
    # Statut
    is_deprecated = models.BooleanField(
        default=False,
        verbose_name="Obsolète"
    )
    
    version_deprecation = models.CharField(
        max_length=20,
        verbose_name="Version de dépréciation",
        blank=True
    )
    
    is_published = models.BooleanField(
        default=True,
        verbose_name="Publié"
    )
    
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    class Meta:
        verbose_name = "Documentation API"
        verbose_name_plural = "Documentation API"
        ordering = ['categorie', 'ordre', 'endpoint']
        unique_together = [['endpoint', 'method']]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.titre}"