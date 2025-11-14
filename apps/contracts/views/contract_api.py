# apps/contracts/views/contract_api.py
"""
API endpoints pour les contrats de location
"""

import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone

from ..models import RentalContract
from apps.properties.models.appartement import Appartement
from apps.tiers.models import Tiers


@login_required
@require_http_methods(["GET"])
def get_appartement_info(request):
    """
    API pour récupérer les informations d'un appartement
    """
    appartement_id = request.GET.get('appartement_id')
    if not appartement_id:
        return JsonResponse({'error': 'ID appartement requis'}, status=400)

    try:
        appartement = Appartement.objects.select_related('residence__proprietaire').get(id=appartement_id)

        data = {
            'nom': appartement.nom,
            'residence_nom': appartement.residence.nom,
            'adresse_complete': appartement.adresse_complete,
            'loyer_base': float(appartement.loyer_base),
            'charges': float(appartement.charges),
            'loyer_total': float(appartement.loyer_total),
            'depot_garantie': float(appartement.depot_garantie) if appartement.depot_garantie else 0,
            'type_bien': appartement.get_type_bien_display(),
            'superficie': float(appartement.superficie) if appartement.superficie else None,
            'nb_pieces': appartement.nb_pieces,
            'nb_chambres': appartement.nb_chambres,
            'is_available': appartement.is_available,
            'proprietaire': {
                'nom': appartement.residence.proprietaire.nom_complet,
                'email': appartement.residence.proprietaire.email,
            }
        }

        return JsonResponse({'success': True, 'data': data})

    except Appartement.DoesNotExist:
        return JsonResponse({'error': 'Appartement non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_locataire_info(request):
    """
    API pour récupérer les informations d'un locataire (Tiers)
    """
    locataire_id = request.GET.get('locataire_id')
    if not locataire_id:
        return JsonResponse({'error': 'ID locataire requis'}, status=400)

    try:
        locataire = Tiers.objects.get(id=locataire_id, type_tiers='locataire')

        data = {
            'nom_complet': locataire.nom_complet,
            'email': locataire.email,
            'telephone': locataire.telephone,
        }

        return JsonResponse({'success': True, 'data': data})

    except Tiers.DoesNotExist:
        return JsonResponse({'error': 'Locataire non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def validate_contract_dates(request):
    """
    API pour valider les dates de contrat
    """
    try:
        data = json.loads(request.body)
        date_debut = datetime.strptime(data.get('date_debut'), '%Y-%m-%d').date()
        date_fin = datetime.strptime(data.get('date_fin'), '%Y-%m-%d').date()
        appartement_id = data.get('appartement_id')

        # Validations
        errors = []

        # Vérifier que la date de fin est après la date de début
        if date_fin <= date_debut:
            errors.append("La date de fin doit être postérieure à la date de début.")

        # Vérifier que les dates ne sont pas dans le passé
        if date_debut < timezone.now().date():
            errors.append("La date de début ne peut pas être dans le passé.")

        # Vérifier les conflits avec d'autres contrats
        if appartement_id:
            conflicting_contracts = RentalContract.objects.filter(
                appartement_id=appartement_id,
                statut__in=['actif', 'brouillon']
            ).filter(
                Q(date_debut__lte=date_fin) & Q(date_fin__gte=date_debut)
            )

            if conflicting_contracts.exists():
                contract = conflicting_contracts.first()
                errors.append(
                    f"Conflit avec le contrat {contract.numero_contrat} "
                    f"({contract.date_debut} - {contract.date_fin})"
                )

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Calculer la durée
        duree_jours = (date_fin - date_debut).days
        duree_mois = round(duree_jours / 30.44)  # Moyenne de jours par mois

        return JsonResponse({
            'success': True,
            'duree_jours': duree_jours,
            'duree_mois': duree_mois,
            'message': f'Durée du contrat: {duree_mois} mois ({duree_jours} jours)'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def contract_api_list(request):
    """
    API endpoint pour la liste des contrats (pour AJAX)
    """
    contracts = RentalContract.objects.select_related(
        'appartement__residence__proprietaire',
        'locataire',
        'cree_par'
    ).order_by('-created_at')

    # Filtres similaires à la vue liste
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')

    if search:
        contracts = contracts.filter(
            Q(numero_contrat__icontains=search) |
            Q(appartement__nom__icontains=search) |
            Q(appartement__residence__nom__icontains=search) |
            Q(locataire__nom__icontains=search) |
            Q(locataire__prenom__icontains=search) |
            Q(locataire__email__icontains=search)
        )

    if statut:
        contracts = contracts.filter(statut=statut)

    # Permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'tiers'):
            tiers = request.user.tiers
            if tiers.type_tiers == 'locataire':
                contracts = contracts.filter(locataire=tiers)
            elif tiers.type_tiers == 'proprietaire':
                contracts = contracts.filter(appartement__residence__proprietaire=tiers)
            else:
                contracts = contracts.none()
        else:
            contracts = contracts.none()

    # Limitation pour l'API
    contracts = contracts[:50]

    data = []
    for contract in contracts:
        data.append({
            'id': contract.id,
            'numero_contrat': contract.numero_contrat,
            'appartement_nom': f"{contract.appartement.residence.nom} - {contract.appartement.nom}",
            'locataire_nom': contract.locataire.nom_complet,
            'date_debut': contract.date_debut.strftime('%d/%m/%Y'),
            'date_fin': contract.date_fin.strftime('%d/%m/%Y'),
            'loyer_mensuel': float(contract.loyer_mensuel),
            'statut': contract.get_statut_display(),
            'url': reverse('contracts:detail', kwargs={'pk': contract.pk}),
        })

    return JsonResponse({
        'success': True,
        'data': data,
        'count': len(data)
    })


@login_required
@require_http_methods(["GET"])
def contract_stats_api(request):
    """
    API pour les statistiques des contrats
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission refusée'}, status=403)

    try:
        # Statistiques globales
        total = RentalContract.objects.count()
        actifs = RentalContract.objects.filter(statut='actif').count()
        expires = RentalContract.objects.filter(statut='expire').count()
        brouillons = RentalContract.objects.filter(statut='brouillon').count()

        # Contrats arrivant à échéance (30 jours)
        date_limite = timezone.now().date() + timedelta(days=30)
        arrivant_echeance = RentalContract.objects.filter(
            statut='actif',
            date_fin__lte=date_limite
        ).count()

        # Revenus mensuels estimés
        revenus_estimes = RentalContract.objects.filter(
            statut='actif'
        ).aggregate(total=Sum('loyer_mensuel'))['total'] or 0

        data = {
            'total_contrats': total,
            'contrats_actifs': actifs,
            'contrats_expires': expires,
            'contrats_brouillons': brouillons,
            'arrivant_echeance': arrivant_echeance,
            'revenus_mensuels_estimes': float(revenus_estimes),
            'taux_occupation': round((actifs / total * 100), 2) if total > 0 else 0,
        }

        return JsonResponse({'success': True, 'data': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_contract_info_api(request, pk):
    """
    API pour récupérer les informations d'un contrat
    Utilisé pour l'auto-complétion des factures de loyer
    """
    try:
        contrat = RentalContract.objects.select_related(
            'locataire',
            'appartement__residence__proprietaire'
        ).get(pk=pk)

        # Vérifier les permissions
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)

        data = {
            'success': True,
            'locataire': contrat.locataire.nom_complet,
            'bien': f"{contrat.appartement.nom} - {contrat.appartement.residence.nom}",
            'loyer_mensuel': f"{contrat.loyer_mensuel:,.0f}",
            'loyer_mensuel_raw': float(contrat.loyer_mensuel),
            'periode': f"Du {contrat.date_debut.strftime('%d/%m/%Y')} au {contrat.date_fin.strftime('%d/%m/%Y')}",
            'charges': f"{contrat.charges_mensuelles:,.0f}" if contrat.charges_mensuelles else "0",
            'statut': contrat.get_statut_display(),
        }

        return JsonResponse(data)

    except RentalContract.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Contrat non trouvé'
        }, status=404)
