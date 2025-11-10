# apps/payments/views/demande_achat_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponseForbidden
from decimal import Decimal

from apps.payments.models import Invoice, LigneDemandeAchat, HistoriqueValidation
from apps.payments.forms import (
    DemandeAchatForm,
    LigneDemandeAchatFormSet,
    ValidationResponsableForm,
    TraitementComptableForm,
    ValidationDGForm,
    ReceptionMarchandiseForm,
    LigneReceptionFormSet,
)


# ============================================================================
# CRÉATION DE DEMANDE D'ACHAT
# ============================================================================

@login_required
def demande_achat_create(request):
    """Vue pour créer une nouvelle demande d'achat"""

    if request.method == 'POST':
        form = DemandeAchatForm(request.POST)
        formset = LigneDemandeAchatFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Créer la facture
                demande = form.save(commit=False)
                demande.type_facture = 'demande_achat'
                demande.demandeur = request.user
                demande.date_demande = timezone.now().date()
                demande.date_emission = timezone.now().date()
                demande.etape_workflow = 'brouillon'
                demande.statut = 'brouillon'
                demande.creee_par = request.user
                demande.is_manual = True

                # Calculer le montant total à partir des lignes
                total = Decimal('0.00')
                for ligne_form in formset:
                    if ligne_form.cleaned_data and not ligne_form.cleaned_data.get('DELETE'):
                        quantite = ligne_form.cleaned_data.get('quantite', 0)
                        prix_unitaire = ligne_form.cleaned_data.get('prix_unitaire', 0)
                        total += Decimal(str(quantite)) * Decimal(str(prix_unitaire))

                demande.montant_ht = total
                demande.montant_ttc = total
                demande.signature_demandeur_date = timezone.now()

                demande.save()

                # Sauvegarder les lignes
                formset.instance = demande
                formset.save()

                # Créer l'entrée d'historique
                HistoriqueValidation.objects.create(
                    demande=demande,
                    action='creation',
                    effectue_par=request.user,
                    commentaire=f"Demande créée par {request.user.get_full_name()}"
                )

                # ✅ Si lié à un travail, mettre à jour le statut du travail
                # Architecture 1-to-Many: Plus besoin d'assigner demande_achat, la relation existe via travail_lie
                if demande.travail_lie and demande.travail_lie.statut not in ['en_attente_materiel', 'en_cours', 'complete']:
                    demande.travail_lie.statut = 'en_attente_materiel'
                    demande.travail_lie.save()

                messages.success(
                    request,
                    f'Demande d\'achat {demande.numero_facture} créée avec succès! '
                    f'Vous pouvez maintenant la soumettre pour validation.'
                )

                return redirect('payments:demande_achat_detail', pk=demande.pk)

    else:
        form = DemandeAchatForm()
        formset = LigneDemandeAchatFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Nouvelle Demande d\'Achat',
    }

    return render(request, 'payments/demande_achat_create.html', context)


# ============================================================================
# DÉTAIL ET LISTE
# ============================================================================

@login_required
def demande_achat_detail(request, pk):
    """Vue détaillée d'une demande d'achat"""

    demande = get_object_or_404(
        Invoice.objects.select_related(
            'demandeur', 'travail_lie', 'valide_par_responsable',
            'traite_par_comptable', 'valide_par_dg', 'receptionne_par'
        ).prefetch_related(
            'lignes_achat', 'historique_validations__effectue_par'
        ),
        pk=pk,
        type_facture='demande_achat'
    )

    # Vérifier les permissions
    user_can_view = (
        request.user == demande.demandeur or
        request.user.user_type in ['manager', 'accountant'] or
        request.user.is_staff
    )

    if not user_can_view:
        return HttpResponseForbidden("Vous n'avez pas accès à cette demande.")

    context = {
        'demande': demande,
        'lignes': demande.lignes_achat.all(),
        'historique': demande.historique_validations.all().order_by('-date_action'),
        'title': f'Demande {demande.numero_facture}',
    }

    return render(request, 'payments/demande_achat_detail.html', context)


