"""
Vues pour la gestion des copropriétaires.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.syndic.models import Coproprietaire
from apps.syndic.forms import CoproprietaireForm


@login_required
def coproprietaire_list(request):
    """Liste de tous les copropriétaires."""
    coproprietaires = Coproprietaire.objects.select_related(
        'tiers',
        'copropriete__residence'
    ).prefetch_related('lots').all()

    # Filtres
    copropriete_id = request.GET.get('copropriete')
    if copropriete_id:
        coproprietaires = coproprietaires.filter(copropriete_id=copropriete_id)

    statut = request.GET.get('statut')
    if statut == 'actif':
        coproprietaires = coproprietaires.filter(is_active=True)
    elif statut == 'inactif':
        coproprietaires = coproprietaires.filter(is_active=False)

    coproprietaires = coproprietaires.order_by(
        'copropriete__residence__nom',
        'tiers__nom',
        'tiers__prenom'
    )

    context = {
        'coproprietaires': coproprietaires,
        'copropriete_filter': copropriete_id,
        'statut_filter': statut,
    }

    return render(request, 'syndic/coproprietaire_list.html', context)


@login_required
def coproprietaire_create(request):
    """Créer un nouveau copropriétaire."""
    if request.method == 'POST':
        form = CoproprietaireForm(request.POST)
        if form.is_valid():
            coproprietaire = form.save()
            messages.success(request, f'Copropriétaire "{coproprietaire.tiers.nom_complet}" ajouté avec succès.')
            return redirect('syndic:copropriete_detail', pk=coproprietaire.copropriete.pk)
    else:
        # Pré-remplir la copropriété si fournie en paramètre
        copropriete_id = request.GET.get('copropriete')
        initial = {'copropriete': copropriete_id} if copropriete_id else {}
        form = CoproprietaireForm(initial=initial)

    context = {
        'form': form,
        'action': 'create',
    }

    return render(request, 'syndic/coproprietaire_form.html', context)


@login_required
def coproprietaire_update(request, pk):
    """Modifier un copropriétaire."""
    coproprietaire = get_object_or_404(Coproprietaire, pk=pk)

    if request.method == 'POST':
        form = CoproprietaireForm(request.POST, instance=coproprietaire)
        if form.is_valid():
            coproprietaire = form.save()
            messages.success(request, f'Copropriétaire "{coproprietaire.tiers.nom_complet}" modifié avec succès.')
            return redirect('syndic:copropriete_detail', pk=coproprietaire.copropriete.pk)
    else:
        form = CoproprietaireForm(instance=coproprietaire)

    context = {
        'form': form,
        'coproprietaire': coproprietaire,
        'action': 'update',
    }

    return render(request, 'syndic/coproprietaire_form.html', context)


@login_required
def coproprietaire_delete(request, pk):
    """Supprimer un copropriétaire."""
    coproprietaire = get_object_or_404(Coproprietaire, pk=pk)
    copropriete_pk = coproprietaire.copropriete.pk

    if request.method == 'POST':
        nom = coproprietaire.tiers.nom_complet
        coproprietaire.delete()
        messages.success(request, f'Copropriétaire "{nom}" supprimé avec succès.')
        return redirect('syndic:copropriete_detail', pk=copropriete_pk)

    return redirect('syndic:copropriete_detail', pk=copropriete_pk)
