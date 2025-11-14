from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference

User = get_user_model()


# ============================================================================
# ANCIENS MODÈLES (DÉPRÉCIÉS - À migrer vers Travail)
# ============================================================================


class Intervention(BaseModel):
    """Modèle pour les interventions de maintenance"""
    
    # Numéro unique généré automatiquement
    numero_intervention = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro d'intervention",
        help_text="Généré automatiquement"
    )
    
    # Informations de base
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        verbose_name="Description",
        blank=True
    )
    
    type_intervention = models.CharField(
        max_length=30,
        choices=[
            ('plomberie', 'Plomberie'),
            ('electricite', 'Électricité'),
            ('menage', 'Ménage'),
            ('reparation', 'Réparation'),
            ('peinture', 'Peinture'),
            ('serrurerie', 'Serrurerie'),
            ('climatisation', 'Climatisation'),
            ('jardinage', 'Jardinage'),
            ('securite', 'Sécurité'),
            ('autres', 'Autres'),
        ],
        verbose_name="Type d'intervention"
    )
    
    priorite = models.CharField(
        max_length=15,
        choices=[
            ('basse', 'Basse'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
            ('urgente', 'Urgente'),
        ],
        default='normale',
        verbose_name="Priorité"
    )
    
    # Relations vers la nouvelle structure
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        related_name='interventions',
        verbose_name="Appartement concerné"
    )
    
    # Maintenir aussi l'ancien champ pour compatibilité temporaire
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='interventions_legacy',
        verbose_name="Bien concerné (Legacy)",
        null=True,
        blank=True,
        help_text="Champ de compatibilité - sera supprimé après migration"
    )
    
    locataire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interventions_signalees',
        verbose_name="Locataire signataire",
        limit_choices_to={'type_tiers': 'locataire'}
    )
    
    technicien = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interventions_techniques',
        verbose_name="Technicien assigné",
        # 🆕 SIMPLIFIÉ: Un seul type d'employé (modèle déprécié)
        limit_choices_to={'user_type': 'employe'}
    )
    
    # Dates et statut
    date_signalement = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de signalement"
    )
    
    date_assignation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'assignation"
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
    
    statut = models.CharField(
        max_length=20,
        choices=[
            ('signale', 'Signalé'),
            ('assigne', 'Assigné'),
            ('en_cours', 'En cours'),
            ('complete', 'Terminé'),
            ('annule', 'Annulé'),
        ],
        default='signale',
        verbose_name="Statut"
    )
    
    # Coûts
    cout_estime = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Coût estimé"
    )
    
    cout_reel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Coût réel"
    )
    
    # Commentaires
    commentaire_technicien = models.TextField(
        blank=True,
        verbose_name="Commentaire technicien"
    )
    
    satisfaction_locataire = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        verbose_name="Satisfaction locataire (1-5)"
    )
    
    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes"
    )
    
    class Meta:
        verbose_name = "Intervention"
        verbose_name_plural = "Interventions"
        ordering = ['-date_signalement']
        indexes = [
            models.Index(fields=['numero_intervention']),
            models.Index(fields=['statut']),
            models.Index(fields=['type_intervention']),
            models.Index(fields=['priorite']),
            models.Index(fields=['date_signalement']),
            models.Index(fields=['appartement']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.numero_intervention:
            self.numero_intervention = generate_unique_reference('INT')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_intervention} - {self.titre}"
    
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
    def duree_intervention(self):
        """Calcule la durée de l'intervention"""
        if self.date_debut and self.date_fin:
            return self.date_fin - self.date_debut
        return None
    
    @property
    def est_en_retard(self):
        """Vérifie si l'intervention est en retard"""
        if self.statut in ['complete', 'annule']:
            return False
        
        # Considérer en retard après 48h pour urgente, 7 jours pour normale
        limite = timezone.now() - timezone.timedelta(
            hours=48 if self.priorite == 'urgente' else 168
        )
        
        return self.date_signalement < limite


class InterventionMedia(BaseModel):
    """Médias liés aux interventions"""
    
    intervention = models.ForeignKey(
        Intervention,
        on_delete=models.CASCADE,
        related_name='medias',
        verbose_name="Intervention"
    )
    
    type_media = models.CharField(
        max_length=20,
        choices=[
            ('photo_avant', 'Photo avant'),
            ('photo_apres', 'Photo après'),
            ('facture', 'Facture'),
            ('devis', 'Devis'),
            ('rapport', 'Rapport'),
        ],
        verbose_name="Type de média"
    )
    
    fichier = models.FileField(
        upload_to='interventions/medias/%Y/%m/',
        verbose_name="Fichier"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    ajoute_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Ajouté par"
    )
    
    class Meta:
        verbose_name = "Média d'intervention"
        verbose_name_plural = "Médias d'interventions"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.intervention.numero_intervention} - {self.get_type_media_display()}"


