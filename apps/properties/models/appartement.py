from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounting.models.expenses import User
from apps.core.models import BaseModel, TimestampedModel
from apps.core.utils import generate_unique_reference
from apps.properties.models.residence import Residence

# ====== NOUVEAUX MODÈLES POUR LA STRUCTURE BAILLEUR → RÉSIDENCE → APPARTEMENT ======

class Appartement(TimestampedModel):
    """
    Modèle représentant un appartement dans une résidence
    """
    
    TYPE_BIEN_CHOICES = [
        ('studio', 'Studio'),
        ('apartment', 'Appartement'),  # Garde compatibilité avec ancien
        ('f1', 'F1 (1 pièce)'),
        ('f2', 'F2 (2 pièces)'),
        ('f3', 'F3 (3 pièces)'),
        ('f4', 'F4 (4 pièces)'),
        ('f5_plus', 'F5+ (5 pièces et plus)'),
        ('duplex', 'Duplex'),
        ('penthouse', 'Penthouse'),
        ('villa', 'Villa'),  # Garde compatibilité
        ('commercial', 'Local commercial'),
        ('office', 'Bureau'),  # Garde compatibilité
        ('warehouse', 'Entrepôt'),  # Garde compatibilité
    ]
    
    STATUT_OCCUPATION_CHOICES = [
        ('available', 'Libre'),  # Garde compatibilité avec ancien
        ('libre', 'Libre'),
        ('occupied', 'Occupé'),  # Garde compatibilité avec ancien
        ('occupe', 'Occupé'),
        ('maintenance', 'En maintenance'),
        ('reserved', 'Réservé'),  # Garde compatibilité avec ancien
        ('reserve', 'Réservé'),
        ('hors_service', 'Hors service'),
    ]
    
    MODE_LOCATION_CHOICES = [
        ('short_term', 'Courte durée'),  # Garde compatibilité
        ('courte_duree', 'Courte durée (- 3 mois)'),
        ('long_term', 'Longue durée'),  # Garde compatibilité
        ('longue_duree', 'Longue durée (+ 3 mois)'),
        ('saisonniere', 'Saisonnière'),
        ('both', 'Les deux'),  # Garde compatibilité
    ]
    
    # Identification
    reference = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Référence",
        help_text="Référence unique de l'appartement (ex: APP-001)"
    )
    
    nom = models.CharField(
        max_length=200,
        verbose_name="Nom/Numéro",
        help_text="Ex: Appartement 3A, Bureau 12, Studio Rose"
    )
    
    # Relation avec la résidence
    residence = models.ForeignKey(
        Residence,
        on_delete=models.CASCADE,
        related_name='appartements',
        verbose_name="Résidence"
    )
    
    # Caractéristiques physiques
    etage = models.IntegerField(
        default=0,
        verbose_name="Étage",
        help_text="0 pour RDC, -1 pour sous-sol"
    )
    
    type_bien = models.CharField(
        max_length=20,
        choices=TYPE_BIEN_CHOICES,
        verbose_name="Type d'appartement"
    )
    
    # Garde les noms de champs existants pour compatibilité
    superficie = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Superficie (m²)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Champs alternatifs pour compatibilité avec l'ancien modèle
    surface_area = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Surface Area (m²)",
        help_text="Champ de compatibilité - utilise superficie"
    )
    
    nb_pieces = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Nombre de pièces",
        validators=[MinValueValidator(1)]
    )
    
    # Champ alternatif pour compatibilité
    rooms_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Rooms Count",
        help_text="Champ de compatibilité - utilise nb_pieces"
    )
    
    nb_chambres = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de chambres"
    )
    
    # Champ alternatif pour compatibilité
    bedrooms_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Bedrooms Count",
        help_text="Champ de compatibilité - utilise nb_chambres"
    )
    
    nb_sdb = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre de salles de bain"
    )
    
    # Champ alternatif pour compatibilité
    bathrooms_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Bathrooms Count",
        help_text="Champ de compatibilité - utilise nb_sdb"
    )
    
    nb_wc = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre de WC"
    )
    
    # Équipements
    is_meuble = models.BooleanField(
        default=False,
        verbose_name="Meublé"
    )
    
    # Champ alternatif pour compatibilité
    is_furnished = models.BooleanField(
        default=False,
        verbose_name="Is Furnished",
        help_text="Champ de compatibilité - utilise is_meuble"
    )
    
    has_balcon = models.BooleanField(
        default=False,
        verbose_name="Balcon/Terrasse"
    )
    
    has_parking = models.BooleanField(
        default=False,
        verbose_name="Place de parking"
    )
    
    has_climatisation = models.BooleanField(
        default=False,
        verbose_name="Climatisation"
    )
    
    equipements_inclus = models.TextField(
        blank=True,
        verbose_name="Équipements inclus",
        help_text="Réfrigérateur, lave-linge, TV, etc."
    )
    
    # Champ alternatif pour compatibilité (JSON)
    amenities = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Amenities",
        help_text="Champ de compatibilité - utilise equipements_inclus"
    )
    
    # État et disponibilité
    statut_occupation = models.CharField(
        max_length=20,
        choices=STATUT_OCCUPATION_CHOICES,
        default='libre',
        verbose_name="Statut d'occupation"
    )
    
    # Champ alternatif pour compatibilité
    occupancy_status = models.CharField(
        max_length=20,
        choices=STATUT_OCCUPATION_CHOICES,
        default='available',
        verbose_name="Occupancy Status",
        help_text="Champ de compatibilité - utilise statut_occupation"
    )
    
    mode_location = models.CharField(
        max_length=20,
        choices=MODE_LOCATION_CHOICES,
        default='longue_duree',
        verbose_name="Mode de location"
    )
    
    # Champ alternatif pour compatibilité
    rental_mode = models.CharField(
        max_length=20,
        choices=MODE_LOCATION_CHOICES,
        default='long_term',
        verbose_name="Rental Mode",
        help_text="Champ de compatibilité - utilise mode_location"
    )
    
    # Tarification
    loyer_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Loyer de base (FCFA)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Champ alternatif pour compatibilité
    base_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Base Rent (FCFA)",
        help_text="Champ de compatibilité - utilise loyer_base"
    )
    
    charges = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Charges mensuelles (FCFA)"
    )
    
    depot_garantie = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Dépôt de garantie (FCFA)",
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Champ alternatif pour compatibilité
    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Security Deposit (FCFA)",
        help_text="Champ de compatibilité - utilise depot_garantie"
    )
    
    frais_agence = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Frais d'agence (FCFA)"
    )
    
    # Informations complémentaires
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes",
        help_text="Notes visibles uniquement par l'équipe"
    )
    
    # Dates importantes
    date_derniere_renovation = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date dernière rénovation"
    )
    
    date_mise_en_location = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date mise en location"
    )
    
    class Meta:
        verbose_name = "Appartement"
        verbose_name_plural = "Appartements"
        ordering = ['residence__nom', 'etage', 'nom']
        unique_together = [['residence', 'nom']]
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['residence', 'statut_occupation']),
            models.Index(fields=['type_bien', 'mode_location']),
            models.Index(fields=['loyer_base']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_unique_reference('APP')
        
        # Synchroniser les champs de compatibilité
        if self.superficie and not self.surface_area:
            self.surface_area = self.superficie
        elif self.surface_area and not self.superficie:
            self.superficie = self.surface_area
            
        if self.nb_pieces and not self.rooms_count:
            self.rooms_count = self.nb_pieces
        elif self.rooms_count and not self.nb_pieces:
            self.nb_pieces = self.rooms_count
            
        if self.nb_chambres and not self.bedrooms_count:
            self.bedrooms_count = self.nb_chambres
        elif self.bedrooms_count and not self.nb_chambres:
            self.nb_chambres = self.bedrooms_count
            
        if self.nb_sdb and not self.bathrooms_count:
            self.bathrooms_count = self.nb_sdb
        elif self.bathrooms_count and not self.nb_sdb:
            self.nb_sdb = self.bathrooms_count
            
        if self.is_meuble != self.is_furnished:
            self.is_furnished = self.is_meuble
            
        if self.loyer_base and not self.base_rent:
            self.base_rent = self.loyer_base
        elif self.base_rent and not self.loyer_base:
            self.loyer_base = self.base_rent
            
        if self.depot_garantie and not self.security_deposit:
            self.security_deposit = self.depot_garantie
        elif self.security_deposit and not self.depot_garantie:
            self.depot_garantie = self.security_deposit
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.residence.nom} - {self.nom}"
    
    @property
    def loyer_total(self):
        """Loyer total (base + charges)"""
        return self.loyer_base + self.charges
    
    @property
    def total_rent(self):
        """Compatibilité avec ancien modèle"""
        return self.loyer_total
    
    @property
    def bailleur(self):
        """Accès rapide au bailleur via la résidence"""
        return self.residence.bailleur
    
    @property
    def landlord(self):
        """Compatibilité avec ancien modèle"""
        return self.bailleur
    
    @property
    def adresse_complete(self):
        """Adresse complète de l'appartement"""
        return f"{self.nom}, {self.residence.adresse}, {self.residence.quartier}, {self.residence.ville}"
    
    @property
    def address(self):
        """Compatibilité avec ancien modèle"""
        return self.residence.adresse
    
    @property
    def neighborhood(self):
        """Compatibilité avec ancien modèle"""
        return self.residence.quartier
    
    @property
    def city(self):
        """Compatibilité avec ancien modèle"""
        return self.residence.ville
    
    @property
    def postal_code(self):
        """Compatibilité avec ancien modèle"""
        return self.residence.code_postal
    
    @property
    def name(self):
        """Compatibilité avec ancien modèle"""
        return self.nom
    
    @property
    def property_type(self):
        """Compatibilité avec ancien modèle"""
        return self.type_bien
    
    @property
    def area(self):
        """Compatibilité avec ancien modèle"""
        return self.superficie
    
    @property
    def rooms(self):
        """Compatibilité avec ancien modèle"""
        return self.nb_pieces
    
    @property
    def is_available(self):
        """Compatibilité avec ancien modèle"""
        return self.statut_occupation in ['libre', 'available']
    
    @property
    def contrat_actuel(self):
        """Contrat actuel s'il existe"""
        try:
            from apps.contracts.models import RentalContract
            return self.contrats.filter(
                statut='actif',
                date_debut__lte=timezone.now().date(),
                date_fin__gte=timezone.now().date()
            ).first()
        except:
            return None
    
    @property
    def current_contract(self):
        """Compatibilité avec ancien modèle"""
        return self.contrat_actuel
    
    @property
    def locataire_actuel(self):
        """Locataire actuel s'il existe"""
        contrat = self.contrat_actuel
        return contrat.locataire if contrat else None


