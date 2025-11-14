from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.core.models import BaseModel
from apps.maintenance.models.intervention import Intervention

User = get_user_model()



# ✅ Maintenir les autres modèles existants avec corrections mineures
class MaintenanceSchedule(BaseModel):
    """Modèle pour la maintenance préventive programmée"""
    
    # Relations duales pour compatibilité
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        related_name='maintenances_programmees',
        verbose_name="Appartement",
        null=True,
        blank=True
    )
    
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='maintenances_programmees_legacy',
        verbose_name="Bien immobilier (Legacy)",
        null=True,
        blank=True
    )
    
    type_maintenance = models.CharField(
        max_length=30,
        choices=[
            ('revision_annuelle', 'Révision annuelle'),
            ('nettoyage_mensuel', 'Nettoyage mensuel'),
            ('inspection_trimestre', 'Inspection trimestrielle'),
            ('verification_equipement', 'Vérification équipements'),
            ('entretien_jardin', 'Entretien jardin'),
            ('autres', 'Autres'),
        ],
        verbose_name="Type de maintenance"
    )
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        verbose_name="Description",
        blank=True
    )
    
    frequence = models.CharField(
        max_length=20,
        choices=[
            ('hebdomadaire', 'Hebdomadaire'),
            ('mensuel', 'Mensuel'),
            ('trimestriel', 'Trimestriel'),
            ('semestriel', 'Semestriel'),
            ('annuel', 'Annuel'),
        ],
        verbose_name="Fréquence"
    )
    
    prochaine_maintenance = models.DateField(
        verbose_name="Prochaine maintenance"
    )
    
    technicien_assigne = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenances_assignees',
        verbose_name="Technicien assigné",
        limit_choices_to={'user_type': 'employe'}  # 🆕 SIMPLIFIÉ (modèle déprécié)
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
        verbose_name="Programmation active"
    )
    
    notes = models.TextField(
        verbose_name="Notes",
        blank=True
    )
    
    class Meta:
        verbose_name = "Maintenance programmée"
        verbose_name_plural = "Maintenances programmées"
        ordering = ['prochaine_maintenance']
        indexes = [
            models.Index(fields=['prochaine_maintenance']),
            models.Index(fields=['frequence']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        lieu = self.appartement or self.bien
        return f"{self.titre} - {lieu}"
    
    @property
    def bien_concerne(self):
        """Retourne le bien concerné"""
        return self.appartement or self.bien
    
    def generate_next_intervention(self):
        """Génère la prochaine intervention à partir de cette programmation"""
        from datetime import timedelta
        
        if not self.is_active:
            return None
        
        # Créer l'intervention
        intervention = Intervention.objects.create(
            appartement=self.appartement,
            bien=self.bien,  # Compatibilité
            technicien=self.technicien_assigne,
            type_intervention='maintenance_preventive',
            priorite='normale',
            titre=self.titre,
            description=f"Maintenance programmée: {self.description}",
            statut='assigne' if self.technicien_assigne else 'signale',
            cout_estime=self.cout_estime,
        )
        
        # Calculer la prochaine date selon la fréquence
        if self.frequence == 'hebdomadaire':
            self.prochaine_maintenance += timedelta(weeks=1)
        elif self.frequence == 'mensuel':
            self.prochaine_maintenance += timedelta(days=30)
        elif self.frequence == 'trimestriel':
            self.prochaine_maintenance += timedelta(days=90)
        elif self.frequence == 'semestriel':
            self.prochaine_maintenance += timedelta(days=180)
        elif self.frequence == 'annuel':
            self.prochaine_maintenance += timedelta(days=365)
        
        self.save()
        return intervention

