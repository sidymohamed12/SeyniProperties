"""
Modèles pour la gestion des tiers (clients, propriétaires, partenaires, etc.)
"""
from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.conf import settings
from apps.core.models import TimestampedModel
from apps.core.utils import generate_unique_reference


class Tiers(TimestampedModel):
    """
    Modèle représentant un tiers (client, propriétaire, prestataire, etc.)
    """

    TYPE_TIERS_CHOICES = [
        ('proprietaire', 'Propriétaire'),
        ('locataire', 'Locataire'),
        ('coproprietaire', 'Copropriétaire'),
        ('prestataire', 'Prestataire'),
        ('partenaire', 'Partenaire'),
        ('investisseur', 'Investisseur'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('en_attente', 'En attente'),
        ('archive', 'Archivé'),
    ]

    # Identification
    reference = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Référence",
        help_text="Référence unique du tiers (ex: TIER-2025-001234)",
        editable=False
    )

    # Informations personnelles
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom",
        help_text="Nom de famille ou raison sociale"
    )

    prenom = models.CharField(
        max_length=100,
        verbose_name="Prénom",
        blank=True,
        help_text="Prénom (pour les particuliers)"
    )

    type_tiers = models.CharField(
        max_length=20,
        choices=TYPE_TIERS_CHOICES,
        verbose_name="Type de tiers",
        db_index=True
    )

    # 🔑 Lien avec compte utilisateur (optionnel)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tiers_profile',
        verbose_name="Compte utilisateur",
        help_text="Compte utilisateur associé (si la personne a besoin d'accès au système)"
    )

    # Coordonnées
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
    )

    telephone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone principal"
    )

    telephone_secondaire = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name="Téléphone secondaire",
        help_text="Numéro de téléphone secondaire (optionnel)"
    )

    email = models.EmailField(
        validators=[EmailValidator()],
        verbose_name="Email",
        help_text="Adresse email"
    )

    adresse = models.TextField(
        verbose_name="Adresse",
        help_text="Adresse complète"
    )

    ville = models.CharField(
        max_length=100,
        default="Dakar",
        verbose_name="Ville"
    )

    quartier = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Quartier"
    )

    code_postal = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Code postal"
    )

    # Informations complémentaires
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='actif',
        verbose_name="Statut",
        db_index=True
    )

    date_ajout = models.DateField(
        auto_now_add=True,
        verbose_name="Date d'ajout"
    )

    # Pièces justificatives
    piece_identite = models.FileField(
        upload_to='tiers/pieces_identite/',
        blank=True,
        null=True,
        verbose_name="Pièce d'identité",
        help_text="CNI, Passeport, etc."
    )

    piece_identite_numero = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro pièce d'identité",
        help_text="Numéro de CNI, Passeport, etc."
    )

    autre_document = models.FileField(
        upload_to='tiers/documents/',
        blank=True,
        null=True,
        verbose_name="Autre document",
        help_text="Document complémentaire (optionnel)"
    )

    # ============================================
    # CHAMPS SPÉCIFIQUES LOCATAIRES
    # ============================================

    SITUATION_PROFESSIONNELLE_CHOICES = [
        ('salarie', 'Salarié'),
        ('independant', 'Indépendant'),
        ('etudiant', 'Étudiant'),
        ('retraite', 'Retraité'),
        ('chomeur', "Demandeur d'emploi"),
        ('autre', 'Autre'),
    ]

    date_entree = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'entrée",
        help_text="Date d'entrée dans le logement (pour les locataires)"
    )

    situation_pro = models.CharField(
        max_length=20,
        choices=SITUATION_PROFESSIONNELLE_CHOICES,
        blank=True,
        verbose_name="Situation professionnelle",
        help_text="Pour les locataires"
    )

    garant_nom = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom du garant",
        help_text="Pour les locataires"
    )

    garant_tel = models.CharField(
        max_length=17,
        blank=True,
        verbose_name="Téléphone du garant",
        help_text="Pour les locataires"
    )

    # ============================================
    # CHAMPS SPÉCIFIQUES BAILLEURS/PROPRIÉTAIRES
    # ============================================

    TYPE_BAILLEUR_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
        ('sci', 'SCI'),
        ('autre', 'Autre'),
    ]

    type_bailleur = models.CharField(
        max_length=20,
        choices=TYPE_BAILLEUR_CHOICES,
        blank=True,
        default='particulier',
        verbose_name="Type de bailleur",
        help_text="Pour les propriétaires/bailleurs"
    )

    entreprise = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nom de l'entreprise",
        help_text="Si bailleur entreprise"
    )

    numero_siret = models.CharField(
        max_length=14,
        blank=True,
        verbose_name="Numéro SIRET",
        help_text="Pour les entreprises"
    )

    adresse_fiscale = models.TextField(
        blank=True,
        verbose_name="Adresse fiscale",
        help_text="Adresse pour les documents fiscaux (si différente de l'adresse principale)"
    )

    # Notes et observations
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Notes et observations sur le tiers"
    )

    # ============================================
    # GESTION DU COMPTE UTILISATEUR
    # ============================================

    mot_de_passe_temporaire = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mot de passe temporaire",
        help_text="Mot de passe temporaire généré lors de la création du compte (sera effacé après première connexion)"
    )

    date_creation_compte = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de création du compte",
        help_text="Date de création du compte utilisateur associé"
    )

    compte_active = models.BooleanField(
        default=False,
        verbose_name="Compte activé",
        help_text="Indique si le compte utilisateur a été activé par le tiers"
    )

    # Gestion
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tiers_crees',
        verbose_name="Créé par"
    )

    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tiers_modifies',
        verbose_name="Modifié par"
    )

    class Meta:
        verbose_name = "Tiers"
        verbose_name_plural = "Tiers"
        ordering = ['-date_ajout', 'nom']
        indexes = [
            models.Index(fields=['type_tiers', 'statut']),
            models.Index(fields=['nom', 'prenom']),
            models.Index(fields=['-date_ajout']),
        ]

    def __str__(self):
        if self.prenom:
            return f"{self.nom} {self.prenom} ({self.get_type_tiers_display()})"
        return f"{self.nom} ({self.get_type_tiers_display()})"

    def save(self, *args, **kwargs):
        # Générer automatiquement la référence si elle n'existe pas
        if not self.reference:
            self.reference = generate_unique_reference(prefix='TIER', length=6)
        super().save(*args, **kwargs)

    @property
    def nom_complet(self):
        """Retourne le nom complet du tiers"""
        if self.entreprise and self.type_bailleur != 'particulier':
            return self.entreprise
        if self.prenom:
            return f"{self.nom} {self.prenom}"
        return self.nom

    @property
    def biens_lies_count(self):
        """Retourne le nombre de biens liés à ce tiers"""
        return self.biens_lies.count()

    @property
    def has_user_account(self):
        """Vérifie si le tiers a un compte utilisateur associé"""
        return self.user is not None

    @property
    def is_proprietaire(self):
        """Vérifie si le tiers est un propriétaire"""
        return self.type_tiers == 'proprietaire'

    @property
    def is_locataire(self):
        """Vérifie si le tiers est un locataire"""
        return self.type_tiers == 'locataire'

    @property
    def is_prestataire(self):
        """Vérifie si le tiers est un prestataire"""
        return self.type_tiers == 'prestataire'

    def get_display_name(self):
        """Retourne le nom d'affichage approprié selon le type"""
        if self.entreprise and self.type_bailleur != 'particulier':
            return f"{self.entreprise} (Entreprise)"
        return self.nom_complet

    def generer_mot_de_passe_temporaire(self):
        """Génère un mot de passe temporaire aléatoire"""
        import random
        import string
        # Format: 3 lettres majuscules + 4 chiffres + 3 lettres minuscules
        # Exemple: ABC1234xyz
        uppercase = ''.join(random.choices(string.ascii_uppercase, k=3))
        digits = ''.join(random.choices(string.digits, k=4))
        lowercase = ''.join(random.choices(string.ascii_lowercase, k=3))
        return f"{uppercase}{digits}{lowercase}"

    def get_identifiants_connexion(self):
        """Retourne les identifiants de connexion si un compte existe"""
        if self.user:
            return {
                'username': self.user.username,
                'email': self.user.email,
                'mot_de_passe_temporaire': self.mot_de_passe_temporaire,
                'compte_active': self.compte_active,
                'date_creation': self.date_creation_compte
            }
        return None


