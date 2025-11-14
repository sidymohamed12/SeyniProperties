# apps/contracts/views/contract_reports.py
"""
Rapports et statistiques pour les contrats de location
"""

import csv
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum

from ..models import RentalContract


@login_required
def contracts_statistics_view(request):
    """
    Vue des statistiques des contrats
    """
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('contracts:list')

    # Statistiques basiques
    stats = {
        'total_contracts': RentalContract.objects.count(),
        'active_contracts': RentalContract.objects.filter(statut='actif').count(),
        'expired_contracts': RentalContract.objects.filter(statut='expire').count(),
        'draft_contracts': RentalContract.objects.filter(statut='brouillon').count(),
        'terminated_contracts': RentalContract.objects.filter(statut='resilie').count(),
    }

    # Revenus mensuels estimés
    monthly_revenue = RentalContract.objects.filter(
        statut='actif'
    ).aggregate(total=Sum('loyer_mensuel'))['total'] or 0

    stats['monthly_revenue'] = float(monthly_revenue)

    context = {
        'stats': stats,
    }

    return render(request, 'contracts/statistics.html', context)


@login_required
def contracts_expiring_report(request):
    """
    Rapport des contrats qui expirent bientôt
    Adapté au template expiring.html avec sections urgents/bientôt
    """
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('contracts:list')

    today = datetime.now().date()
    in_7_days = today + timedelta(days=7)
    in_30_days = today + timedelta(days=30)

    # Contrats URGENTS (≤ 7 jours)
    urgent_contracts = RentalContract.objects.filter(
        statut='actif',
        date_fin__lte=in_7_days,
        date_fin__gte=today
    ).select_related(
        'appartement__residence__proprietaire',
        'locataire',
        'cree_par'
    ).order_by('date_fin')

    # Contrats expirant BIENTÔT (8-30 jours)
    soon_contracts = RentalContract.objects.filter(
        statut='actif',
        date_fin__lte=in_30_days,
        date_fin__gt=in_7_days
    ).select_related(
        'appartement__residence__proprietaire',
        'locataire',
        'cree_par'
    ).order_by('date_fin')

    total_expiring = urgent_contracts.count() + soon_contracts.count()

    context = {
        'urgent_contracts': urgent_contracts,
        'soon_contracts': soon_contracts,
        'total_expiring': total_expiring,
        'today': today,
    }

    return render(request, 'contracts/expiring.html', context)


@login_required
def contracts_revenue_report(request):
    """
    Rapport des revenus par contrat
    Adapté au template reports/revenue.html
    """
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('contracts:list')

    # Filtres depuis le GET
    period = request.GET.get('period', 'current')
    residence_id = request.GET.get('residence')
    proprietaire_id = request.GET.get('proprietaire')

    # Query de base : contrats actifs
    contracts_query = RentalContract.objects.filter(
        statut='actif'
    ).select_related(
        'appartement__residence__proprietaire',
        'locataire',
        'cree_par'
    )

    # Appliquer les filtres
    if residence_id:
        contracts_query = contracts_query.filter(appartement__residence_id=residence_id)

    if proprietaire_id:
        contracts_query = contracts_query.filter(
            appartement__residence__proprietaire_id=proprietaire_id
        )

    active_contracts = contracts_query.order_by('-loyer_mensuel')

    # Calculs financiers
    total_revenue = sum(contract.montant_total_mensuel for contract in active_contracts)
    annual_revenue = total_revenue * 12
    average_rent = total_revenue / active_contracts.count() if active_contracts.count() > 0 else 0
    total_contracts = active_contracts.count()

    # Données pour les filtres
    from apps.properties.models.residence import Residence
    from apps.tiers.models import Tiers

    residences = Residence.objects.all().order_by('nom')
    proprietaires = Tiers.objects.filter(type_tiers='proprietaire').order_by('nom')

    context = {
        'contracts': active_contracts,
        'total_revenue': total_revenue,
        'annual_revenue': annual_revenue,
        'average_rent': average_rent,
        'total_contracts': total_contracts,
        'residences': residences,
        'proprietaires': proprietaires,
        'period': period,
    }

    return render(request, 'contracts/reports/revenue.html', context)


@login_required
def export_contracts_csv(request):
    """
    Export des contrats en CSV
    """
    if not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('contracts:list')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contrats.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Numéro', 'Appartement', 'Locataire', 'Date début', 'Date fin',
        'Loyer', 'Charges', 'Total', 'Statut'
    ])

    contracts = RentalContract.objects.select_related(
        'appartement__residence__proprietaire',
        'locataire',
        'cree_par'
    ).all()

    for contract in contracts:
        writer.writerow([
            contract.numero_contrat,
            f"{contract.appartement.nom} - {contract.appartement.residence.nom}",
            contract.locataire.nom_complet,
            contract.date_debut.strftime('%d/%m/%Y'),
            contract.date_fin.strftime('%d/%m/%Y'),
            contract.loyer_mensuel,
            contract.charges_mensuelles,
            contract.montant_total_mensuel,
            contract.get_statut_display()
        ])

    return response
