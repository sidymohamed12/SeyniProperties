from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.core.models import BaseModel

User = get_user_model()


# ============================================================================
# ANCIENS MODÈLES (DÉPRÉCIÉS - À migrer vers Travail)
# ============================================================================


class Tache(BaseModel):  # ✅ Modèle français pour maintenance
    """
    Tâches planifiées de maintenance (ménage, visites, maintenance préventive, etc.)
    """
    
    TYPE_TACHE_CHOICES = [
        ('menage', 'Ménage'),
        ('visite', 'Visite de contrôle'),
        ('maintenance_preventive', 'Maintenance préventive'),
        ('etat_lieux', 'État des lieux'),
        ('reparation', 'Réparation'),
        ('livraison', 'Livraison'),
        ('rendez_vous', 'Rendez-vous'),
        ('administrative', 'Tâche administrative'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('complete', 'Terminé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    RECURRENCE_CHOICES = [
        ('aucune', 'Aucune'),
        ('quotidien', 'Quotidienne'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('annuelle', 'Annuelle'),
    ]
    
    # Identification
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de la tâche"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Relations vers la nouvelle structure
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taches_maintenance',  # ✅ DISTINCT des tâches d'employés
        verbose_name="Appartement concerné",
        help_text="Peut être null pour une tâche générale"
    )
    
    # Maintenir aussi l'ancien champ pour compatibilité
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taches_maintenance_legacy',  # ✅ DISTINCT
        verbose_name="Bien concerné (Legacy)",
        help_text="Champ de compatibilité - sera supprimé après migration"
    )
    
    # ✅ CORRIGÉ: related_name distincts pour éviter les conflits
    assigne_a = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches_maintenance_assignees',  # ✅ DISTINCT
        verbose_name="Assigné à",
        limit_choices_to={'user_type': 'employe'}  # 🆕 SIMPLIFIÉ (modèle déprécié)
    )
    
    cree_par = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='taches_maintenance_creees',  # ✅ DISTINCT
        verbose_name="Créé par"
    )
    
    # Caractéristiques
    type_tache = models.CharField(
        max_length=25,
        choices=TYPE_TACHE_CHOICES,
        verbose_name="Type de tâche"
    )
    
    priorite = models.CharField(
        max_length=10,
        choices=PRIORITE_CHOICES,
        default='normale',
        verbose_name="Priorité"
    )
    
    # Planification
    date_prevue = models.DateTimeField(
        verbose_name="Date prévue"
    )
    
    duree_estimee = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Durée estimée",
        help_text="Format: HH:MM:SS"
    )
    
    # Exécution
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
    
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='planifie',
        verbose_name="Statut"
    )
    
    # Récurrence
    is_recurrente = models.BooleanField(
        default=False,
        verbose_name="Tâche récurrente"
    )
    
    recurrence_type = models.CharField(
        max_length=15,
        choices=RECURRENCE_CHOICES,
        default='aucune',
        verbose_name="Type de récurrence"
    )
    
    recurrence_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fin de récurrence"
    )
    
    # Suivi
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    temps_reel = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Temps réel passé"
    )
    
    class Meta:
        verbose_name = "Tâche de maintenance"
        verbose_name_plural = "Tâches de maintenance"
        ordering = ['date_prevue', '-priorite']
        indexes = [
            models.Index(fields=['appartement', 'statut']),
            models.Index(fields=['assigne_a', 'statut']),
            models.Index(fields=['type_tache', 'date_prevue']),
            models.Index(fields=['date_prevue']),
            models.Index(fields=['is_recurrente']),
        ]
    
    def __str__(self):
        lieu = f" - {self.appartement}" if self.appartement else (f" - {self.bien}" if self.bien else "")
        return f"{self.titre}{lieu}"
    
    @property
    def bien_concerne(self):
        """Retourne le bien concerné (nouveau ou ancien)"""
        return self.appartement or self.bien
    
    @property
    def bailleur(self):
        """Accès au bailleur via appartement ou bien"""
        if self.appartement:
            return self.appartement.residence.bailleur
        elif self.bien:
            return self.bien.landlord
        return None
    
    @property
    def est_en_retard(self):
        """Vérifie si la tâche est en retard"""
        if self.statut in ['complete', 'annule']:
            return False
        
        return timezone.now() > self.date_prevue
    
    @property
    def duree_reelle(self):
        """Durée réelle de la tâche"""
        if self.date_debut and self.date_fin:
            return self.date_fin - self.date_debut
        return self.temps_reel
    
    def marquer_complete(self, commentaire=""):
        """Marque la tâche comme terminée"""
        self.statut = 'complete'
        if not self.date_fin:
            self.date_fin = timezone.now()
        
        if commentaire:
            self.commentaire = commentaire
        
        # Calculer le temps réel si début défini
        if self.date_debut:
            self.temps_reel = self.date_fin - self.date_debut
        
        self.save()
        
        # Créer la prochaine occurrence si récurrente
        if self.is_recurrente and self.recurrence_type != 'aucune':
            self.creer_prochaine_occurrence()
    
    def creer_prochaine_occurrence(self):
        """Crée la prochaine occurrence pour une tâche récurrente"""
        from datetime import timedelta
        
        if not self.is_recurrente or self.recurrence_type == 'aucune':
            return
        
        # Calculer la prochaine date
        if self.recurrence_type == 'quotidien':
            prochaine_date = self.date_prevue + timedelta(days=1)
        elif self.recurrence_type == 'hebdomadaire':
            prochaine_date = self.date_prevue + timedelta(weeks=1)
        elif self.recurrence_type == 'mensuelle':
            prochaine_date = self.date_prevue + timedelta(days=30)
        elif self.recurrence_type == 'trimestrielle':
            prochaine_date = self.date_prevue + timedelta(days=90)
        elif self.recurrence_type == 'annuelle':
            prochaine_date = self.date_prevue + timedelta(days=365)
        else:
            return
        
        # Vérifier si on n'a pas dépassé la date de fin
        if self.recurrence_fin and prochaine_date.date() > self.recurrence_fin:
            return
        
        # Créer la nouvelle tâche
        Tache.objects.create(
            titre=self.titre,
            description=self.description,
            appartement=self.appartement,
            bien=self.bien,
            assigne_a=self.assigne_a,
            cree_par=self.cree_par,
            type_tache=self.type_tache,
            priorite=self.priorite,
            date_prevue=prochaine_date,
            duree_estimee=self.duree_estimee,
            is_recurrente=self.is_recurrente,
            recurrence_type=self.recurrence_type,
            recurrence_fin=self.recurrence_fin,
        )