class AppartementMedia(TimestampedModel):
    """
    Médias associés à un appartement (photos, documents, vidéos)
    """
    
    TYPE_MEDIA_CHOICES = [
        ('photo_principale', 'Photo principale'),
        ('photo_interieur', 'Photo intérieur'),
        ('photo_exterieur', 'Photo extérieur'),
        ('plan', 'Plan de l\'appartement'),
        ('document_legal', 'Document légal'),
        ('video_visite', 'Vidéo de visite'),
        ('facture', 'Facture'),
        ('autre', 'Autre'),
    ]
    
    appartement = models.ForeignKey(
        Appartement,
        on_delete=models.CASCADE,
        related_name='medias',
        verbose_name="Appartement"
    )
    
    type_media = models.CharField(
        max_length=20,
        choices=TYPE_MEDIA_CHOICES,
        verbose_name="Type de média"
    )
    
    fichier = models.FileField(
        upload_to='appartements/medias/%Y/%m/',
        verbose_name="Fichier"
    )
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    is_principal = models.BooleanField(
        default=False,
        verbose_name="Média principal",
        help_text="Une seule photo principale par appartement"
    )
    
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    is_public = models.BooleanField(
        default=True,
        verbose_name="Visible publiquement",
        help_text="Visible sur le portail locataire"
    )
    
    class Meta:
        verbose_name = "Média d'appartement"
        verbose_name_plural = "Médias d'appartements"
        ordering = ['ordre', 'created_at']
    
    def __str__(self):
        return f"{self.appartement} - {self.titre}"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule photo principale par appartement
        if self.is_principal:
            AppartementMedia.objects.filter(
                appartement=self.appartement,
                is_principal=True
            ).exclude(pk=self.pk).update(is_principal=False)
        
        super().save(*args, **kwargs)