@login_required
def demande_achat_list(request):
    """Liste des demandes d'achat avec filtres"""

    # Base queryset
    demandes = Invoice.objects.filter(
        type_facture='demande_achat'
    ).select_related(
        'demandeur', 'travail_lie'
    ).prefetch_related('lignes_achat')

    # Filtres
    etape = request.GET.get('etape')
    if etape:
        demandes = demandes.filter(etape_workflow=etape)

    # Filtrer selon le rôle de l'utilisateur
    if request.user.user_type == 'manager':
        # Manager voit tout
        pass
    elif request.user.user_type == 'accountant':
        # Comptable voit ce qui est validé par responsable
        demandes = demandes.filter(
            etape_workflow__in=['comptable', 'validation_dg', 'approuve', 'en_cours_achat', 'recue', 'paye']
        )
    else:
        # Employés voient uniquement leurs demandes
        demandes = demandes.filter(demandeur=request.user)

    # Ordre
    demandes = demandes.order_by('-date_demande', '-created_at')

    context = {
        'demandes': demandes,
        'etape_filter': etape,
        'title': 'Demandes d\'Achat',
    }

    return render(request, 'payments/demande_achat_list.html', context)


# ============================================================================
# SOUMISSION POUR VALIDATION
# ============================================================================

@login_required
def demande_achat_soumettre(request, pk):
    """Soumettre une demande pour validation (demandeur ou manager)"""

    demande = get_object_or_404(
        Invoice,
        pk=pk,
        type_facture='demande_achat',
        etape_workflow='brouillon'
    )

    # Vérifier que l'utilisateur a le droit de soumettre
    # Soit c'est le demandeur, soit c'est un manager
    if demande.demandeur != request.user and request.user.user_type != 'manager':
        messages.error(request, "Vous n'avez pas l'autorisation de soumettre cette demande.")
        return redirect('payments:demande_achat_detail', pk=demande.pk)

    if request.method == 'POST':
        with transaction.atomic():
            demande.etape_workflow = 'en_attente'
            demande.save()

            HistoriqueValidation.objects.create(
                demande=demande,
                action='soumission',
                effectue_par=request.user,
                commentaire="Demande soumise pour validation responsable"
            )

            messages.success(
                request,
                f'Demande {demande.numero_facture} soumise pour validation!'
            )

        return redirect('payments:demande_achat_detail', pk=demande.pk)

    context = {
        'demande': demande,
        'title': 'Soumettre la demande',
    }

    return render(request, 'payments/demande_achat_soumettre.html', context)


# ============================================================================
# VALIDATION RESPONSABLE
# ============================================================================

@login_required
def demande_achat_validation_responsable(request, pk):
    """Validation par le responsable"""

    # Vérifier que l'utilisateur est manager
    if request.user.user_type != 'manager':
        return HttpResponseForbidden("Seuls les managers peuvent valider.")

    demande = get_object_or_404(
        Invoice.objects.select_related('demandeur').prefetch_related('lignes_achat'),
        pk=pk,
        type_facture='demande_achat',
        etape_workflow='en_attente'
    )

    if request.method == 'POST':
        form = ValidationResponsableForm(request.POST)

        if form.is_valid():
            decision = form.cleaned_data['decision']
            commentaire = form.cleaned_data.get('commentaire', '')

            with transaction.atomic():
                if decision == 'valider':
                    # Valider
                    demande.etape_workflow = 'valide_responsable'
                    demande.valide_par_responsable = request.user
                    demande.date_validation_responsable = timezone.now()
                    demande.commentaire_responsable = commentaire

                    # Passer automatiquement à l'étape comptable
                    demande.etape_workflow = 'comptable'

                    action = 'validation_responsable'
                    message_success = f'Demande {demande.numero_facture} validée et transmise à la comptabilité!'

                else:
                    # Refuser
                    demande.etape_workflow = 'refuse'
                    demande.valide_par_responsable = request.user
                    demande.date_validation_responsable = timezone.now()
                    demande.commentaire_responsable = commentaire

                    action = 'refus_responsable'
                    message_success = f'Demande {demande.numero_facture} refusée.'

                demande.save()

                HistoriqueValidation.objects.create(
                    demande=demande,
                    action=action,
                    effectue_par=request.user,
                    commentaire=commentaire or f"Décision: {decision}"
                )

                messages.success(request, message_success)

            return redirect('payments:demande_achat_detail', pk=demande.pk)

    else:
        form = ValidationResponsableForm()

    context = {
        'demande': demande,
        'form': form,
        'lignes': demande.lignes_achat.all(),
        'title': f'Validation Responsable - {demande.numero_facture}',
    }

    return render(request, 'payments/demande_achat_validation_responsable.html', context)


