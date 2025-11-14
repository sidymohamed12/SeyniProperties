from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounting.models.expenses import User
from apps.core.models import BaseModel, TimestampedModel
from apps.core.utils import generate_unique_reference
from apps.properties.models.appartement import Appartement
from apps.properties.models.etat_lieu import EtatDesLieux


# ====== ANCIEN MODÈLE PROPERTY (Maintenu temporairement pour compatibilité) ======

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