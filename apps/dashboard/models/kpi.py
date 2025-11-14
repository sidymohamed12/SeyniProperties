from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.core.models import BaseModel

User = get_user_model()

class KPI(BaseModel):
    """Modèle pour les indicateurs de performance clés"""
    
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du KPI"
    )
    
    description = models.TextField(
        verbose_name="Description",
        blank=True
    )
    
    unite = models.CharField(
        max_length=20,
        choices=[
            ('pourcentage', '%'),
            ('euro', '€'),
            ('nombre', 'Unité'),
            ('jours', 'Jours'),
        ],
        verbose_name="Unité"
    )
    
    valeur_actuelle = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valeur actuelle"
    )
    
    valeur_objectif = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valeur objectif"
    )
    
    valeur_precedente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valeur précédente"
    )
    
    tendance = models.CharField(
        max_length=10,
        choices=[
            ('hausse', 'Hausse'),
            ('baisse', 'Baisse'),
            ('stable', 'Stable'),
        ],
        default='stable',
        verbose_name="Tendance"
    )
    
    couleur = models.CharField(
        max_length=10,
        choices=[
            ('green', 'Vert'),
            ('orange', 'Orange'),
            ('red', 'Rouge'),
            ('blue', 'Bleu'),
        ],
        default='blue',
        verbose_name="Couleur d'affichage"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    ordre_affichage = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    date_derniere_maj = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour"
    )
    
    class Meta:
        verbose_name = "KPI"
        verbose_name_plural = "KPIs"
        ordering = ['ordre_affichage', 'nom']
    
    def __str__(self):
        return f"{self.nom}: {self.valeur_actuelle} {self.get_unite_display()}"
    
    @property
    def evolution_pourcentage(self):
        """Calcule l'évolution en pourcentage par rapport à la valeur précédente"""
        if not self.valeur_precedente or self.valeur_precedente == 0:
            return 0
        
        evolution = ((self.valeur_actuelle - self.valeur_precedente) / self.valeur_precedente) * 100
        return round(evolution, 2)
    
    @property
    def atteint_objectif(self):
        """Vérifie si l'objectif est atteint"""
        if not self.valeur_objectif:
            return None
        return self.valeur_actuelle >= self.valeur_objectif
    
    def update_value(self, nouvelle_valeur):
        """Met à jour la valeur du KPI"""
        self.valeur_precedente = self.valeur_actuelle
        self.valeur_actuelle = nouvelle_valeur
        
        # Déterminer la tendance
        if self.valeur_precedente:
            if nouvelle_valeur > self.valeur_precedente:
                self.tendance = 'hausse'
            elif nouvelle_valeur < self.valeur_precedente:
                self.tendance = 'baisse'
            else:
                self.tendance = 'stable'
        
        self.save()
