# apps/maintenance/models_unified.py
"""
Modèles unifiés pour la gestion des travaux et demandes d'achat
Remplace Intervention et Tache par un modèle Travail unifié
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from apps.core.models import BaseModel
from apps.core.utils import generate_unique_reference

User = get_user_model()


class Travail(BaseModel):
    """
    Modèle unifié pour tous les travaux: interventions réactives, tâches planifiées, maintenance préventive
    Remplace les modèles Intervention et Tache
    """

    # ========== CHOIX ==========
    NATURE_CHOICES = [
        ('reactif', 'Réactif (intervention urgente)'),
        ('planifie', 'Planifié (tâche programmée)'),
        ('preventif', 'Préventif (maintenance)'),
        ('projet', 'Projet (travaux importants)'),
    ]

    TYPE_TRAVAIL_CHOICES = [
        # Techniques
        ('plomberie', 'Plomberie'),
        ('electricite', 'Électricité'),
        ('climatisation', 'Climatisation'),
        ('serrurerie', 'Serrurerie'),
        ('peinture', 'Peinture'),
        ('menuiserie', 'Menuiserie'),
        ('reparation_generale', 'Réparation générale'),

        # Entretien
        ('menage', 'Ménage'),
        ('jardinage', 'Jardinage'),
        ('nettoyage', 'Nettoyage'),

        # Administratif
        ('visite_controle', 'Visite de contrôle'),
        ('etat_lieux', 'État des lieux'),
        ('livraison', 'Livraison'),
        ('rendez_vous', 'Rendez-vous'),

        # Sécurité
        ('securite', 'Sécurité'),

        # Autres
        ('autre', 'Autre'),
    ]

    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]

    STATUT_CHOICES = [
        ('signale', 'Signalé'),
        ('planifie', 'Planifié'),
        ('assigne', 'Assigné'),
        ('en_attente_materiel', 'En attente matériel'),
        ('en_cours', 'En cours'),
        ('en_pause', 'En pause'),
        ('complete', 'Terminé'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
        ('reporte', 'Reporté'),
    ]

    RECURRENCE_CHOICES = [
        ('aucune', 'Aucune'),
        ('quotidien', 'Quotidien'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
    ]

    # ========== IDENTIFICATION ==========
    numero_travail = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de travail",
        help_text="Généré automatiquement: TRAV-2025-001"
    )

    titre = models.CharField(
        max_length=200,
        verbose_name="Titre"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    # ========== NATURE DU TRAVAIL ==========
    nature = models.CharField(
        max_length=20,
        choices=NATURE_CHOICES,
        default='reactif',
        verbose_name="Nature du travail"
    )

    type_travail = models.CharField(
        max_length=30,
        choices=TYPE_TRAVAIL_CHOICES,
        verbose_name="Type de travail"
    )

    priorite = models.CharField(
        max_length=15,
        choices=PRIORITE_CHOICES,
        default='normale',
        verbose_name="Priorité"
    )

    # ========== RELATIONS ==========
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='travaux',
        verbose_name="Appartement concerné",
        help_text="Null pour tâches générales (ex: livraison au bureau)"
    )

    residence = models.ForeignKey(
        'properties.Residence',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='travaux_residence',
        verbose_name="Résidence concernée",
        help_text="Pour travaux sur parties communes"
    )

    # ========== PERSONNES ==========
    signale_par = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travaux_signales',
        verbose_name="Signalé par",
        help_text="Locataire qui a signalé (pour réactif)"
    )

    assigne_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travaux_assignes',
        verbose_name="Assigné à",
        help_text="Employé responsable"
    )

    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='travaux_crees',
        verbose_name="Créé par"
    )

    # ========== STATUT & WORKFLOW ==========
    statut = models.CharField(
        max_length=25,
        choices=STATUT_CHOICES,
        default='signale',
        verbose_name="Statut"
    )

    # ========== DATES ==========
    date_signalement = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de signalement"
    )

    date_prevue = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date prévue",
        help_text="Pour travaux planifiés"
    )

    date_assignation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'assignation"
    )

    date_debut = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début effectif"
    )

    date_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin"
    )

    duree_estimee = models.DurationField(
        null=True,
        blank=True,
        verbose_name="Durée estimée",
        help_text="Format: HH:MM:SS"
    )

    # ========== RÉCURRENCE (pour planifiés) ==========
    is_recurrent = models.BooleanField(
        default=False,
        verbose_name="Travail récurrent"
    )

    recurrence = models.CharField(
        max_length=15,
        choices=RECURRENCE_CHOICES,
        default='aucune',
        verbose_name="Fréquence de récurrence"
    )

    recurrence_jour_semaine = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="Jour de la semaine (0=Lundi)",
        help_text="Pour récurrence hebdomadaire"
    )

    prochaine_occurrence = models.DateField(
        null=True,
        blank=True,
        verbose_name="Prochaine occurrence"
    )

    tache_parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='occurrences',
        verbose_name="Tâche récurrente parent"
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

    # ========== DEMANDE D'ACHAT LIÉE ==========
    demande_achat = models.ForeignKey(
        'payments.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='travaux_lies',
        limit_choices_to={'type_facture': 'demande_achat'},
        verbose_name="Demande d'achat liée"
    )

    # ========== RETOURS ==========
    commentaire_employe = models.TextField(
        blank=True,
        verbose_name="Commentaire de l'employé"
    )

    satisfaction_client = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfaction client (1-5)"
    )

    notes_internes = models.TextField(
        blank=True,
        verbose_name="Notes internes (visibles managers uniquement)"
    )

    # ========== MÉTHODES ==========
    def save(self, *args, **kwargs):
        # Générer le numéro si nouveau
        if not self.numero_travail:
            self.numero_travail = generate_unique_reference('TRAV')

        # Si assigné pour la première fois
        if self.assigne_a and not self.date_assignation:
            self.date_assignation = timezone.now()
            if self.statut == 'signale':
                self.statut = 'assigne'

        super().save(*args, **kwargs)

    def marquer_en_cours(self):
        """Démarre le travail"""
        if not self.date_debut:
            self.date_debut = timezone.now()
        self.statut = 'en_cours'
        self.save()

    def marquer_complete(self, cout_reel=None, commentaire=None):
        """Termine le travail"""
        self.date_fin = timezone.now()
        self.statut = 'complete'

        if cout_reel:
            self.cout_reel = cout_reel

        if commentaire:
            self.commentaire_employe = commentaire

        self.save()

        # Générer prochaine occurrence si récurrent
        if self.is_recurrent and self.recurrence != 'aucune':
            self.generer_prochaine_occurrence()

    def generer_prochaine_occurrence(self):
        """Génère la prochaine occurrence pour une tâche récurrente"""
        if not self.is_recurrent or self.recurrence == 'aucune':
            return None

        # Calculer la prochaine date
        base_date = self.date_prevue or timezone.now()

        if self.recurrence == 'quotidien':
            prochaine_date = base_date + timedelta(days=1)
        elif self.recurrence == 'hebdomadaire':
            prochaine_date = base_date + timedelta(weeks=1)
        elif self.recurrence == 'mensuel':
            prochaine_date = base_date + timedelta(days=30)
        elif self.recurrence == 'trimestriel':
            prochaine_date = base_date + timedelta(days=90)
        elif self.recurrence == 'annuel':
            prochaine_date = base_date + timedelta(days=365)
        else:
            return None

        # Créer la nouvelle occurrence
        nouvelle_occurrence = Travail.objects.create(
            titre=self.titre,
            description=self.description,
            nature=self.nature,
            type_travail=self.type_travail,
            priorite=self.priorite,
            appartement=self.appartement,
            residence=self.residence,
            assigne_a=self.assigne_a,
            cree_par=self.cree_par,
            statut='planifie',
            date_prevue=prochaine_date,
            duree_estimee=self.duree_estimee,
            is_recurrent=True,
            recurrence=self.recurrence,
            recurrence_jour_semaine=self.recurrence_jour_semaine,
            tache_parent=self.tache_parent or self,
            cout_estime=self.cout_estime,
            notes_internes=self.notes_internes,
        )

        # Mettre à jour la prochaine occurrence de la tâche parent
        parent = self.tache_parent or self
        parent.prochaine_occurrence = prochaine_date.date()
        parent.save(update_fields=['prochaine_occurrence'])

        return nouvelle_occurrence

    def creer_demande_achat(self, demandeur, articles, motif):
        """
        Crée une demande d'achat liée à ce travail

        Args:
            demandeur: User qui fait la demande
            articles: Liste de dicts avec {designation, quantite, unite, fournisseur, prix_unitaire, motif}
            motif: Motif général de la demande

        Returns:
            Invoice (demande d'achat créée)
        """
        from apps.payments.models.invoice import Invoice
        from apps.payments.models.ligne_demade_achat import LigneDemandeAchat

        # Calculer le montant total
        montant_total = sum(
            Decimal(str(article['quantite'])) * Decimal(str(article['prix_unitaire']))
            for article in articles
        )

        # Créer la demande d'achat
        demande = Invoice.objects.create(
            type_facture='demande_achat',
            demandeur=demandeur,
            service_fonction="Maintenance",
            description=motif,
            motif_principal=f"Travail {self.numero_travail} - {self.titre}",
            montant_ht=montant_total,
            taux_tva=Decimal('0.00'),  # Pas de TVA pour achats internes
            montant_ttc=montant_total,
            date_emission=timezone.now().date(),
            date_echeance=timezone.now().date() + timedelta(days=7),
            etape_workflow='brouillon',
            statut='brouillon',
        )

        # Créer les lignes d'articles
        for article in articles:
            prix_total = Decimal(str(article['quantite'])) * Decimal(str(article['prix_unitaire']))

            LigneDemandeAchat.objects.create(
                demande=demande,
                designation=article['designation'],
                quantite=Decimal(str(article['quantite'])),
                unite=article.get('unite', 'unité'),
                fournisseur=article.get('fournisseur', ''),
                prix_unitaire=Decimal(str(article['prix_unitaire'])),
                prix_total=prix_total,
                motif=article.get('motif', motif)
            )

        # Lier la demande au travail et mettre en attente matériel
        self.demande_achat = demande
        self.statut = 'en_attente_materiel'
        self.save()

        return demande

    @property
    def duree_reelle(self):
        """Calcule la durée réelle du travail si terminé"""
        if self.date_debut and self.date_fin:
            return self.date_fin - self.date_debut
        return None

    @property
    def est_en_retard(self):
        """Vérifie si le travail est en retard"""
        if self.date_prevue and self.statut not in ['complete', 'valide', 'annule']:
            return timezone.now() > self.date_prevue
        return False

    @property
    def bien_concerne(self):
        """Retourne le bien concerné (appartement ou résidence)"""
        return self.appartement or self.residence

    def __str__(self):
        return f"{self.numero_travail} - {self.titre}"

    class Meta:
        verbose_name = "Travail"
        verbose_name_plural = "Travaux"
        ordering = ['-date_signalement']
        indexes = [
            models.Index(fields=['statut', 'priorite']),
            models.Index(fields=['assigne_a', 'statut']),
            models.Index(fields=['date_prevue']),
            models.Index(fields=['nature', 'type_travail']),
        ]


class TravailMedia(BaseModel):
    """
    Médias liés à un travail (photos, factures, devis, rapports)
    Remplace InterventionMedia
    """

    TYPE_MEDIA_CHOICES = [
        ('photo_avant', 'Photo avant travaux'),
        ('photo_apres', 'Photo après travaux'),
        ('photo_probleme', 'Photo du problème'),
        ('facture', 'Facture'),
        ('devis', 'Devis'),
        ('rapport', 'Rapport'),
        ('autre', 'Autre document'),
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

    titre = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Titre"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    ajoute_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medias_travaux_ajoutes',
        verbose_name="Ajouté par"
    )

    date_ajout = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )

    def __str__(self):
        return f"{self.get_type_media_display()} - {self.travail.numero_travail}"

    class Meta:
        verbose_name = "Média de travail"
        verbose_name_plural = "Médias de travaux"
        ordering = ['-date_ajout']


class TravailChecklist(BaseModel):
    """
    Checklist d'items à vérifier pour un travail
    Remplace InterventionChecklistItem
    """

    travail = models.ForeignKey(
        Travail,
        on_delete=models.CASCADE,
        related_name='checklist_items',
        verbose_name="Travail"
    )

    description = models.CharField(
        max_length=255,
        verbose_name="Description"
    )

    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre"
    )

    est_complete = models.BooleanField(
        default=False,
        verbose_name="Complété"
    )

    complete_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checklist_items_completes',
        verbose_name="Complété par"
    )

    date_completion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de complétion"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )

    def marquer_complete(self, user):
        """Marque l'item comme complété"""
        self.est_complete = True
        self.complete_par = user
        self.date_completion = timezone.now()
        self.save()

    def __str__(self):
        status = "✓" if self.est_complete else "○"
        return f"{status} {self.description}"

    class Meta:
        verbose_name = "Item de checklist"
        verbose_name_plural = "Items de checklist"
        ordering = ['ordre', 'id']