class TiersBien(TimestampedModel):
    """
    Modèle représentant la liaison entre un tiers et un bien immobilier
    avec le type de contrat associé
    """

    TYPE_CONTRAT_CHOICES = [
        ('location', 'Location'),
        ('vente', 'Vente'),
        ('gestion', 'Gestion'),
    ]

    TYPE_MANDAT_CHOICES = [
        ('exclusif', 'Mandat exclusif'),
        ('non_exclusif', 'Mandat non exclusif'),
        ('sans_mandat', 'Sans mandat'),
    ]

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
        ('annule', 'Annulé'),
    ]

    # Relations
    tiers = models.ForeignKey(
        Tiers,
        on_delete=models.CASCADE,
        related_name='biens_lies',
        verbose_name="Tiers"
    )

    # Lien avec appartement (nouveau modèle)
    appartement = models.ForeignKey(
        'properties.Appartement',
        on_delete=models.CASCADE,
        related_name='tiers_lies',
        null=True,
        blank=True,
        verbose_name="Appartement"
    )

    # Lien avec résidence (si liaison directe à une résidence)
    residence = models.ForeignKey(
        'properties.Residence',
        on_delete=models.CASCADE,
        related_name='tiers_lies',
        null=True,
        blank=True,
        verbose_name="Résidence"
    )

    # Type de contrat
    type_contrat = models.CharField(
        max_length=20,
        choices=TYPE_CONTRAT_CHOICES,
        verbose_name="Type de contrat",
        db_index=True
    )

    type_mandat = models.CharField(
        max_length=20,
        choices=TYPE_MANDAT_CHOICES,
        default='sans_mandat',
        verbose_name="Type de mandat"
    )

    # Dates
    date_debut = models.DateField(
        verbose_name="Date de début",
        help_text="Date de début de la relation contractuelle"
    )

    date_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin",
        help_text="Date de fin prévue ou effective (optionnel)"
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_cours',
        verbose_name="Statut",
        db_index=True
    )

    # Informations contractuelles
    montant_commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant de la commission (FCFA)",
        help_text="Commission prévue pour cette relation"
    )

    pourcentage_commission = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Pourcentage de commission (%)",
        help_text="Pourcentage de commission (si applicable)"
    )

    # Documents
    contrat_signe = models.FileField(
        upload_to='tiers/contrats/',
        blank=True,
        null=True,
        verbose_name="Contrat signé",
        help_text="Document du contrat signé"
    )

    mandat_document = models.FileField(
        upload_to='tiers/mandats/',
        blank=True,
        null=True,
        verbose_name="Document de mandat",
        help_text="Document de mandat (si applicable)"
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Notes et observations sur cette relation"
    )

    # Gestion
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tiers_biens_crees',
        verbose_name="Créé par"
    )

    class Meta:
        verbose_name = "Liaison Tiers-Bien"
        verbose_name_plural = "Liaisons Tiers-Biens"
        ordering = ['-date_debut']
        unique_together = [
            ('tiers', 'appartement', 'type_contrat'),
        ]
        indexes = [
            models.Index(fields=['type_contrat', 'statut']),
            models.Index(fields=['-date_debut']),
        ]

    def __str__(self):
        bien = self.appartement or self.residence
        return f"{self.tiers.nom_complet} - {bien} ({self.get_type_contrat_display()})"

    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError

        # S'assurer qu'au moins un bien est lié (appartement ou résidence)
        if not self.appartement and not self.residence:
            raise ValidationError(
                "Vous devez lier au moins un bien (appartement ou résidence)"
            )

        # Vérifier que date_fin est après date_debut
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError(
                "La date de fin ne peut pas être antérieure à la date de début"
            )

    @property
    def bien_lie(self):
        """Retourne le bien lié (appartement ou résidence)"""
        return self.appartement or self.residence

    @property
    def duree_jours(self):
        """Retourne la durée en jours de la relation"""
        from django.utils import timezone
        if self.date_fin:
            return (self.date_fin - self.date_debut).days
        else:
            return (timezone.now().date() - self.date_debut).days


