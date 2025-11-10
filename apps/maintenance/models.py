# apps/maintenance/models.py - Version unifiée avec Travail

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference

User = get_user_model()


# ============================================================================
# MODÈLE UNIFIÉ TRAVAIL (Remplace Intervention + Tache)
# ============================================================================

class Travail(BaseModel):
    """
    Modèle unifié pour tous les travaux
    Remplace les anciens modèles Intervention et Tache
    Couvre: interventions réactives, tâches planifiées, maintenance préventive, projets
    """

    NATURE_CHOICES = [
        ('reactif', 'Réactif (intervention urgente)'),
        ('planifie', 'Planifié (tâche programmée)'),
        ('preventif', 'Préventif (maintenance)'),
        ('projet', 'Projet (travaux importants)'),
    ]

    TYPE_TRAVAIL_CHOICES = [
        ('plomberie', 'Plomberie'),
        ('electricite', 'Électricité'),
        ('menuiserie', 'Menuiserie'),
        ('peinture', 'Peinture'),
        ('menage', 'Ménage'),
        ('serrurerie', 'Serrurerie'),
        ('climatisation', 'Climatisation'),
        ('jardinage', 'Jardinage'),
        ('securite', 'Sécurité'),
        ('vitrerie', 'Vitrerie'),
        ('maconnerie', 'Maçonnerie'),
        ('toiture', 'Toiture'),
        ('etat_lieux', 'État des lieux'),
        ('visite_controle', 'Visite de contrôle'),
        ('livraison', 'Livraison'),
        ('administrative', 'Tâche administrative'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('signale', 'Signalé'),
        ('planifie', 'Planifié'),
        ('assigne', 'Assigné'),
        ('en_attente_materiel', 'En attente matériel'),  # 🆕 Nouveau statut
        ('en_cours', 'En cours'),
        ('complete', 'Terminé'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]

    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]

    RECURRENCE_CHOICES = [
        ('aucune', 'Aucune'),
        ('quotidien', 'Quotidienne'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('annuelle', 'Annuelle'),
    ]

    # ========== IDENTIFICATION ==========
    numero_travail = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de travail",
        help_text="Généré automatiquement"
    )

    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )

    description = models.TextField(
        verbose_name="Description",
        blank=True
    )

    # ========== CARACTÉRISTIQUES ==========
    nature = models.CharField(
        max_length=15,
        choices=NATURE_CHOICES,
        verbose_name="Nature du travail"
    )

    type_travail = models.CharField(
        max_length=25,
        choices=TYPE_TRAVAIL_CHOICES,
        verbose_name="Type de travail"
    )

    priorite = models.CharField(
        max_length=15,
        choices=PRIORITE_CHOICES,
        default='normale',
        verbose_name="Priorité"
    )

    statut = models.CharField(
        max_length=25,
        choices=STATUT_CHOICES,
        default='signale',
        verbose_name="Statut"
    )

    # ========== LOCALISATION ==========
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='travaux',
        verbose_name="Appartement concerné"
    )

    residence = models.ForeignKey(
        'properties.Residence',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='travaux',
        verbose_name="Résidence concernée"
    )

    # ========== PERSONNES IMPLIQUÉES ==========
    signale_par = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travaux_signales',
        verbose_name="Signalé par",
        limit_choices_to={'type_tiers': 'locataire'}
    )

    assigne_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travaux_assignes',
        verbose_name="Assigné à",
        limit_choices_to={'user_type': 'employe'}  # 🆕 SIMPLIFIÉ: Un seul type d'employé
    )

    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='travaux_crees',
        verbose_name="Créé par"
    )

    # ========== DATES ==========
    date_signalement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de signalement"
    )

    date_prevue = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date prévue"
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

    duree_estimee = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Durée estimée"
    )

    # ========== RÉCURRENCE ==========
    is_recurrent = models.BooleanField(
        default=False,
        verbose_name="Travail récurrent"
    )

    recurrence = models.CharField(
        max_length=15,
        choices=RECURRENCE_CHOICES,
        default='aucune',
        verbose_name="Type de récurrence"
    )

    recurrence_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fin de récurrence"
    )

    # ========== COÛTS ==========
    cout_estime = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Coût estimé (FCFA)"
    )

    cout_reel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Coût réel (FCFA)"
    )

    # ========== SUIVI ET SATISFACTION ==========
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )

    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes"
    )

    satisfaction = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfaction (1-5)"
    )

    temps_reel = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Temps réel passé"
    )

    class Meta:
        verbose_name = "Travail"
        verbose_name_plural = "Travaux"
        ordering = ['-created_at', '-date_signalement']
        indexes = [
            models.Index(fields=['numero_travail']),
            models.Index(fields=['statut', 'priorite']),
            models.Index(fields=['nature', 'type_travail']),
            models.Index(fields=['date_prevue']),
            models.Index(fields=['assigne_a', 'statut']),
            models.Index(fields=['appartement']),
            models.Index(fields=['residence']),
        ]

    def save(self, *args, **kwargs):
        if not self.numero_travail:
            self.numero_travail = generate_unique_reference('TRV')

        # Auto-définir date_signalement pour nature réactive
        if self.nature == 'reactif' and not self.date_signalement:
            self.date_signalement = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_travail} - {self.titre}"

    @property
    def lieu_travail(self):
        """Retourne le lieu du travail"""
        if self.appartement:
            return f"{self.appartement.nom} - {self.appartement.residence.nom}"
        elif self.residence:
            return self.residence.nom
        return "Non spécifié"

    @property
    def duree_reelle(self):
        """Calcule la durée réelle du travail"""
        if self.date_debut and self.date_fin:
            return self.date_fin - self.date_debut
        return self.temps_reel

    @property
    def est_en_retard(self):
        """Vérifie si le travail est en retard"""
        if self.statut in ['complete', 'valide', 'annule']:
            return False

        if self.nature == 'reactif' and self.date_signalement:
            # En retard après 48h pour urgente, 7 jours pour normale
            limite = timezone.now() - timezone.timedelta(
                hours=48 if self.priorite == 'urgente' else 168
            )
            return self.date_signalement < limite

        if self.date_prevue:
            return timezone.now() > self.date_prevue

        return False

    @property
    def necessite_materiel(self):
        """Vérifie si le travail nécessite du matériel (a des demandes d'achat)"""
        return self.demandes_achat.exists()

    @property
    def statut_materiel(self):
        """
        Retourne le statut du matériel pour ce travail

        Returns:
            str: 'aucun_materiel', 'en_attente_validation', 'en_attente_reception',
                 'materiel_recu', 'materiel_partiel'
        """
        demandes = self.demandes_achat.all()

        if not demandes.exists():
            return 'aucun_materiel'

        # Vérifier les différents statuts
        etapes = list(demandes.values_list('etape_workflow', flat=True))

        if all(e in ['brouillon', 'en_attente'] for e in etapes):
            return 'en_attente_validation'

        if all(e == 'recue' for e in etapes):
            return 'materiel_recu'

        if any(e in ['brouillon', 'en_attente', 'valide_responsable', 'comptable',
                     'validation_dg', 'approuve', 'en_cours_achat'] for e in etapes):
            return 'en_attente_reception'

        if any(e == 'recue' for e in etapes):
            return 'materiel_partiel'

        return 'en_attente_reception'

    @property
    def cout_total_materiel(self):
        """Calcule le coût total du matériel (toutes les demandes d'achat)"""
        demandes = self.demandes_achat.filter(
            etape_workflow__in=['recue', 'paye']
        )
        return sum(d.montant_ttc for d in demandes) if demandes.exists() else Decimal('0.00')

    def creer_demande_achat(self, demandeur, service_fonction, motif_principal, articles):
        """
        Crée une demande d'achat liée à ce travail
        Architecture 1-to-Many: Un travail peut avoir plusieurs demandes d'achat

        Args:
            demandeur (User): Utilisateur qui fait la demande
            service_fonction (str): Service/fonction du demandeur
            motif_principal (str): Motif principal de la demande
            articles (list): Liste de dict avec: designation, quantite, unite, prix_unitaire, fournisseur, motif

        Returns:
            Invoice: La demande d'achat créée

        Example:
            >>> travail = Travail.objects.get(id=1)
            >>> demande = travail.creer_demande_achat(
            ...     demandeur=request.user,
            ...     service_fonction="Maintenance",
            ...     motif_principal="Matériel pour plomberie",
            ...     articles=[
            ...         {
            ...             'designation': 'Tuyau PVC 50mm',
            ...             'quantite': 10,
            ...             'unite': 'mètre',
            ...             'prix_unitaire': 2500,
            ...             'fournisseur': 'Quincaillerie du Nord',
            ...             'motif': 'Remplacement tuyauterie endommagée'
            ...         }
            ...     ]
            ... )
        """
        from apps.payments.models import Invoice, LigneDemandeAchat, HistoriqueValidation
        from decimal import Decimal

        # Calculer le montant total
        montant_total = Decimal('0.00')
        for article in articles:
            quantite = Decimal(str(article['quantite']))
            prix_unitaire = Decimal(str(article['prix_unitaire']))
            montant_total += quantite * prix_unitaire

        # Créer la facture de type demande_achat
        demande = Invoice.objects.create(
            type_facture='demande_achat',
            montant_ht=montant_total,
            montant_ttc=montant_total,
            date_emission=timezone.now().date(),
            date_echeance=timezone.now().date() + timezone.timedelta(days=30),
            description=f"Demande d'achat pour {self.titre} ({self.numero_travail})",
            statut='brouillon',
            creee_par=demandeur,
            is_manual=True,
            # Champs workflow
            etape_workflow='brouillon',
            demandeur=demandeur,
            date_demande=timezone.now().date(),
            service_fonction=service_fonction,
            motif_principal=motif_principal,
            # 🆕 Liaison avec le travail (relation 1-to-Many)
            travail_lie=self,
        )

        # Créer les lignes de demande
        for article in articles:
            LigneDemandeAchat.objects.create(
                demande=demande,
                designation=article['designation'],
                quantite=Decimal(str(article['quantite'])),
                unite=article.get('unite', 'unité'),
                fournisseur=article.get('fournisseur', ''),
                prix_unitaire=Decimal(str(article['prix_unitaire'])),
                motif=article.get('motif', motif_principal),
            )

        # Créer l'historique
        HistoriqueValidation.objects.create(
            demande=demande,
            action='creation',
            effectue_par=demandeur,
            commentaire=f"Demande créée pour le travail {self.numero_travail}"
        )

        # 🆕 Changer le statut du travail si c'est sa première demande
        if self.statut not in ['en_attente_materiel', 'en_cours', 'complete', 'valide']:
            self.statut = 'en_attente_materiel'
            self.save()

        return demande

    def marquer_complete(self, commentaire=""):
        """Marque le travail comme terminé"""
        self.statut = 'complete'
        if not self.date_fin:
            self.date_fin = timezone.now()

        if commentaire:
            self.commentaire = commentaire

        # Calculer le temps réel
        if self.date_debut:
            self.temps_reel = self.date_fin - self.date_debut

        self.save()

        # Créer prochaine occurrence si récurrent
        if self.is_recurrent and self.recurrence != 'aucune':
            self.generer_prochaine_occurrence()

    def generer_prochaine_occurrence(self):
        """Génère la prochaine occurrence pour un travail récurrent"""
        from datetime import timedelta

        if not self.is_recurrent or self.recurrence == 'aucune':
            return None

        # Calculer la prochaine date
        date_base = self.date_prevue or timezone.now()

        if self.recurrence == 'quotidien':
            prochaine_date = date_base + timedelta(days=1)
        elif self.recurrence == 'hebdomadaire':
            prochaine_date = date_base + timedelta(weeks=1)
        elif self.recurrence == 'mensuelle':
            prochaine_date = date_base + timedelta(days=30)
        elif self.recurrence == 'trimestrielle':
            prochaine_date = date_base + timedelta(days=90)
        elif self.recurrence == 'annuelle':
            prochaine_date = date_base + timedelta(days=365)
        else:
            return None

        # Vérifier la date de fin
        if self.recurrence_fin and prochaine_date.date() > self.recurrence_fin:
            return None

        # Créer le nouveau travail
        nouveau = Travail.objects.create(
            titre=self.titre,
            description=self.description,
            nature=self.nature,
            type_travail=self.type_travail,
            priorite=self.priorite,
            appartement=self.appartement,
            residence=self.residence,
            assigne_a=self.assigne_a,
            cree_par=self.cree_par,
            date_prevue=prochaine_date,
            duree_estimee=self.duree_estimee,
            cout_estime=self.cout_estime,
            is_recurrent=True,
            recurrence=self.recurrence,
            recurrence_fin=self.recurrence_fin,
            statut='planifie',
        )

        return nouveau


