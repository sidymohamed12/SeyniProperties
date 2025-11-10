# apps/properties/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounting.models import User
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


# apps/properties/models.py
# (Ajouter ces modèles à la fin du fichier existant)

class EtatDesLieux(BaseModel):
    """
    Modèle pour l'état des lieux (entrée ou sortie)
    """
    
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    
    # Référence unique
    numero_etat = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro d'état des lieux",
        help_text="Généré automatiquement (ex: EDL-E-2025-001 ou EDL-S-2025-001)"
    )
    
    # Type d'état des lieux
    type_etat = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Type d'état des lieux"
    )
    
    # Liens
    contrat = models.ForeignKey(
        'contracts.RentalContract',
        on_delete=models.CASCADE,
        related_name='etats_lieux',
        verbose_name="Contrat"
    )
    
    appartement = models.ForeignKey(
        Appartement,
        on_delete=models.CASCADE,
        related_name='etats_lieux',
        verbose_name="Appartement"
    )
    
    locataire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='etats_lieux',
        verbose_name="Locataire",
        limit_choices_to={'type_tiers': 'locataire'}
    )
    
    # Informations générales
    date_etat = models.DateField(
        verbose_name="Date de l'état des lieux",
        default=timezone.now
    )
    
    commercial_imany = models.CharField(
        max_length=100,
        verbose_name="Commercial IMANY",
        blank=True
    )
    
    # Observations globales
    observation_globale = models.TextField(
        verbose_name="Observation globale",
        blank=True
    )
    
    # Signatures
    signe_bailleur = models.BooleanField(
        default=False,
        verbose_name="Signé par le bailleur"
    )
    
    signe_locataire = models.BooleanField(
        default=False,
        verbose_name="Signé par le locataire"
    )
    
    date_signature = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de signature"
    )
    
    # Fichier PDF généré
    fichier_pdf = models.FileField(
        upload_to='etats_lieux/pdf/',
        verbose_name="Fichier PDF",
        blank=True,
        null=True
    )
    
    # Créé par
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='etats_lieux_crees',
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "État des lieux"
        verbose_name_plural = "États des lieux"
        ordering = ['-date_etat']
    
    def __str__(self):
        return f"{self.numero_etat} - {self.get_type_etat_display()} - {self.appartement}"
    
    def save(self, *args, **kwargs):
        # Générer le numéro d'état des lieux si nouveau
        if not self.numero_etat:
            from django.utils import timezone
            year = timezone.now().year
            prefix = f'EDL-{"E" if self.type_etat == "entree" else "S"}-{year}-'
            
            last_etat = EtatDesLieux.objects.filter(
                numero_etat__startswith=prefix
            ).order_by('-numero_etat').first()
            
            if last_etat:
                last_number = int(last_etat.numero_etat.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.numero_etat = f'{prefix}{new_number:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def residence(self):
        """Retourne la résidence de l'appartement"""
        return self.appartement.residence if self.appartement else None
    
    @property
    def is_complet(self):
        """Vérifie si l'état des lieux est complet"""
        return self.signe_bailleur and self.signe_locataire


class EtatDesLieuxDetail(BaseModel):
    """
    Modèle pour les détails de l'état des lieux (chaque ligne du tableau)
    """
    
    etat_lieux = models.ForeignKey(
        EtatDesLieux,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name="État des lieux"
    )
    
    # Colonnes du tableau
    piece = models.CharField(
        max_length=100,
        verbose_name="Pièce",
        help_text="Ex: Salon, Chambre 1, Cuisine, etc."
    )
    
    corps_etat = models.CharField(
        max_length=200,
        verbose_name="Corps d'état",
        help_text="Ex: Murs, Sol, Plafond, Fenêtres, Portes, etc."
    )
    
    observations = models.TextField(
        verbose_name="Observations",
        blank=True,
        help_text="État, dégâts éventuels, remarques"
    )
    
    # Ordre d'affichage
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre"
    )
    
    class Meta:
        verbose_name = "Détail état des lieux"
        verbose_name_plural = "Détails états des lieux"
        ordering = ['ordre', 'piece']
    
    def __str__(self):
        return f"{self.piece} - {self.corps_etat}"
    