# ============================================================================
# TRAITEMENT COMPTABLE
# ============================================================================

@login_required
def demande_achat_traitement_comptable(request, pk):
    """Traitement par le comptable (préparation chèque)"""

    # Vérifier que l'utilisateur est comptable
    if request.user.user_type != 'accountant':
        return HttpResponseForbidden("Seuls les comptables peuvent traiter.")

    demande = get_object_or_404(
        Invoice.objects.select_related('demandeur', 'valide_par_responsable').prefetch_related('lignes_achat'),
        pk=pk,
        type_facture='demande_achat',
        etape_workflow='comptable'
    )

    if request.method == 'POST':
        form = TraitementComptableForm(request.POST, instance=demande)

        if form.is_valid():
            with transaction.atomic():
                demande = form.save(commit=False)
                demande.traite_par_comptable = request.user
                demande.date_traitement_comptable = timezone.now()
                demande.etape_workflow = 'validation_dg'
                demande.save()

                HistoriqueValidation.objects.create(
                    demande=demande,
                    action='traitement_comptable',
                    effectue_par=request.user,
                    commentaire=demande.commentaire_comptable or "Chèque préparé"
                )

                HistoriqueValidation.objects.create(
                    demande=demande,
                    action='preparation_cheque',
                    effectue_par=request.user,
                    commentaire=f"Chèque N° {demande.numero_cheque} - {demande.banque_cheque}"
                )

                messages.success(
                    request,
                    f'Chèque préparé pour la demande {demande.numero_facture}. '
                    f'En attente de signature DG.'
                )

            return redirect('payments:demande_achat_detail', pk=demande.pk)

    else:
        form = TraitementComptableForm(instance=demande)

    context = {
        'demande': demande,
        'form': form,
        'lignes': demande.lignes_achat.all(),
        'title': f'Traitement Comptable - {demande.numero_facture}',
    }

    return render(request, 'payments/demande_achat_traitement_comptable.html', context)


# ============================================================================
# VALIDATION DIRECTION GÉNÉRALE
# ============================================================================

@login_required
def demande_achat_validation_dg(request, pk):
    """Validation finale par la Direction Générale"""

    # Vérifier que l'utilisateur est manager (DG)
    if request.user.user_type != 'manager':
        return HttpResponseForbidden("Seule la Direction peut valider.")

    demande = get_object_or_404(
        Invoice.objects.select_related(
            'demandeur', 'valide_par_responsable', 'traite_par_comptable'
        ).prefetch_related('lignes_achat'),
        pk=pk,
        type_facture='demande_achat',
        etape_workflow='validation_dg'
    )

    if request.method == 'POST':
        form = ValidationDGForm(request.POST)

        if form.is_valid():
            decision = form.cleaned_data['decision']
            commentaire = form.cleaned_data.get('commentaire', '')

            with transaction.atomic():
                if decision == 'valider':
                    # Valider
                    demande.etape_workflow = 'approuve'
                    demande.valide_par_dg = request.user
                    demande.date_validation_dg = timezone.now()
                    demande.commentaire_dg = commentaire

                    action = 'validation_dg'
                    message_success = f'Demande {demande.numero_facture} approuvée! Achat autorisé.'

                else:
                    # Refuser
                    demande.etape_workflow = 'refuse'
                    demande.valide_par_dg = request.user
                    demande.date_validation_dg = timezone.now()
                    demande.commentaire_dg = commentaire

                    action = 'refus_dg'
                    message_success = f'Demande {demande.numero_facture} refusée par la DG.'

                demande.save()

                HistoriqueValidation.objects.create(
                    demande=demande,
                    action=action,
                    effectue_par=request.user,
                    commentaire=commentaire or f"Décision DG: {decision}"
                )

                if decision == 'valider':
                    HistoriqueValidation.objects.create(
                        demande=demande,
                        action='approbation',
                        effectue_par=request.user,
                        commentaire="Approbation finale - Achat autorisé"
                    )

                messages.success(request, message_success)

            return redirect('payments:demande_achat_detail', pk=demande.pk)

    else:
        form = ValidationDGForm()

    context = {
        'demande': demande,
        'form': form,
        'lignes': demande.lignes_achat.all(),
        'title': f'Validation DG - {demande.numero_facture}',
    }

    return render(request, 'payments/demande_achat_validation_dg.html', context)


