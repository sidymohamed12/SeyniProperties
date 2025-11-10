"""
Vues pour la gestion des cotisations.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.syndic.models import CotisationSyndic, PaiementCotisation
from apps.syndic.forms import CotisationSyndicForm, PaiementCotisationForm


@login_required
def cotisation_list(request):
    """Liste de toutes les cotisations avec filtres."""
    cotisations = CotisationSyndic.objects.select_related(
        'coproprietaire__tiers',
        'coproprietaire__copropriete__residence'
    ).all()

    # Filtres
    statut = request.GET.get('statut')
    if statut:
        cotisations = cotisations.filter(statut=statut)

    annee = request.GET.get('annee')
    if annee:
        cotisations = cotisations.filter(annee=annee)

    periode = request.GET.get('periode')
    if periode:
        cotisations = cotisations.filter(periode=periode)

    cotisations = cotisations.order_by('-annee', '-periode', 'coproprietaire__tiers__nom')

    context = {
        'cotisations': cotisations,
        'statut_filter': statut,
        'annee_filter': annee,
        'periode_filter': periode,
    }

    return render(request, 'syndic/cotisation_list.html', context)


@login_required
def cotisation_detail(request, pk):
    """Détails d'une cotisation."""
    cotisation = get_object_or_404(
        CotisationSyndic.objects.select_related(
            'coproprietaire__tiers',
            'coproprietaire__copropriete__residence'
        ).prefetch_related('paiements'),
        pk=pk
    )

    context = {
        'cotisation': cotisation,
    }

    return render(request, 'syndic/cotisation_detail.html', context)


@login_required
def cotisation_create(request):
    """Créer une nouvelle cotisation."""
    if request.method == 'POST':
        form = CotisationSyndicForm(request.POST)
        if form.is_valid():
            cotisation = form.save()
            messages.success(request, f'Cotisation {cotisation.reference} créée avec succès.')
            return redirect('syndic:cotisation_detail', pk=cotisation.pk)
    else:
        form = CotisationSyndicForm()

    context = {
        'form': form,
        'action': 'create',
    }

    return render(request, 'syndic/cotisation_form.html', context)


@login_required
def cotisation_update(request, pk):
    """Modifier une cotisation."""
    cotisation = get_object_or_404(CotisationSyndic, pk=pk)

    if request.method == 'POST':
        form = CotisationSyndicForm(request.POST, instance=cotisation)
        if form.is_valid():
            cotisation = form.save()
            messages.success(request, f'Cotisation {cotisation.reference} modifiée avec succès.')
            return redirect('syndic:cotisation_detail', pk=cotisation.pk)
    else:
        form = CotisationSyndicForm(instance=cotisation)

    context = {
        'form': form,
        'cotisation': cotisation,
        'action': 'update',
    }

    return render(request, 'syndic/cotisation_form.html', context)


@login_required
def cotisation_delete(request, pk):
    """Supprimer une cotisation."""
    cotisation = get_object_or_404(CotisationSyndic, pk=pk)

    if request.method == 'POST':
        reference = cotisation.reference
        cotisation.delete()
        messages.success(request, f'Cotisation {reference} supprimée avec succès.')
        return redirect('syndic:cotisation_list')

    return redirect('syndic:cotisation_detail', pk=pk)


@login_required
def paiement_create(request, cotisation_pk):
    """Enregistrer un paiement pour une cotisation."""
    cotisation = get_object_or_404(CotisationSyndic, pk=cotisation_pk)

    if request.method == 'POST':
        form = PaiementCotisationForm(request.POST, cotisation=cotisation)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.cotisation = cotisation
            paiement.save()
            messages.success(request, f'Paiement de {paiement.montant} FCFA enregistré avec succès.')
            return redirect('syndic:cotisation_detail', pk=cotisation.pk)
    else:
        # Pré-remplir avec le montant restant
        montant_initial = cotisation.montant_restant
        form = PaiementCotisationForm(
            cotisation=cotisation,
            initial={
                'montant': montant_initial if montant_initial > 0 else 0
            }
        )

    context = {
        'form': form,
        'cotisation': cotisation,
    }

    return render(request, 'syndic/paiement_form.html', context)