class RemiseDesCles(BaseModel):
    """
    Modèle pour l'attestation de remise des clés
    """
    
    TYPE_REMISE_CHOICES = [
        ('entree', 'Remise à l\'entrée'),
        ('sortie', 'Restitution à la sortie'),
    ]
    
    # Référence unique
    numero_attestation = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro d'attestation",
        help_text="Généré automatiquement (ex: RDC-E-2025-001)"
    )
    
    # Type de remise
    type_remise = models.CharField(
        max_length=10,
        choices=TYPE_REMISE_CHOICES,
        verbose_name="Type de remise"
    )
    
    # Liens
    contrat = models.ForeignKey(
        'contracts.RentalContract',
        on_delete=models.CASCADE,
        related_name='remises_cles',
        verbose_name="Contrat"
    )
    
    appartement = models.ForeignKey(
        Appartement,
        on_delete=models.CASCADE,
        related_name='remises_cles',
        verbose_name="Appartement"
    )
    
    locataire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.CASCADE,
        related_name='remises_cles',
        verbose_name="Locataire",
        limit_choices_to={'type_tiers': 'locataire'}
    )
    
    # Lien optionnel avec l'état des lieux
    etat_lieux = models.ForeignKey(
        EtatDesLieux,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remises_cles',
        verbose_name="État des lieux associé"
    )
    
    # Informations de remise
    date_remise = models.DateField(
        verbose_name="Date de remise",
        default=timezone.now
    )
    
    heure_remise = models.TimeField(
        verbose_name="Heure de remise",
        null=True,
        blank=True
    )
    
    # Détails des clés
    nombre_cles_appartement = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de clés de l'appartement"
    )
    
    nombre_cles_boite_lettres = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de clés de boîte aux lettres"
    )
    
    nombre_cles_garage = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de clés de garage/parking"
    )
    
    nombre_badges = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de badges d'accès"
    )
    
    nombre_telecommandes = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de télécommandes"
    )
    
    # Autres équipements
    autres_equipements = models.TextField(
        verbose_name="Autres équipements remis",
        blank=True,
        help_text="Ex: Clés de cave, interphone, etc."
    )
    
    # Observations
    observations = models.TextField(
        verbose_name="Observations",
        blank=True
    )
    
    # Personnes présentes
    remis_par = models.CharField(
        max_length=100,
        verbose_name="Remis par",
        help_text="Nom de la personne qui remet les clés"
    )
    
    recu_par = models.CharField(
        max_length=100,
        verbose_name="Reçu par",
        help_text="Nom de la personne qui reçoit les clés"
    )
    
    # Signatures
    signe_bailleur = models.BooleanField(
        default=False,
        verbose_name="Signé par le bailleur/représentant"
    )
    
    signe_locataire = models.BooleanField(
        default=False,
        verbose_name="Signé par le locataire"
    )
    
    date_signature = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de signature"
    )
    
    # Fichier PDF généré
    fichier_pdf = models.FileField(
        upload_to='remises_cles/pdf/',
        verbose_name="Fichier PDF",
        blank=True,
        null=True
    )
    
    # Créé par
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='remises_cles_creees',
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Remise des clés"
        verbose_name_plural = "Remises des clés"
        ordering = ['-date_remise']
    
    def __str__(self):
        return f"{self.numero_attestation} - {self.get_type_remise_display()} - {self.appartement}"
    
    def save(self, *args, **kwargs):
        # Générer le numéro d'attestation si nouveau
        if not self.numero_attestation:
            from django.utils import timezone
            year = timezone.now().year
            prefix = f'RDC-{"E" if self.type_remise == "entree" else "S"}-{year}-'
            
            last_remise = RemiseDesCles.objects.filter(
                numero_attestation__startswith=prefix
            ).order_by('-numero_attestation').first()
            
            if last_remise:
                last_number = int(last_remise.numero_attestation.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.numero_attestation = f'{prefix}{new_number:03d}'
        
        super().save(*args, **kwargs)
    
    @property
    def residence(self):
        """Retourne la résidence de l'appartement"""
        return self.appartement.residence if self.appartement else None
    
    @property
    def total_cles(self):
        """Retourne le nombre total de clés et équipements"""
        return (
            self.nombre_cles_appartement +
            self.nombre_cles_boite_lettres +
            self.nombre_cles_garage +
            self.nombre_badges +
            self.nombre_telecommandes
        )
    
    @property
    def is_complet(self):
        """Vérifie si l'attestation est complète"""
        return self.signe_bailleur and self.signe_locataire