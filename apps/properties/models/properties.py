from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounting.models.expenses import User
from apps.core.models import BaseModel, TimestampedModel
from apps.core.utils import generate_unique_reference


# ====== ANCIEN MODÈLE PROPERTY (Maintenu temporairement pour compatibilité) ======

class Property(TimestampedModel):
    """
    ANCIEN MODÈLE - Maintenu temporairement pour compatibilité
    À SUPPRIMER après migration complète vers Appartement
    """
    
    PROPERTY_TYPES = [
        ('studio', 'Studio'),
        ('apartment', 'Appartement'),
        ('villa', 'Villa'),
        ('commercial', 'Local commercial'),
        ('office', 'Bureau'),
        ('warehouse', 'Entrepôt'),
    ]
    
    OCCUPANCY_STATUS = [
        ('available', 'Libre'),
        ('occupied', 'Occupé'),
        ('maintenance', 'En maintenance'),
        ('reserved', 'Réservé'),
    ]
    
    RENTAL_MODES = [
        ('short_term', 'Courte durée'),
        ('long_term', 'Longue durée'),
        ('both', 'Les deux'),
    ]
    
    # Informations de base
    reference = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Référence"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du bien"
    )
    
    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPES,
        verbose_name="Type de bien"
    )
    
    # Localisation
    address = models.TextField(verbose_name="Adresse")
    neighborhood = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Quartier"
    )
    city = models.CharField(
        max_length=100,
        default='Dakar',
        verbose_name="Ville"
    )
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Code postal"
    )
    
    # Caractéristiques
    surface_area = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Superficie (m²)"
    )
    
    rooms_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de pièces"
    )
    
    bedrooms_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de chambres"
    )
    
    bathrooms_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de salles de bain"
    )
    
    is_furnished = models.BooleanField(
        default=False,
        verbose_name="Meublé"
    )
    
    # Statut et mode de location
    occupancy_status = models.CharField(
        max_length=20,
        choices=OCCUPANCY_STATUS,
        default='available',
        verbose_name="Statut d'occupation"
    )
    
    rental_mode = models.CharField(
        max_length=20,
        choices=RENTAL_MODES,
        default='long_term',
        verbose_name="Mode de location"
    )
    
    # Tarification
    base_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Loyer de base (FCFA)"
    )
    
    charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Charges (FCFA)"
    )
    
    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Dépôt de garantie (FCFA)"
    )
    
    # Relations
    landlord = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='properties_legacy',
        limit_choices_to={'type_tiers': 'proprietaire'},
        verbose_name="Propriétaire"
    )
    
    # Métadonnées
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    amenities = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Équipements"
    )
    
    class Meta:
        verbose_name = "Bien immobilier (Legacy)"
        verbose_name_plural = "Biens immobiliers (Legacy)"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.reference:
            from apps.core.utils import generate_reference
            self.reference = generate_reference('PROP')
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.reference} - {self.name}"
    
    @property
    def total_rent(self):
        """Calcule le loyer total (base + charges)"""
        base = self.base_rent or 0
        charges_amount = self.charges or 0
        return base + charges_amount
    
    @property
    def current_contract(self):
        """Retourne le contrat actuel s'il existe"""
        try:
            return self.contracts.filter(status='active').first()
        except:
            return None
    
    @property
    def is_available(self):
        return self.occupancy_status == 'available'
    
    @property
    def area(self):
        return self.surface_area
    
    @property
    def rooms(self):
        return self.rooms_count

