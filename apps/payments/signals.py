# apps/payments/signals.py
"""
Signals pour le module Payments
Gestion automatique des actions liées aux paiements et factures
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, Invoice


@receiver(post_save, sender=Payment)
def workflow_facture_payee(sender, instance, created, **kwargs):
    """
    Quand un paiement est créé ou validé, mettre à jour la facture
    et vérifier si le workflow PMO peut avancer
    """
    # Ne traiter que les paiements validés avec une facture
    if not instance.facture or instance.statut != 'valide':
        return

    facture = instance.facture

    # ============================================
    # 1. RECALCULER LES MONTANTS (via @property)
    # ============================================
    # Les montants sont calculés automatiquement via les @property:
    # - facture.montant_paye : somme des paiements validés
    # - facture.solde_restant : montant_ttc - montant_paye

    # On utilise ces propriétés calculées
    total_paye = facture.montant_paye
    solde_restant = facture.solde_restant

    # ============================================
    # 2. METTRE À JOUR LE STATUT DE LA FACTURE
    # ============================================
    ancien_statut = facture.statut

    if solde_restant <= 0:
        # Facture complètement payée
        facture.statut = 'payee'
        print(f"✅ Facture {facture.numero_facture} complètement payée : {total_paye} FCFA")
    elif total_paye > 0:
        # Paiement partiel - garder le statut actuel mais logger l'info
        print(f"ℹ️ Facture {facture.numero_facture} partiellement payée : {total_paye} FCFA / {facture.montant_ttc} FCFA")

    # Sauvegarder uniquement le statut si changé
    if facture.statut != ancien_statut:
        facture.save(update_fields=['statut'])

    # ============================================
    # 3. METTRE À JOUR LE WORKFLOW PMO SI NÉCESSAIRE
    # ============================================
    # Vérifier si la facture est liée à un workflow
    try:
        workflow = facture.workflow_contrat.first()
    except AttributeError:
        workflow = None

    if workflow and workflow.etape_actuelle == 'attente_facture':
        # Si la facture est complètement payée
        if facture.statut == 'payee':
            # Mettre à jour le workflow
            workflow.facture_validee_le = timezone.now()
            workflow.save()

            print(f"✅ Workflow {workflow.id} - Facture validée, prêt à passer à l'étape suivante")

            # Possibilité de passer automatiquement à l'étape suivante
            # Décommentez la ligne suivante si vous voulez une progression automatique
            # workflow.passer_etape_suivante()

    # ============================================
    # 4. METTRE À JOUR LE WORKFLOW DEMANDE D'ACHAT
    # ============================================
    if facture.type_facture == 'demande_achat' and hasattr(facture, 'etape_workflow'):
        if facture.statut == 'payee':
            # Si la demande n'est pas encore marquée comme payée, la passer à "payé"
            # Accepter toutes les étapes avant paiement
            etapes_avant_paiement = ['comptable', 'validation_dg', 'approuve', 'en_cours_achat']

            if facture.etape_workflow in etapes_avant_paiement:
                ancien_statut = facture.etape_workflow
                facture.etape_workflow = 'paye'
                facture.save(update_fields=['etape_workflow'])
                print(f"✅ Demande d'achat {facture.numero_facture} - Workflow: {ancien_statut} → payé")

                # Créer une entrée dans l'historique
                try:
                    from apps.payments.models_extensions import HistoriqueValidation
                    HistoriqueValidation.objects.create(
                        demande=facture,
                        action='paiement',
                        effectue_par=instance.valide_par if hasattr(instance, 'valide_par') and instance.valide_par else None,
                        commentaire=f"Paiement {instance.numero_paiement} validé - Montant: {instance.montant} FCFA"
                    )
                except Exception as e:
                    print(f"⚠️ Erreur création historique: {e}")


@receiver(post_save, sender=Invoice)
def generer_documents_facture_payee(sender, instance, created, **kwargs):
    """
    🆕 MODULE 8 : Quand une facture de loyer passe à statut 'payee',
    préparer la génération automatique de :
    - État de loyer pour le propriétaire
    - Quittance pour le locataire
    """
    # Ne traiter que les factures de loyer liées à un contrat
    if instance.type_facture != 'loyer' or not instance.contrat:
        return

    # Détecter le passage au statut 'payee'
    if instance.statut == 'payee' and not instance.etat_loyer_genere:
        # Marquer pour génération des documents
        # Note : La génération effective des PDF sera faite par une tâche asynchrone
        # ou via une vue dédiée pour éviter de bloquer le signal

        print(f"✅ MODULE 8 : Facture {instance.numero_facture} payée - Documents à générer")
        print(f"   → État de loyer pour propriétaire : {instance.contrat.appartement.residence.proprietaire.nom_complet}")
        print(f"   → Quittance pour locataire : {instance.contrat.locataire.nom_complet}")

        # TODO : Déclencher génération asynchrone des documents
        # Exemple avec Celery : generate_invoice_documents.delay(instance.id)
        # Pour l'instant, on peut le faire directement dans une vue ou une commande

        # Optionnel : Envoyer notification au propriétaire
        try:
            from apps.notifications.utils import send_notification
            proprietaire = instance.contrat.appartement.residence.proprietaire
            if proprietaire.email:
                send_notification(
                    destinataire=proprietaire,
                    sujet=f"Loyer reçu - {instance.contrat.appartement.nom}",
                    message=f"Le loyer de {instance.montant_ttc} FCFA a été payé pour {instance.periode_debut.strftime('%B %Y')}.",
                    type_notification='paiement_recu'
                )
                print(f"   → Notification envoyée au propriétaire")
        except Exception as e:
            print(f"   ⚠️ Erreur notification : {e}")


@receiver(post_save, sender=Invoice)
def verifier_factures_en_retard(sender, instance, **kwargs):
    """
    🆕 MODULE 8 : Vérifie si une facture est en retard et envoie un rappel automatique
    """
    # Ne traiter que les factures de loyer émises et non payées
    if instance.type_facture != 'loyer' or instance.statut not in ['emise']:
        return

    # Vérifier si la facture est en retard
    if instance.is_overdue:
        now = timezone.now()

        # Vérifier si on doit envoyer un rappel (éviter de spammer)
        # Par exemple : 1 rappel par semaine maximum
        envoyer_rappel = False

        if not instance.date_derniere_relance:
            # Aucun rappel envoyé encore
            envoyer_rappel = True
        else:
            # Vérifier si le dernier rappel date de plus de 7 jours
            jours_depuis_dernier_rappel = (now - instance.date_derniere_relance).days
            if jours_depuis_dernier_rappel >= 7:
                envoyer_rappel = True

        if envoyer_rappel:
            # Mettre à jour le statut de la facture
            if instance.statut != 'en_retard':
                instance.statut = 'en_retard'
                instance.save(update_fields=['statut'])

            # Enregistrer le rappel
            from .models import PaymentReminder

            locataire = instance.contrat.locataire if instance.contrat else None
            if locataire and locataire.email:
                message = f"""
                Bonjour {locataire.nom_complet},

                Votre facture {instance.numero_facture} d'un montant de {instance.montant_ttc} FCFA
                est en retard (échéance : {instance.date_echeance.strftime('%d/%m/%Y')}).

                Merci de régulariser votre situation dans les plus brefs délais.

                Cordialement,
                L'équipe Seyni Properties
                """

                rappel = PaymentReminder.objects.create(
                    facture=instance,
                    type_rappel='automatique',
                    moyen_envoi='email',
                    message=message,
                    statut='envoye'
                )

                # Mettre à jour les compteurs
                instance.date_derniere_relance = now
                instance.nombre_relances += 1
                instance.save(update_fields=['date_derniere_relance', 'nombre_relances'])

                print(f"⚠️ MODULE 8 : Rappel envoyé pour facture {instance.numero_facture} (relance #{instance.nombre_relances})")

                # TODO : Envoyer l'email réel
                # send_email(locataire.email, 'Rappel de paiement', message)
