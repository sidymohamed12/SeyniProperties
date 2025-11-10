"""
Vues pour le tableau de bord syndic.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.syndic.models import Copropriete, CotisationSyndic
from decimal import Decimal


@login_required
def syndic_dashboard(request):
    """
    Tableau de bord principal du module syndic.
    Affiche les statistiques générales et les alertes.
    """
    # Statistiques générales
    coproprietes_actives = Copropriete.objects.filter(is_active=True)
    total_coproprietes = coproprietes_actives.count()

    # Cotisations du trimestre actuel
    now = timezone.now()
    annee_courante = now.year
    mois = now.month
    if mois <= 3:
        periode = 'Q1'
    elif mois <= 6:
        periode = 'Q2'
    elif mois <= 9:
        periode = 'Q3'
    else:
        periode = 'Q4'

    cotisations_periode = CotisationSyndic.objects.filter(
        annee=annee_courante,
        periode=periode
    )

    # Montants théoriques vs perçus
    total_theorique = cotisations_periode.aggregate(
        total=Sum('montant_theorique')
    )['total'] or Decimal('0.00')

    total_percu = cotisations_periode.aggregate(
        total=Sum('montant_percu')
    )['total'] or Decimal('0.00')

    total_restant = total_theorique - total_percu

    # Taux de recouvrement
    if total_theorique > 0:
        taux_recouvrement = (total_percu / total_theorique) * 100
    else:
        taux_recouvrement = 0

    # Cotisations en retard
    cotisations_retard = cotisations_periode.filter(
        statut='impaye',
        date_echeance__lt=now.date()
    )
    nb_impayees = cotisations_retard.count()
    montant_impaye = cotisations_retard.aggregate(
        total=Sum('montant_theorique')
    )['total'] or Decimal('0.00')

    # Copropriétaires avec impayés
    coproprietaires_debiteurs = cotisations_retard.values(
        'coproprietaire__tiers__nom',
        'coproprietaire__tiers__prenom',
        'coproprietaire__copropriete__residence__nom'
    ).annotate(
        total_impaye=Sum('montant_theorique') - Sum('montant_percu')
    ).order_by('-total_impaye')[:10]

    # Prochaines cotisations à émettre
    prochaines_cotisations = CotisationSyndic.objects.filter(
        statut='a_venir',
        date_emission__gte=now.date(),
        date_emission__lte=now.date() + timezone.timedelta(days=30)
    ).order_by('date_emission')[:5]

    # Budget global
    budgets_annuels = coproprietes_actives.aggregate(
        total=Sum('budget_annuel')
    )['total'] or Decimal('0.00')

    context = {
        'total_coproprietes': total_coproprietes,
        'periode_courante': f'{annee_courante}-{periode}',
        'total_theorique': total_theorique,
        'total_percu': total_percu,
        'total_restant': total_restant,
        'taux_recouvrement': taux_recouvrement,
        'nb_impayees': nb_impayees,
        'montant_impaye': montant_impaye,
        'coproprietaires_debiteurs': coproprietaires_debiteurs,
        'prochaines_cotisations': prochaines_cotisations,
        'budgets_annuels': budgets_annuels,
        'coproprietes_actives': coproprietes_actives[:5],  # Top 5 pour affichage
    }

    return render(request, 'syndic/dashboard.html', context)
