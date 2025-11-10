"""
Vues pour la gestion des budgets prévisionnels.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from apps.syndic.models import BudgetPrevisionnel, LigneBudget
from apps.syndic.forms import BudgetPrevisionnelForm


@login_required
def budget_list(request):
    """Liste de tous les budgets prévisionnels."""
    budgets = BudgetPrevisionnel.objects.select_related(
        'copropriete__residence'
    ).all()

    # Filtres
    copropriete_id = request.GET.get('copropriete')
    if copropriete_id:
        budgets = budgets.filter(copropriete_id=copropriete_id)

    annee = request.GET.get('annee')
    if annee:
        budgets = budgets.filter(annee=annee)

    statut = request.GET.get('statut')
    if statut:
        budgets = budgets.filter(statut=statut)

    budgets = budgets.order_by('-annee', 'copropriete__residence__nom')

    context = {
        'budgets': budgets,
        'copropriete_filter': copropriete_id,
        'annee_filter': annee,
        'statut_filter': statut,
    }

    return render(request, 'syndic/budget_list.html', context)


@login_required
def budget_detail(request, pk):
    """Détails d'un budget prévisionnel."""
    budget = get_object_or_404(
        BudgetPrevisionnel.objects.select_related('copropriete__residence'),
        pk=pk
    )

    # Lignes de budget par catégorie
    lignes = budget.lignes.all().order_by('categorie', 'description')

    # Calculs
    total_prevu = lignes.aggregate(total=Sum('montant_prevu'))['total'] or 0
    total_realise = lignes.aggregate(total=Sum('montant_realise'))['total'] or 0
    ecart = total_prevu - total_realise

    context = {
        'budget': budget,
        'lignes': lignes,
        'total_prevu': total_prevu,
        'total_realise': total_realise,
        'ecart': ecart,
    }

    return render(request, 'syndic/budget_detail.html', context)


@login_required
def budget_create(request):
    """Créer un nouveau budget prévisionnel."""
    if request.method == 'POST':
        form = BudgetPrevisionnelForm(request.POST, request.FILES)
        if form.is_valid():
            budget = form.save()
            messages.success(request, f'Budget {budget.annee} pour {budget.copropriete.residence.nom} créé avec succès.')
            return redirect('syndic:budget_detail', pk=budget.pk)
    else:
        # Pré-remplir la copropriété si fournie en paramètre
        copropriete_id = request.GET.get('copropriete')
        initial = {'copropriete': copropriete_id} if copropriete_id else {}
        form = BudgetPrevisionnelForm(initial=initial)

    context = {
        'form': form,
        'action': 'create',
    }

    return render(request, 'syndic/budget_form.html', context)


@login_required
def budget_update(request, pk):
    """Modifier un budget prévisionnel."""
    budget = get_object_or_404(BudgetPrevisionnel, pk=pk)

    if request.method == 'POST':
        form = BudgetPrevisionnelForm(request.POST, request.FILES, instance=budget)
        if form.is_valid():
            budget = form.save()
            messages.success(request, f'Budget {budget.annee} modifié avec succès.')
            return redirect('syndic:budget_detail', pk=budget.pk)
    else:
        form = BudgetPrevisionnelForm(instance=budget)

    context = {
        'form': form,
        'budget': budget,
        'action': 'update',
    }

    return render(request, 'syndic/budget_form.html', context)


@login_required
def budget_delete(request, pk):
    """Supprimer un budget prévisionnel."""
    budget = get_object_or_404(BudgetPrevisionnel, pk=pk)

    if request.method == 'POST':
        annee = budget.annee
        copropriete = budget.copropriete.residence.nom
        budget.delete()
        messages.success(request, f'Budget {annee} pour {copropriete} supprimé avec succès.')
        return redirect('syndic:budget_list')

    return redirect('syndic:budget_detail', pk=pk)