class TravailMedia(BaseModel):
    """
    Médias liés aux travaux (photos, documents, factures)
    """

    TYPE_MEDIA_CHOICES = [
        ('photo_avant', 'Photo avant travaux'),
        ('photo_apres', 'Photo après travaux'),
        ('photo_probleme', 'Photo du problème'),
        ('facture', 'Facture'),
        ('devis', 'Devis'),
        ('bon_commande', 'Bon de commande'),
        ('rapport', 'Rapport'),
        ('plan', 'Plan/Schéma'),
        ('autre', 'Autre'),
    ]

    travail = models.ForeignKey(
        Travail,
        on_delete=models.CASCADE,
        related_name='medias',
        verbose_name="Travail"
    )

    type_media = models.CharField(
        max_length=20,
        choices=TYPE_MEDIA_CHOICES,
        verbose_name="Type de média"
    )

    fichier = models.FileField(
        upload_to='travaux/medias/%Y/%m/',
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
        verbose_name = "Média de travail"
        verbose_name_plural = "Médias de travaux"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.travail.numero_travail} - {self.get_type_media_display()}"


class TravailChecklist(BaseModel):
    """
    Éléments de checklist pour les travaux
    Permet de définir des étapes à suivre
    """

    travail = models.ForeignKey(
        Travail,
        on_delete=models.CASCADE,
        related_name='checklist',
        verbose_name="Travail"
    )

    description = models.CharField(
        max_length=200,
        verbose_name="Description de l'étape"
    )

    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre"
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name="Terminé"
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

    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )

    class Meta:
        verbose_name = "Checklist de travail"
        verbose_name_plural = "Checklists de travaux"
        ordering = ['ordre', 'created_at']

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.description}"

    def mark_completed(self, user=None):
        """Marque l'élément comme terminé"""
        self.is_completed = True
        self.completed_by = user
        self.date_completion = timezone.now()
        self.save()


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


