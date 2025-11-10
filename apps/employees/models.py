# apps/employees/models.py - Version corrigée avec les constantes de choix
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.core.models import BaseModel

User = get_user_model()


class Employee(BaseModel):
    """Modèle pour les employés (techniciens, agents de terrain, etc.)"""
    
    # Constantes pour les choix
    SPECIALITES = [
        ('technique', 'Technique'),
        ('menage', 'Ménage'),
        ('jardinage', 'Jardinage'),
        ('peinture', 'Peinture'),
        ('plomberie', 'Plomberie'),
        ('electricite', 'Électricité'),
        ('serrurerie', 'Serrurerie'),
        ('climatisation', 'Climatisation'),
        ('polyvalent', 'Polyvalent'),
    ]
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('conge', 'En congé'),
        ('maladie', 'Arrêt maladie'),
        ('suspendu', 'Suspendu'),
    ]
    
    NIVEAU_COMPETENCE_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
        ('expert', 'Expert'),
    ]
    
    # Relation OneToOne avec User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    
    # Informations professionnelles
    specialite = models.CharField(
        max_length=50,
        choices=SPECIALITES,
        verbose_name="Spécialité"
    )
    
    date_embauche = models.DateField(
        verbose_name="Date d'embauche",
        null=True,  # ✅ AJOUTÉ: Permet les valeurs NULL temporairement
        blank=True  # ✅ AJOUTÉ: Permet les champs vides dans les formulaires
    )
    
    salaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Salaire mensuel",
        null=True,
        blank=True
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='actif',
        verbose_name="Statut"
    )
    
    # Informations de contact professionnelles
    telephone_professionnel = models.CharField(
        max_length=20,
        verbose_name="Téléphone professionnel",
        blank=True
    )
    
    # Compétences et évaluations
    niveau_competence = models.CharField(
        max_length=15,
        choices=NIVEAU_COMPETENCE_CHOICES,
        default='intermediaire',
        verbose_name="Niveau de compétence"
    )
    
    note_moyenne = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Note moyenne (sur 5)",
        help_text="Note basée sur les évaluations des interventions"
    )
    
    # Disponibilité
    is_available = models.BooleanField(
        default=True,
        verbose_name="Disponible"
    )
    
    # Métadonnées
    notes = models.TextField(
        verbose_name="Notes internes",
        blank=True
    )

    # Identifiants de connexion
    mot_de_passe_temporaire = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mot de passe temporaire",
        help_text="Mot de passe temporaire généré lors de la création du compte (sera effacé après première connexion)"
    )

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['-date_embauche']
        indexes = [
            models.Index(fields=['specialite']),
            models.Index(fields=['statut']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialite}"


class Task(BaseModel):
    """Modèle pour les tâches assignées aux employés"""
    
    # ===== CONSTANTES DE CHOIX =====
    TYPE_TACHE_CHOICES = [
        ('menage', 'Ménage'),
        ('visite', 'Visite d\'inspection'),
        ('maintenance_preventive', 'Maintenance préventive'),
        ('etat_lieux', 'État des lieux'),
        ('livraison', 'Livraison'),
        ('administrative', 'Tâche administrative'),
        ('autres', 'Autres'),
    ]
    
    STATUT_CHOICES = [
        ('planifie', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('complete', 'Complétée'),
        ('annule', 'Annulée'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    RECURRENCE_TYPE_CHOICES = [
        ('quotidien', 'Quotidien'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuel', 'Mensuel'),
    ]
    
    # ===== CHAMPS DU MODÈLE =====
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        verbose_name="Description",
        blank=True
    )
    
    type_tache = models.CharField(
        max_length=30,
        choices=TYPE_TACHE_CHOICES,
        verbose_name="Type de tâche"
    )
    
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taches',
        verbose_name="Bien concerné",
        help_text="Peut être null pour les tâches générales"
    )
    
    assigne_a = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='taches_assignees',
        verbose_name="Assigné à",
        limit_choices_to={'user_type__in': ['agent_terrain', 'technicien']}
    )
    
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='taches_creees',
        verbose_name="Créé par"
    )
    
    # Planification
    date_prevue = models.DateTimeField(
        verbose_name="Date prévue"
    )
    
    date_debut = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début"
    )
    
    date_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )
    
    duree_estimee = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Durée estimée (minutes)"
    )
    
    # Statut et priorité
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='planifie',
        verbose_name="Statut"
    )
    
    priorite = models.CharField(
        max_length=15,
        choices=PRIORITE_CHOICES,
        default='normale',
        verbose_name="Priorité"
    )
    
    # Récurrence
    is_recurrente = models.BooleanField(
        default=False,
        verbose_name="Tâche récurrente"
    )
    
    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_TYPE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Type de récurrence"
    )
    
    recurrence_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fin de récurrence"
    )
    
    # Résultats
    commentaire = models.TextField(
        verbose_name="Commentaire de l'employé",
        blank=True
    )
    
    temps_passe = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Temps passé (minutes)"
    )
    
    class Meta:
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        ordering = ['-date_prevue']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_prevue']),
            models.Index(fields=['priorite']),
            models.Index(fields=['type_tache']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.assigne_a.get_full_name()}"
    
    @property
    def is_overdue(self):
        """Vérifie si la tâche est en retard"""
        from django.utils import timezone
        return (
            self.statut in ['planifie', 'en_cours'] and 
            self.date_prevue < timezone.now()
        )
    
    @property
    def duree_reelle(self):
        """Calcule la durée réelle de la tâche"""
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            return int(delta.total_seconds() / 60)  # en minutes
        return self.temps_passe
    
    def start_task(self):
        """Démarre la tâche"""
        from django.utils import timezone
        
        self.statut = 'en_cours'
        self.date_debut = timezone.now()
        self.save()
    
    def complete_task(self, commentaire="", temps_passe=None):
        """Marque la tâche comme terminée"""
        from django.utils import timezone
        
        self.statut = 'complete'
        self.date_fin = timezone.now()
        if commentaire:
            self.commentaire = commentaire
        if temps_passe:
            self.temps_passe = temps_passe
        self.save()
        
        # Générer la prochaine occurrence si récurrente
        if self.is_recurrente:
            self.generate_next_occurrence()
    
    def generate_next_occurrence(self):
        """Génère la prochaine occurrence pour les tâches récurrentes"""
        from datetime import timedelta
        from django.utils import timezone
        
        if not self.is_recurrente or not self.recurrence_type:
            return
        
        # Calculer la prochaine date
        if self.recurrence_type == 'quotidien':
            next_date = self.date_prevue + timedelta(days=1)
        elif self.recurrence_type == 'hebdomadaire':
            next_date = self.date_prevue + timedelta(weeks=1)
        elif self.recurrence_type == 'mensuel':
            next_date = self.date_prevue + timedelta(days=30)
        else:
            return
        
        # Vérifier si on n'a pas dépassé la date de fin
        if self.recurrence_fin and next_date.date() > self.recurrence_fin:
            return
        
        # Créer la nouvelle tâche
        Task.objects.create(
            titre=self.titre,
            description=self.description,
            type_tache=self.type_tache,
            bien=self.bien,
            assigne_a=self.assigne_a,
            cree_par=self.cree_par,
            date_prevue=next_date,
            duree_estimee=self.duree_estimee,
            priorite=self.priorite,
            is_recurrente=self.is_recurrente,
            recurrence_type=self.recurrence_type,
            recurrence_fin=self.recurrence_fin,
        )


class TaskMedia(BaseModel):
    """Modèle pour les médias associés aux tâches"""
    
    TYPE_MEDIA_CHOICES = [
        ('photo_avant', 'Photo avant'),
        ('photo_apres', 'Photo après'),
        ('rapport', 'Rapport'),
        ('facture', 'Facture'),
        ('autre', 'Autre'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='medias',
        verbose_name="Tâche"
    )
    
    type_media = models.CharField(
        max_length=20,
        choices=TYPE_MEDIA_CHOICES,
        verbose_name="Type de média"
    )
    
    fichier = models.FileField(
        upload_to='tasks/media/',
        verbose_name="Fichier"
    )
    
    description = models.CharField(
        max_length=200,
        verbose_name="Description",
        blank=True
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Téléchargé par"
    )
    
    class Meta:
        verbose_name = "Média de tâche"
        verbose_name_plural = "Médias de tâche"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.titre} - {self.type_media}"