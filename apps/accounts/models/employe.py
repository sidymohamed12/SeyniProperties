from django.db import models

from apps.accounts.models.custom_user import CustomUser

class Employe(models.Model):
    """Profil spécialisé pour les employés"""

    SPECIALITES = [
        ('menage', 'Ménage'),
        ('plomberie', 'Plomberie'),
        ('electricite', 'Électricité'),
        ('peinture', 'Peinture'),
        ('jardinage', 'Jardinage'),
        ('securite', 'Sécurité'),
        ('maintenance', 'Maintenance générale'),
        ('commercial', 'Commercial'),
        ('administratif', 'Administratif'),
    ]

    STATUTS = [
        ('actif', 'Actif'),
        ('conge', 'En congé'),
        ('arret', 'Arrêt maladie'),
        ('suspendu', 'Suspendu'),
        ('demission', 'Démissionné'),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Utilisateur"
    )
    specialite = models.CharField(
        max_length=20,
        choices=SPECIALITES,
        verbose_name="Spécialité"
    )
    date_embauche = models.DateField(
        verbose_name="Date d'embauche"
    )
    salaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Salaire mensuel",
        help_text="En FCFA"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default='actif',
        verbose_name="Statut"
    )

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"

    def __str__(self):
        return f"Employé: {self.user.get_full_name() or self.user.username} ({self.get_specialite_display()})"
