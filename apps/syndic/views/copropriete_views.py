"""
Vues pour la gestion des copropriétés.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from apps.syndic.models import Copropriete, Coproprietaire
from apps.syndic.forms import CoproprieteForm


@login_required
def copropriete_list(request):
    """Liste de toutes les copropriétés."""
    coproprietes = Copropriete.objects.select_related('residence').all()

    context = {
        'coproprietes': coproprietes,
    }

    return render(request, 'syndic/copropriete_list.html', context)


@login_required
def copropriete_detail(request, pk):
    """Détails d'une copropriété."""
    copropriete = get_object_or_404(
        Copropriete.objects.select_related('residence'),
        pk=pk
    )

    # Copropriétaires
    coproprietaires = copropriete.coproprietaires.select_related(
        'tiers'
    ).filter(is_active=True).order_by('-quote_part')

    # Budget actuel
    annee_courante = timezone.now().year
    budget_actuel = copropriete.budgets.filter(
        annee=annee_courante
    ).first()

    # Cotisations de l'année en cours
    cotisations_annee = copropriete.coproprietaires.filter(
        is_active=True
    ).values('tiers__nom', 'tiers__prenom').annotate(
        total_theorique=Sum('cotisations__montant_theorique'),
        total_percu=Sum('cotisations__montant_percu')
    )

    context = {
        'copropriete': copropriete,
        'coproprietaires': coproprietaires,
        'budget_actuel': budget_actuel,
        'cotisations_annee': cotisations_annee,
    }

    return render(request, 'syndic/copropriete_detail.html', context)


@login_required
def copropriete_create(request):
    """Créer une nouvelle copropriété."""
    if request.method == 'POST':
        form = CoproprieteForm(request.POST)
        if form.is_valid():
            copropriete = form.save()
            messages.success(request, f'Copropriété "{copropriete.residence.nom}" créée avec succès.')
            return redirect('syndic:copropriete_detail', pk=copropriete.pk)
    else:
        form = CoproprieteForm()

    context = {
        'form': form,
        'action': 'create',
    }

    return render(request, 'syndic/copropriete_form.html', context)


@login_required
def copropriete_update(request, pk):
    """Modifier une copropriété."""
    copropriete = get_object_or_404(Copropriete, pk=pk)

    if request.method == 'POST':
        form = CoproprieteForm(request.POST, instance=copropriete)
        if form.is_valid():
            copropriete = form.save()
            messages.success(request, f'Copropriété "{copropriete.residence.nom}" modifiée avec succès.')
            return redirect('syndic:copropriete_detail', pk=copropriete.pk)
    else:
        form = CoproprieteForm(instance=copropriete)

    context = {
        'form': form,
        'copropriete': copropriete,
        'action': 'update',
    }

    return render(request, 'syndic/copropriete_form.html', context)


@login_required
def copropriete_delete(request, pk):
    """Supprimer une copropriété."""
    copropriete = get_object_or_404(Copropriete, pk=pk)

    if request.method == 'POST':
        nom = copropriete.residence.nom
        copropriete.delete()
        messages.success(request, f'Copropriété "{nom}" supprimée avec succès.')
        return redirect('syndic:copropriete_list')

    # Si GET, rediriger vers la page de détails
    return redirect('syndic:copropriete_detail', pk=pk)