# ============================================================================
# RÉCEPTION MARCHANDISE
# ============================================================================

@login_required
def demande_achat_reception(request, pk):
    """Enregistrer la réception de la marchandise"""

    demande = get_object_or_404(
        Invoice.objects.prefetch_related('lignes_achat'),
        pk=pk,
        type_facture='demande_achat',
        etape_workflow__in=['approuve', 'en_cours_achat']
    )

    # Vérifier permissions (manager, accountant, ou demandeur)
    if not (request.user.user_type in ['manager', 'accountant'] or request.user == demande.demandeur):
        return HttpResponseForbidden("Vous n'avez pas accès à cette fonction.")

    if request.method == 'POST':
        form = ReceptionMarchandiseForm(request.POST, instance=demande)
        formset = LigneReceptionFormSet(request.POST, instance=demande)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                demande = form.save(commit=False)
                demande.receptionne_par = request.user
                demande.etape_workflow = 'recue'
                demande.save()

                formset.save()

                HistoriqueValidation.objects.create(
                    demande=demande,
                    action='reception',
                    effectue_par=request.user,
                    commentaire=f"Marchandise réceptionnée le {demande.date_reception}"
                )

                # Si lié à un travail, débloquer le travail
                if demande.travail_lie and demande.travail_lie.statut == 'en_attente_materiel':
                    demande.travail_lie.statut = 'assigne'
                    demande.travail_lie.save()

                messages.success(
                    request,
                    f'Réception enregistrée pour {demande.numero_facture}!'
                )

            return redirect('payments:demande_achat_detail', pk=demande.pk)

    else:
        form = ReceptionMarchandiseForm(instance=demande)
        formset = LigneReceptionFormSet(instance=demande)

    context = {
        'demande': demande,
        'form': form,
        'formset': formset,
        'title': f'Réception Marchandise - {demande.numero_facture}',
    }

    return render(request, 'payments/demande_achat_reception.html', context)


# ============================================================================
# DASHBOARDS PAR RÔLE
# ============================================================================

@login_required
def dashboard_demandes_achat(request):
    """Dashboard selon le rôle de l'utilisateur"""

    user_type = request.user.user_type

    if user_type == 'manager':
        # Manager voit tout
        en_attente_validation = Invoice.objects.filter(
            type_facture='demande_achat',
            etape_workflow='en_attente'
        ).count()

        en_attente_dg = Invoice.objects.filter(
            type_facture='demande_achat',
            etape_workflow='validation_dg'
        ).count()

        stats = {
            'en_attente_validation': en_attente_validation,
            'en_attente_dg': en_attente_dg,
        }

    elif user_type == 'accountant':
        # Comptable voit ce qu'il doit traiter
        a_traiter = Invoice.objects.filter(
            type_facture='demande_achat',
            etape_workflow='comptable'
        ).count()

        stats = {
            'a_traiter': a_traiter,
        }

    else:
        # Employé voit ses demandes
        mes_demandes = Invoice.objects.filter(
            type_facture='demande_achat',
            demandeur=request.user
        ).count()

        stats = {
            'mes_demandes': mes_demandes,
        }

    context = {
        'stats': stats,
        'user_type': user_type,
        'title': 'Dashboard Demandes d\'Achat',
    }

    return render(request, 'payments/dashboard_demandes_achat.html', context)
