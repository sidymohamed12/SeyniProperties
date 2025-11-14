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