class Tache(BaseModel):  # ✅ Modèle français pour maintenance
    """
    Tâches planifiées de maintenance (ménage, visites, maintenance préventive, etc.)
    """
    
    TYPE_TACHE_CHOICES = [
        ('menage', 'Ménage'),
        ('visite', 'Visite de contrôle'),
        ('maintenance_preventive', 'Maintenance préventive'),
        ('etat_lieux', 'État des lieux'),
        ('reparation', 'Réparation'),
        ('livraison', 'Livraison'),
        ('rendez_vous', 'Rendez-vous'),
        ('administrative', 'Tâche administrative'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('complete', 'Terminé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    RECURRENCE_CHOICES = [
        ('aucune', 'Aucune'),
        ('quotidien', 'Quotidienne'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuelle', 'Mensuelle'),
        ('trimestrielle', 'Trimestrielle'),
        ('annuelle', 'Annuelle'),
    ]
    
    # Identification
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de la tâche"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    # Relations vers la nouvelle structure
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taches_maintenance',  # ✅ DISTINCT des tâches d'employés
        verbose_name="Appartement concerné",
        help_text="Peut être null pour une tâche générale"
    )
    
    # Maintenir aussi l'ancien champ pour compatibilité
    bien = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='taches_maintenance_legacy',  # ✅ DISTINCT
        verbose_name="Bien concerné (Legacy)",
        help_text="Champ de compatibilité - sera supprimé après migration"
    )
    
    # ✅ CORRIGÉ: related_name distincts pour éviter les conflits
    assigne_a = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taches_maintenance_assignees',  # ✅ DISTINCT
        verbose_name="Assigné à",
        limit_choices_to={'user_type': 'employe'}  # 🆕 SIMPLIFIÉ (modèle déprécié)
    )
    
    cree_par = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='taches_maintenance_creees',  # ✅ DISTINCT
        verbose_name="Créé par"
    )
    
    # Caractéristiques
    type_tache = models.CharField(
        max_length=25,
        choices=TYPE_TACHE_CHOICES,
        verbose_name="Type de tâche"
    )
    
    priorite = models.CharField(
        max_length=10,
        choices=PRIORITE_CHOICES,
        default='normale',
        verbose_name="Priorité"
    )
    
    # Planification
    date_prevue = models.DateTimeField(
        verbose_name="Date prévue"
    )
    
    duree_estimee = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Durée estimée",
        help_text="Format: HH:MM:SS"
    )
    
    # Exécution
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
        max_length=15,
        choices=STATUT_CHOICES,
        default='planifie',
        verbose_name="Statut"
    )
    
    # Récurrence
    is_recurrente = models.BooleanField(
        default=False,
        verbose_name="Tâche récurrente"
    )
    
    recurrence_type = models.CharField(
        max_length=15,
        choices=RECURRENCE_CHOICES,
        default='aucune',
        verbose_name="Type de récurrence"
    )
    
    recurrence_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fin de récurrence"
    )
    
    # Suivi
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    temps_reel = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Temps réel passé"
    )
    
    class Meta:
        verbose_name = "Tâche de maintenance"
        verbose_name_plural = "Tâches de maintenance"
        ordering = ['date_prevue', '-priorite']
        indexes = [
            models.Index(fields=['appartement', 'statut']),
            models.Index(fields=['assigne_a', 'statut']),
            models.Index(fields=['type_tache', 'date_prevue']),
            models.Index(fields=['date_prevue']),
            models.Index(fields=['is_recurrente']),
        ]
    
    def __str__(self):
        lieu = f" - {self.appartement}" if self.appartement else (f" - {self.bien}" if self.bien else "")
        return f"{self.titre}{lieu}"
    
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
    def est_en_retard(self):
        """Vérifie si la tâche est en retard"""
        if self.statut in ['complete', 'annule']:
            return False
        
        return timezone.now() > self.date_prevue
    
    @property
    def duree_reelle(self):
        """Durée réelle de la tâche"""
        if self.date_debut and self.date_fin:
            return self.date_fin - self.date_debut
        return self.temps_reel
    
    def marquer_complete(self, commentaire=""):
        """Marque la tâche comme terminée"""
        self.statut = 'complete'
        if not self.date_fin:
            self.date_fin = timezone.now()
        
        if commentaire:
            self.commentaire = commentaire
        
        # Calculer le temps réel si début défini
        if self.date_debut:
            self.temps_reel = self.date_fin - self.date_debut
        
        self.save()
        
        # Créer la prochaine occurrence si récurrente
        if self.is_recurrente and self.recurrence_type != 'aucune':
            self.creer_prochaine_occurrence()
    
    def creer_prochaine_occurrence(self):
        """Crée la prochaine occurrence pour une tâche récurrente"""
        from datetime import timedelta
        
        if not self.is_recurrente or self.recurrence_type == 'aucune':
            return
        
        # Calculer la prochaine date
        if self.recurrence_type == 'quotidien':
            prochaine_date = self.date_prevue + timedelta(days=1)
        elif self.recurrence_type == 'hebdomadaire':
            prochaine_date = self.date_prevue + timedelta(weeks=1)
        elif self.recurrence_type == 'mensuelle':
            prochaine_date = self.date_prevue + timedelta(days=30)
        elif self.recurrence_type == 'trimestrielle':
            prochaine_date = self.date_prevue + timedelta(days=90)
        elif self.recurrence_type == 'annuelle':
            prochaine_date = self.date_prevue + timedelta(days=365)
        else:
            return
        
        # Vérifier si on n'a pas dépassé la date de fin
        if self.recurrence_fin and prochaine_date.date() > self.recurrence_fin:
            return
        
        # Créer la nouvelle tâche
        Tache.objects.create(
            titre=self.titre,
            description=self.description,
            appartement=self.appartement,
            bien=self.bien,
            assigne_a=self.assigne_a,
            cree_par=self.cree_par,
            type_tache=self.type_tache,
            priorite=self.priorite,
            date_prevue=prochaine_date,
            duree_estimee=self.duree_estimee,
            is_recurrente=self.is_recurrente,
            recurrence_type=self.recurrence_type,
            recurrence_fin=self.recurrence_fin,
        )


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