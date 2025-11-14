from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounting.models.expenses import User
from apps.core.models import BaseModel, TimestampedModel
from apps.core.utils import generate_unique_reference
from apps.properties.models.appartement import Appartement


# ====== ANCIEN MODÈLE PROPERTY (Maintenu temporairement pour compatibilité) ======

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
    
