"""
Signaux pour l'application properties
Gère la création automatique des TiersBien lors de la création/modification de propriétés
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.properties.models import Residence, Appartement


@receiver(post_save, sender=Residence)
def create_tiers_bien_for_residence(sender, instance, created, **kwargs):
    """
    Crée automatiquement un TiersBien quand une résidence est créée
    pour lier le propriétaire à la résidence
    """
    from apps.tiers.models import TiersBien

    if created and instance.proprietaire:
        # Vérifier si un TiersBien existe déjà pour cette relation
        existe_deja = TiersBien.objects.filter(
            tiers=instance.proprietaire,
            residence=instance,
            type_contrat='gestion'
        ).exists()

        if not existe_deja:
            TiersBien.objects.create(
                tiers=instance.proprietaire,
                residence=instance,
                type_contrat='gestion',
                type_mandat='sans_mandat',
                date_debut=instance.created_at.date() if instance.created_at else timezone.now().date(),
                statut='en_cours',
                notes=f"Créé automatiquement lors de la création de la résidence {instance.nom}"
            )
            print(f"✓ TiersBien créé automatiquement: {instance.proprietaire.nom_complet} ↔ {instance.nom}")

    # Si le propriétaire change (modification)
    elif not created and instance.proprietaire:
        # Récupérer l'ancien TiersBien si existant
        ancien_tiers_bien = TiersBien.objects.filter(
            residence=instance,
            type_contrat='gestion',
            statut='en_cours'
        ).exclude(tiers=instance.proprietaire).first()

        if ancien_tiers_bien:
            # Terminer l'ancien lien
            ancien_tiers_bien.statut = 'termine'
            ancien_tiers_bien.date_fin = timezone.now().date()
            ancien_tiers_bien.save()
            print(f"✓ Ancien TiersBien terminé: {ancien_tiers_bien.tiers.nom_complet}")

        # Créer le nouveau lien si nécessaire
        nouveau_existe = TiersBien.objects.filter(
            tiers=instance.proprietaire,
            residence=instance,
            type_contrat='gestion',
            statut='en_cours'
        ).exists()

        if not nouveau_existe:
            TiersBien.objects.create(
                tiers=instance.proprietaire,
                residence=instance,
                type_contrat='gestion',
                type_mandat='sans_mandat',
                date_debut=timezone.now().date(),
                statut='en_cours',
                notes=f"Créé automatiquement lors du changement de propriétaire de {instance.nom}"
            )
            print(f"✓ Nouveau TiersBien créé: {instance.proprietaire.nom_complet} ↔ {instance.nom}")
