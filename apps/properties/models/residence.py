
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounting.models.expenses import User
from apps.core.models import BaseModel, TimestampedModel
from apps.core.utils import generate_unique_reference

# ====== NOUVEAUX MODÈLES POUR LA STRUCTURE BAILLEUR → RÉSIDENCE → APPARTEMENT ======

class Residence(TimestampedModel):
    """
    Modèle représentant une résidence (immeuble, bâtiment)
    Un bailleur possède une ou plusieurs résidences
    """
    
    STATUT_CHOICES = [
        ('active', 'Active'),
        ('en_construction', 'En construction'),
        ('maintenance', 'En maintenance'),
        ('inactive', 'Inactive'),
    ]
    
    TYPE_RESIDENCE_CHOICES = [
        ('immeuble', 'Immeuble'),
        ('villa_divisee', 'Villa divisée'),
        ('complexe', 'Complexe résidentiel'),
        ('batiment_commercial', 'Bâtiment commercial'),
    ]

    TYPE_GESTION_CHOICES = [
        ('location', 'Gestion locative'),
        ('syndic', 'Syndic de copropriété'),
        ('mixte', 'Mixte (location + syndic)'),
    ]
    
    # Identification
    reference = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Référence",
        help_text="Référence unique de la résidence (ex: RES-001)"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom de la résidence",
        help_text="Ex: Résidence Les Palmiers, Immeuble Dakar Plaza"
    )
    
    type_residence = models.CharField(
        max_length=20,
        choices=TYPE_RESIDENCE_CHOICES,
        default='immeuble',
        verbose_name="Type de résidence"
    )

    type_gestion = models.CharField(
        max_length=20,
        choices=TYPE_GESTION_CHOICES,
        default='location',
        verbose_name="Type de gestion",
        help_text="Définit si Imany gère cette résidence en location, en tant que syndic, ou les deux"
    )
    
    # Localisation
    adresse = models.TextField(
        verbose_name="Adresse complète"
    )
    
    quartier = models.CharField(
        max_length=100,
        verbose_name="Quartier"
    )
    
    ville = models.CharField(
        max_length=100,
        default="Dakar",
        verbose_name="Ville"
    )
    
    code_postal = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Code postal"
    )
    
    # Informations techniques
    nb_etages = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre d'étages",
        validators=[MinValueValidator(1)]
    )
    
    nb_appartements_total = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre total d'appartements",
        validators=[MinValueValidator(1)]
    )
    
    annee_construction = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Année de construction",
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(2030)
        ]
    )
    
    # Propriétaire - Relation avec le modèle Tiers
    # Optionnel pour les résidences de type 'syndic' (gérées en copropriété)
    proprietaire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='residences',
        verbose_name="Propriétaire",
        limit_choices_to={'type_tiers': 'proprietaire'},
        null=True,
        blank=True,
        help_text="Obligatoire pour gestion locative/mixte, optionnel pour syndic"
    )
    
    # Status et état
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='active',
        verbose_name="Statut"
    )
    
    # Informations complémentaires
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    equipements = models.TextField(
        blank=True,
        verbose_name="Équipements communs",
        help_text="Ascenseur, parking, gardien, etc."
    )
    
    # Coordonnées GPS (optionnel)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name="Latitude"
    )
    
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name="Longitude"
    )
    
    class Meta:
        verbose_name = "Résidence"
        verbose_name_plural = "Résidences"
        ordering = ['nom', '-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['proprietaire', 'statut']),
            models.Index(fields=['ville', 'quartier']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_unique_reference('RES')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nom} - {self.quartier}"
    
    @property
    def nb_appartements_disponibles(self):
        """Nombre d'appartements libres"""
        return self.appartements.filter(statut_occupation='libre').count()
    
    @property
    def nb_appartements_occupes(self):
        """Nombre d'appartements occupés"""
        return self.appartements.filter(statut_occupation='occupe').count()
    
    @property
    def taux_occupation(self):
        """Taux d'occupation en pourcentage"""
        if self.nb_appartements_total == 0:
            return 0
        return round((self.nb_appartements_occupes / self.nb_appartements_total) * 100, 2)
