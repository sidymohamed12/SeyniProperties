from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé pour Seyni Properties"""

    USER_TYPES = [
        ('manager', 'Manager'),
        ('accountant', 'Comptable'),
        ('employe', 'Employé'),  # 🆕 UNIFIÉ: Remplace field_agent et technician
        ('tenant', 'Locataire'),
        ('landlord', 'Bailleur'),
    ]

    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('other', 'Autre'),
    ]

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='tenant',
        verbose_name="Type d'utilisateur"
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="Genre"
    )

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name="Téléphone"
    )

    address = models.TextField(blank=True, verbose_name="Adresse")
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )

    # Champ pour forcer le changement de mot de passe à la première connexion
    mot_de_passe_temporaire = models.BooleanField(
        default=False,
        verbose_name="Mot de passe temporaire",
        help_text="Si True, l'utilisateur devra changer son mot de passe à la prochaine connexion"
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

