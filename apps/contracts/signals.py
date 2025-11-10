# apps/contracts/signals.py
"""
Signals pour le module contracts
Automatisation des workflows et actions
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import RentalContract, ContractWorkflow, DocumentContrat
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNALS RENTAL CONTRACT
# ============================================================================

@receiver(post_save, sender=RentalContract)
def create_contract_workflow(sender, instance, created, **kwargs):
    """
    Cr�e automatiquement un workflow PMO lors de la cr�ation d'un contrat en brouillon
    """
    if created and instance.statut == 'brouillon':
        # Cr�er le workflow PMO
        workflow, workflow_created = ContractWorkflow.objects.get_or_create(
            contrat=instance,
            defaults={
                'etape_actuelle': 'verification_dossier',
                'statut_dossier': 'en_cours',
                'responsable_pmo': instance.cree_par if instance.cree_par else None
            }
        )

        if workflow_created:
            logger.info(f"Workflow PMO cr�� automatiquement pour le contrat {instance.numero_contrat}")

            # Cr�er les documents obligatoires par d�faut
            documents_requis = [
                ('piece_identite', True),
            ]

            # Ajouter les documents selon le type de contrat
            if instance.type_contrat_usage == 'professionnel':
                # Contrats professionnels : NINEA et RCCM uniquement (pas de RIB ni justificatif de revenu)
                documents_requis.extend([
                    ('ninea', True),
                    ('rccm', True),
                ])
                logger.info(f"Documents professionnels (NINEA, RCCM) ajoutés pour contrat à usage professionnel")
            else:
                # Contrats d'habitation : justificatif de revenus et RIB
                documents_requis.extend([
                    ('justificatif_revenus', True),
                    ('rib', True),
                ])
                logger.info(f"Documents d'habitation (justificatif revenus, RIB) ajoutés pour contrat d'habitation")

            for type_doc, obligatoire in documents_requis:
                DocumentContrat.objects.create(
                    workflow=workflow,
                    type_document=type_doc,
                    obligatoire=obligatoire,
                    statut='attendu'
                )

            logger.info(f"{len(documents_requis)} documents requis cr��s pour le workflow")


@receiver(post_save, sender=RentalContract)
def update_appartement_status(sender, instance, created, **kwargs):
    """
    Met � jour le statut de l'appartement selon le statut du contrat
    """
    if not created:
        appartement = instance.appartement

        if instance.statut == 'actif':
            if appartement.statut_occupation != 'occupe':
                appartement.statut_occupation = 'occupe'
                appartement.save(update_fields=['statut_occupation'])
                logger.info(f"Appartement {appartement.nom} marqu� comme occup�")

        elif instance.statut in ['resilie', 'expire']:
            if appartement.statut_occupation == 'occupe':
                # V�rifier qu'il n'y a pas d'autre contrat actif sur cet appartement
                autres_contrats_actifs = RentalContract.objects.filter(
                    appartement=appartement,
                    statut='actif'
                ).exclude(pk=instance.pk).exists()

                if not autres_contrats_actifs:
                    appartement.statut_occupation = 'libre'
                    appartement.save(update_fields=['statut_occupation'])
                    logger.info(f"Appartement {appartement.nom} marqu� comme libre")


@receiver(post_save, sender=RentalContract)
def create_tiers_bien_for_contract(sender, instance, created, **kwargs):
    """
    Cr�e automatiquement un TiersBien quand un contrat devient actif
    pour lier le locataire � l'appartement
    """
    from apps.tiers.models import TiersBien

    # Cr�er le TiersBien uniquement quand le contrat devient actif
    if instance.statut == 'actif' and instance.locataire and instance.appartement:
        # V�rifier si un TiersBien existe d�j� pour cette relation
        existe_deja = TiersBien.objects.filter(
            tiers=instance.locataire,
            appartement=instance.appartement,
            type_contrat='location'
        ).exists()

        if not existe_deja:
            TiersBien.objects.create(
                tiers=instance.locataire,
                appartement=instance.appartement,
                type_contrat='location',
                type_mandat='sans_mandat',
                date_debut=instance.date_debut,
                date_fin=instance.date_fin,
                statut='en_cours',
                notes=f"Cr�� automatiquement lors de l'activation du contrat {instance.numero_contrat}"
            )
            logger.info(f"TiersBien cr�� automatiquement: {instance.locataire.nom_complet} � {instance.appartement.nom}")

    # Mettre � jour ou terminer le TiersBien si le contrat est r�sili� ou expir�
    elif instance.statut in ['resilie', 'expire']:
        tiers_bien = TiersBien.objects.filter(
            tiers=instance.locataire,
            appartement=instance.appartement,
            type_contrat='location',
            statut='en_cours'
        ).first()

        if tiers_bien:
            tiers_bien.statut = 'termine'
            tiers_bien.date_fin = timezone.now().date()
            tiers_bien.save()
            logger.info(f"TiersBien termin� pour {instance.locataire.nom_complet} � {instance.appartement.nom}")


@receiver(post_save, sender=RentalContract)
def notify_contract_expiration(sender, instance, created, **kwargs):
    """
    Envoie une notification si le contrat expire dans moins de 30 jours
    """
    if not created and instance.statut == 'actif':
        jours_restants = instance.jours_restants

        if jours_restants is not None and 0 < jours_restants <= 30:
            # TODO: Envoyer notification email/SMS
            logger.warning(
                f"Contrat {instance.numero_contrat} expire dans {jours_restants} jours"
            )

            # Si configur�, envoyer un email
            if settings.EMAIL_HOST:
                try:
                    send_mail(
                        subject=f'Expiration prochaine du contrat {instance.numero_contrat}',
                        message=f'Le contrat expire dans {jours_restants} jours le {instance.date_fin}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[instance.locataire.email],
                        fail_silently=True,
                    )
                    logger.info(f"Email d'expiration envoy� pour le contrat {instance.numero_contrat}")
                except Exception as e:
                    logger.error(f"Erreur envoi email expiration: {e}")


@receiver(pre_save, sender=RentalContract)
def calculate_contract_duration(sender, instance, **kwargs):
    """
    Calcule automatiquement la dur�e du contrat si non fournie
    """
    if instance.date_debut and instance.date_fin and not instance.duree_mois:
        delta = instance.date_fin - instance.date_debut
        instance.duree_mois = max(1, round(delta.days / 30))
        logger.info(f"Dur�e calcul�e automatiquement: {instance.duree_mois} mois")


# ============================================================================
# SIGNALS CONTRACT WORKFLOW (PMO)
# ============================================================================

@receiver(post_save, sender=ContractWorkflow)
def notify_workflow_stage_change(sender, instance, created, **kwargs):
    """
    Notifie lors du changement d'�tape du workflow
    """
    if not created:
        # V�rifier si l'�tape a chang�
        if instance.pk:
            old_instance = ContractWorkflow.objects.filter(pk=instance.pk).first()
            if old_instance and old_instance.etape_actuelle != instance.etape_actuelle:
                logger.info(
                    f"Workflow {instance.pk}: {old_instance.etape_actuelle} � {instance.etape_actuelle}"
                )

                # TODO: Envoyer notification selon l'�tape
                if instance.etape_actuelle == 'attente_facture':
                    # Notifier le service finance
                    logger.info("Notification � envoyer au service Finance")

                elif instance.etape_actuelle == 'visite_entree':
                    # Notifier le locataire et le responsable PMO
                    logger.info("Notification visite d'entr�e � envoyer")

                elif instance.etape_actuelle == 'termine':
                    # Activer le contrat automatiquement
                    contrat = instance.contrat
                    if contrat.statut != 'actif':
                        contrat.statut = 'actif'
                        contrat.save(update_fields=['statut'])
                        logger.info(f"Contrat {contrat.numero_contrat} activ� automatiquement")


@receiver(post_save, sender=ContractWorkflow)
def check_workflow_completion(sender, instance, created, **kwargs):
    """
    V�rifie si le workflow peut avancer automatiquement
    """
    if not created:
        # V�rifier si tous les documents obligatoires sont v�rifi�s
        if instance.statut_dossier != 'complet':
            docs_obligatoires = instance.documents.filter(obligatoire=True)
            tous_verifies = all(doc.statut == 'verifie' for doc in docs_obligatoires)

            if tous_verifies and docs_obligatoires.count() > 0:
                instance.statut_dossier = 'complet'
                instance.save(update_fields=['statut_dossier'])
                logger.info(f"Workflow {instance.pk}: Dossier marqu� comme complet")


# ============================================================================
# SIGNALS DOCUMENT CONTRACT
# ============================================================================

@receiver(post_save, sender=DocumentContrat)
def update_workflow_on_document_verification(sender, instance, created, **kwargs):
    """
    Met � jour le workflow quand un document est v�rifi�
    """
    if not created and instance.statut == 'verifie':
        workflow = instance.workflow

        # V�rifier si tous les documents obligatoires sont v�rifi�s
        docs_obligatoires = workflow.documents.filter(obligatoire=True)
        tous_verifies = all(doc.statut == 'verifie' for doc in docs_obligatoires)

        if tous_verifies:
            if workflow.statut_dossier != 'complet':
                workflow.statut_dossier = 'complet'
                workflow.save(update_fields=['statut_dossier'])
                logger.info(f"Workflow {workflow.pk}: Tous les documents obligatoires v�rifi�s")

                # Si le workflow est � l'�tape de v�rification, on peut potentiellement avancer
                if workflow.etape_actuelle == 'verification_dossier' and workflow.peut_avancer:
                    logger.info(f"Workflow {workflow.pk}: Pr�t � passer � l'�tape suivante")


@receiver(post_save, sender=DocumentContrat)
def notify_document_status_change(sender, instance, created, **kwargs):
    """
    Notifie lors du changement de statut d'un document
    """
    if not created:
        if instance.statut == 'refuse':
            logger.warning(
                f"Document {instance.get_type_document_display()} refus� pour le workflow {instance.workflow.pk}"
            )
            # TODO: Envoyer notification au locataire

        elif instance.statut == 'verifie':
            logger.info(
                f"Document {instance.get_type_document_display()} v�rifi� pour le workflow {instance.workflow.pk}"
            )


# ============================================================================
# CLEANUP SIGNALS
# ============================================================================

@receiver(post_delete, sender=RentalContract)
def cleanup_on_contract_delete(sender, instance, **kwargs):
    """
    Nettoie les donn�es li�es lors de la suppression d'un contrat
    """
    # Lib�rer l'appartement si le contrat �tait actif
    if instance.statut == 'actif':
        appartement = instance.appartement
        appartement.statut_occupation = 'libre'
        appartement.save(update_fields=['statut_occupation'])
        logger.info(f"Appartement {appartement.nom} lib�r� apr�s suppression du contrat")