class FicheRenseignement(TimestampedModel):
    """
    Fiche de renseignement client pour location
    """

    TYPE_BIEN_CHOICES = [
        ('appartement', 'Appartement'),
        ('villa', 'Villa'),
        ('appartement_meuble', 'Appartement meublé'),
        ('hangar', 'Hangar'),
    ]

    # Référence unique
    numero_fiche = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de fiche",
        help_text="Généré automatiquement (ex: FICHE-2025-001)"
    )

    # Lien avec le tiers locataire (si déjà créé)
    locataire = models.ForeignKey(
        'tiers.Tiers',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fiches_renseignement',
        verbose_name="Locataire",
        limit_choices_to={'type_tiers': 'locataire'}
    )

    # === SECTION 1: Informations Client ===
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom"
    )

    prenom = models.CharField(
        max_length=100,
        verbose_name="Prénom"
    )

    adresse = models.TextField(
        verbose_name="Adresse"
    )

    telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone"
    )

    email = models.EmailField(
        verbose_name="Email"
    )

    employeur = models.CharField(
        max_length=200,
        verbose_name="Employeur",
        blank=True
    )

    # === SECTION 2: Type de bien recherché ===
    type_bien = models.CharField(
        max_length=30,
        choices=TYPE_BIEN_CHOICES,
        verbose_name="Type de bien"
    )

    # === SECTION 3: Adresse du bien ===
    adresse_bien = models.TextField(
        verbose_name="Adresse du bien",
        blank=True
    )

    # === SECTION 4: Nombre de pièces ===
    nombre_pieces = models.CharField(
        max_length=100,
        verbose_name="Nombre de pièces",
        blank=True
    )

    # === SECTION 5: Documents fournis ===
    bulletins_salaire_fournis = models.BooleanField(
        default=False,
        verbose_name="3 derniers bulletins de salaire"
    )

    piece_identite_fournie = models.BooleanField(
        default=False,
        verbose_name="Copie de la pièce d'identité"
    )

    fiche_signee = models.BooleanField(
        default=False,
        verbose_name="Fiche de renseignement signée"
    )

    # === SECTION 6: Garant ===
    garant_nom = models.CharField(
        max_length=100,
        verbose_name="Nom du garant",
        blank=True
    )

    garant_prenom = models.CharField(
        max_length=100,
        verbose_name="Prénom du garant",
        blank=True
    )

    garant_adresse = models.TextField(
        verbose_name="Adresse du garant",
        blank=True
    )

    garant_telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone du garant",
        blank=True
    )

    garant_employeur = models.CharField(
        max_length=200,
        verbose_name="Employeur du garant",
        blank=True
    )

    # === SECTION 7: Modalités de paiement ===
    evaluation_bien = models.TextField(
        verbose_name="Évaluation du bien",
        blank=True
    )

    montant_caution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant de la caution",
        null=True,
        blank=True
    )

    montant_loyer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant du loyer",
        null=True,
        blank=True
    )

    montant_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Commission d'agence",
        null=True,
        blank=True
    )

    # === SECTION 8: Ancien bailleur ===
    ancien_bailleur = models.CharField(
        max_length=200,
        verbose_name="Ancien bailleur",
        blank=True
    )

    ancien_bailleur_telephone = models.CharField(
        max_length=20,
        verbose_name="Téléphone ancien bailleur",
        blank=True
    )

    # === Métadonnées ===
    date_creation = models.DateField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    date_signature = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de signature"
    )

    # Fichier PDF généré
    fichier_pdf = models.FileField(
        upload_to='fiches_renseignement/',
        verbose_name="Fichier PDF",
        blank=True,
        null=True
    )

    # Signature client (image uploadée)
    signature_client = models.ImageField(
        upload_to='signatures/clients/',
        verbose_name="Signature du client",
        blank=True,
        null=True
    )

    # Signature entreprise (image uploadée)
    signature_entreprise = models.ImageField(
        upload_to='signatures/entreprise/',
        verbose_name="Signature de l'entreprise",
        blank=True,
        null=True
    )

    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('brouillon', 'Brouillon'),
            ('en_attente', 'En attente de signature'),
            ('signee', 'Signée'),
            ('validee', 'Validée'),
        ],
        default='brouillon',
        verbose_name="Statut"
    )

    # Créé par
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fiches_creees',
        verbose_name="Créé par"
    )

    class Meta:
        verbose_name = "Fiche de renseignement"
        verbose_name_plural = "Fiches de renseignement"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.numero_fiche} - {self.nom} {self.prenom}"

    def save(self, *args, **kwargs):
        # Générer le numéro de fiche si nouveau
        if not self.numero_fiche:
            from django.utils import timezone
            year = timezone.now().year
            last_fiche = FicheRenseignement.objects.filter(
                numero_fiche__startswith=f'FICHE-{year}-'
            ).order_by('-numero_fiche').first()

            if last_fiche:
                last_number = int(last_fiche.numero_fiche.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.numero_fiche = f'FICHE-{year}-{new_number:03d}'

        super().save(*args, **kwargs)

    @property
    def nom_complet(self):
        """Retourne le nom complet du client"""
        return f"{self.prenom} {self.nom}"

    @property
    def garant_nom_complet(self):
        """Retourne le nom complet du garant"""
        if self.garant_nom and self.garant_prenom:
            return f"{self.garant_prenom} {self.garant_nom}"
        return ""

    @property
    def documents_complets(self):
        """Vérifie si tous les documents sont fournis"""
        return (
            self.bulletins_salaire_fournis and
            self.piece_identite_fournie and
            self.fiche_signee
        )