class InterventionChecklistItem(BaseModel):
    """Modèle pour les éléments de checklist d'intervention"""
    
    intervention = models.ForeignKey(
        Intervention,
        on_delete=models.CASCADE,
        related_name='checklist_items',
        verbose_name="Intervention"
    )
    
    description = models.CharField(
        max_length=200,
        verbose_name="Description de la tâche"
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Terminé"
    )
    
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre"
    )
    
    notes = models.TextField(
        verbose_name="Notes",
        blank=True
    )
    
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Terminé par"
    )
    
    date_completion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de completion"
    )
    
    class Meta:
        verbose_name = "Élément de checklist"
        verbose_name_plural = "Éléments de checklist"
        ordering = ['ordre', 'created_at']
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.description}"
    
    def mark_completed(self, completed_by=None):
        """Marque l'élément comme terminé"""
        self.is_completed = True
        self.completed_by = completed_by
        self.date_completion = timezone.now()
        self.save()


class InterventionTemplate(BaseModel):
    """Modèle pour les templates d'intervention avec checklist prédéfinie"""
    
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du template"
    )
    
    type_intervention = models.CharField(
        max_length=30,
        choices=[
            ('plomberie', 'Plomberie'),
            ('electricite', 'Électricité'),
            ('menage', 'Ménage'),
            ('reparation', 'Réparation générale'),
            ('peinture', 'Peinture'),
            ('serrurerie', 'Serrurerie'),
            ('climatisation', 'Climatisation'),
            ('jardinage', 'Jardinage'),
            ('maintenance_preventive', 'Maintenance préventive'),
            ('autres', 'Autres'),
        ],
        verbose_name="Type d'intervention"
    )
    
    description = models.TextField(
        verbose_name="Description",
        blank=True
    )
    
    duree_estimee = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Durée estimée (minutes)"
    )
    
    cout_estime = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Coût estimé"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Template actif"
    )
    
    class Meta:
        verbose_name = "Template d'intervention"
        verbose_name_plural = "Templates d'intervention"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def apply_to_intervention(self, intervention):
        """Applique ce template à une intervention"""
        # Copier les informations du template
        if self.duree_estimee and not intervention.cout_estime:
            intervention.cout_estime = self.cout_estime
        
        intervention.save()
        
        # Créer les éléments de checklist
        for item_template in self.checklist_template_items.all():
            InterventionChecklistItem.objects.create(
                intervention=intervention,
                description=item_template.description,
                ordre=item_template.ordre,
            )


class InterventionTemplateChecklistItem(BaseModel):
    """Modèle pour les éléments de checklist des templates"""
    
    template = models.ForeignKey(
        InterventionTemplate,
        on_delete=models.CASCADE,
        related_name='checklist_template_items',
        verbose_name="Template"
    )
    
    description = models.CharField(
        max_length=200,
        verbose_name="Description de la tâche"
    )
    
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre"
    )
    
    is_obligatoire = models.BooleanField(
        default=False,
        verbose_name="Obligatoire"
    )
    
    class Meta:
        verbose_name = "Élément de template checklist"
        verbose_name_plural = "Éléments de template checklist"
        ordering = ['ordre']
    
    def __str__(self):
        obligatoire = "*" if self.is_obligatoire else ""
        return f"{self.ordre}. {self.description}{obligatoire}"