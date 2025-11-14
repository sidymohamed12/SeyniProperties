# apps/dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Imports des modèles
from apps.properties.models import Residence, Appartement
from apps.contracts.models import RentalContract
from apps.payments.models import Invoice, Payment
from apps.maintenance.models.intervention import Intervention
from apps.accounts.models.custom_user import CustomUser
from apps.tiers.models import Tiers, TiersBien

# Import conditionnel pour Employee et Task
try:
    from apps.employees.models.employee import Employee
    from apps.employees.models.task import Task
except ImportError:
    # Modèles factices si les apps n'existent pas
    class Employee:
        objects = None
    class Task:
        objects = None


# ============================================================================
# VUES PRINCIPALES DU DASHBOARD
# ============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Vue principale du dashboard - Version nettoyée"""
    template_name = 'dashboard/index.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions utilisateur
        if request.user.user_type not in ['manager', 'accountant']:
            return redirect('admin:login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dates pour les calculs
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        # === STATISTIQUES PRINCIPALES ===
        
        # Résidences et appartements
        total_residences = Residence.objects.count()
        total_appartements = Appartement.objects.count()
        appartements_libres = Appartement.objects.filter(
            statut_occupation__in=['libre', 'available']
        ).count()
        appartements_occupes = Appartement.objects.filter(
            statut_occupation__in=['occupe', 'occupied']
        ).count()
        
        # Taux d'occupation
        taux_occupation = round(
            (appartements_occupes / total_appartements * 100) if total_appartements > 0 else 0,
            1
        )
        
        # Contrats
        total_contrats = RentalContract.objects.count()
        contrats_actifs = RentalContract.objects.filter(statut='actif').count()
        contrats_expires = RentalContract.objects.filter(
            statut='actif',
            date_fin__lte=today + timedelta(days=30)
        ).count()
        
        # Finances
        revenus_mois = Payment.objects.filter(
            date_paiement__gte=start_of_month,
            statut='paye'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        factures_impayees = Invoice.objects.filter(
            statut='en_attente'
        ).count()
        
        montant_impaye = Invoice.objects.filter(
            statut='en_attente'
        ).aggregate(total=Sum('montant_ttc'))['total'] or 0
        
        # Travaux (unified model)
        from apps.maintenance.models.travail import Travail
        travaux_en_cours = Travail.objects.filter(
            statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
        ).count()

        travaux_urgents = Travail.objects.filter(
            statut__in=['signale', 'assigne', 'en_cours'],
            priorite='urgente'
        ).count()

        travaux_termines_mois = Travail.objects.filter(
            statut='termine',
            date_fin__gte=start_of_month
        ).count()

        # Demandes d'achat
        demandes_achat_en_attente = Invoice.objects.filter(
            type_facture='demande_achat',
            etape_workflow__in=['brouillon', 'en_attente', 'valide_responsable', 'comptable']
        ).count()

        # Revenus par mois (last 6 months)
        revenus_par_mois = []
        for i in range(5, -1, -1):
            month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            revenus = Payment.objects.filter(
                date_paiement__range=[month_start, month_end],
                statut='paye'
            ).aggregate(total=Sum('montant'))['total'] or 0
            revenus_par_mois.append({
                'mois': month_start.strftime('%b %Y'),
                'montant': float(revenus)
            })

        # Activités récentes
        recent_activities = []
        
        # Derniers contrats
        recent_contracts = RentalContract.objects.order_by('-created_at')[:3]
        for contract in recent_contracts:
            recent_activities.append({
                'type': 'contract',
                'icon': 'fa-file-contract',
                'color': 'blue',
                'title': f'Nouveau contrat: {contract.numero_contrat}',
                'description': f'{contract.locataire.nom_complet}',
                'date': contract.created_at,
            })
        
        # Dernières interventions
        recent_interventions = Intervention.objects.order_by('-date_signalement')[:3]
        for intervention in recent_interventions:
            recent_activities.append({
                'type': 'intervention',
                'icon': 'fa-wrench',
                'color': 'orange',
                'title': intervention.titre,
                'description': intervention.get_statut_display(),
                'date': intervention.date_signalement,
            })
        
        # Trier par date
        recent_activities.sort(key=lambda x: x['date'], reverse=True)

        # Statistiques tiers
        tiers_actifs = Tiers.objects.filter(statut='actif').count()
        tiers_recent = Tiers.objects.order_by('-created_at')[:5]
        tiers_proprietaires = Tiers.objects.filter(type_tiers='proprietaire').count()
        tiers_locataires = Tiers.objects.filter(type_tiers='locataire').count()
        tiers_prestataires = Tiers.objects.filter(type_tiers='prestataire').count()

        # Données pour le formulaire nouveau_travail (modal)
        residences_list = Residence.objects.all().order_by('nom')
        appartements_list = Appartement.objects.select_related('residence').all().order_by('residence__nom', 'nom')

        # Récupérer les employés pour le formulaire
        employes_list = CustomUser.objects.filter(
            user_type__in=['technicien', 'technician', 'field_agent', 'employee'],
            is_active=True
        ).order_by('first_name', 'last_name')

        context.update({
            # Statistiques biens
            'total_residences': total_residences,
            'total_appartements': total_appartements,
            'appartements_libres': appartements_libres,
            'appartements_occupes': appartements_occupes,
            'taux_occupation': taux_occupation,

            # Statistiques contrats
            'total_contrats': total_contrats,
            'contrats_actifs': contrats_actifs,
            'contrats_expires': contrats_expires,

            # Statistiques finances
            'revenus_mois': float(revenus_mois),
            'factures_impayees': factures_impayees,
            'montant_impaye': float(montant_impaye),
            'revenus_par_mois': json.dumps(revenus_par_mois),

            # Statistiques travaux
            'travaux_en_cours': travaux_en_cours,
            'travaux_urgents': travaux_urgents,
            'travaux_termines_mois': travaux_termines_mois,
            'demandes_achat_en_attente': demandes_achat_en_attente,

            # Statistiques tiers
            'tiers_actifs': tiers_actifs,
            'tiers_recent': tiers_recent,
            'tiers_proprietaires': tiers_proprietaires,
            'tiers_locataires': tiers_locataires,
            'tiers_prestataires': tiers_prestataires,

            # Activités récentes
            'recent_activities': recent_activities[:5],

            # Données pour formulaires modaux
            'residences': residences_list,
            'appartements': appartements_list,
            'employes': employes_list,
        })
        
        return context


class PropertiesOverviewView(LoginRequiredMixin, TemplateView):
    """Vue d'aperçu des propriétés"""
    template_name = 'dashboard/properties_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupérer les données principales
        residences = Residence.objects.prefetch_related('appartements').all()
        appartements = Appartement.objects.select_related('residence').all()

        # Statistiques globales
        total_appartements = appartements.count()
        appartements_libres = appartements.filter(statut_occupation__in=['libre', 'available']).count()
        appartements_occupes = appartements.filter(statut_occupation__in=['occupe', 'occupied']).count()
        taux_occupation = round((appartements_occupes / total_appartements * 100) if total_appartements > 0 else 0, 1)

        # Préparer les données des résidences avec leurs statistiques
        residences_data = []
        for residence in residences:
            res_appartements = residence.appartements.all()
            total_appts = res_appartements.count()
            occupes = res_appartements.filter(statut_occupation__in=['occupe', 'occupied']).count()
            taux = round((occupes / total_appts * 100) if total_appts > 0 else 0, 1)

            residences_data.append({
                'id': residence.id,
                'nom': residence.nom,
                'adresse': residence.adresse,
                'ville': residence.ville,
                'quartier': residence.quartier,
                'total_appartements': total_appts,
                'taux_occupation': taux,
                'appartements': res_appartements,
            })

        context.update({
            'residences_data': residences_data,
            'all_appartements': appartements,  # Tous les appartements pour section séparée
            'total_residences': residences.count(),
            'total_appartements': total_appartements,
            'appartements_libres': appartements_libres,
            'appartements_occupes': appartements_occupes,
            'taux_occupation': taux_occupation,
        })

        return context


class FinancialOverviewView(LoginRequiredMixin, TemplateView):
    """Vue d'aperçu financier"""
    template_name = 'dashboard/financial_overview.html'


class AnalyticsView(LoginRequiredMixin, TemplateView):
    """Vue analytics"""
    template_name = 'dashboard/analytics.html'


class ResidencesListView(LoginRequiredMixin, TemplateView):
    """Vue liste des résidences"""
    template_name = 'dashboard/residences_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['residences'] = Residence.objects.all()
        return context


class ResidenceDetailView(LoginRequiredMixin, TemplateView):
    """Vue détail d'une résidence"""
    template_name = 'dashboard/residence_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        residence_id = kwargs.get('residence_id')
        context['residence'] = get_object_or_404(Residence, id=residence_id)
        return context


@login_required
def tasks_interventions_unified_view(request):
    """Vue unifiée tâches et interventions - Redirection vers employees"""
    messages.info(request, "Cette vue est obsolète. Redirection vers la gestion des tâches.")
    return redirect('employees:tasks')


# ============================================================================
# VUES DE REDIRECTION (pour compatibilité avec le système de connexion)
# ============================================================================

@login_required
def manager_dashboard_view(request):
    """Redirection manager vers dashboard principal"""
    return redirect('dashboard:index')


@login_required
def accountant_dashboard_view(request):
    """Redirection comptable vers dashboard principal"""
    return redirect('dashboard:index')


@login_required
def employee_dashboard_redirect(request):
    """Redirection pour les employés vers leur dashboard approprié"""
    user = request.user
    
    # Vérifier que l'utilisateur est bien un employé
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if user.user_type not in employee_types:
        messages.error(request, "Accès non autorisé pour ce type d'utilisateur.")
        return redirect('accounts:login')
    
    # Rediriger vers le dashboard mobile des employés
    try:
        return redirect('employees:index')
    except:
        messages.info(request, "Dashboard employé en cours de développement.")
        return redirect('dashboard:index')


# ============================================================================
# APIs POUR STATISTIQUES ET DONNÉES EN TEMPS RÉEL
# ============================================================================

@login_required
def dashboard_stats_api(request):
    """API pour récupérer les statistiques du dashboard"""
    try:
        today = timezone.now().date()
        
        stats = {
            'residences': Residence.objects.count(),
            'appartements': Appartement.objects.count(),
            'appartements_libres': Appartement.objects.filter(
                statut_occupation__in=['libre', 'available']
            ).count(),
            'contrats_actifs': RentalContract.objects.filter(statut='actif').count(),
            'interventions_ouvertes': Intervention.objects.filter(
                statut__in=['signale', 'en_cours']
            ).count(),
        }
        
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def dashboard_revenue_api(request):
    """API pour les revenus"""
    try:
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        
        revenus = Payment.objects.filter(
            date_paiement__gte=start_of_month,
            statut='paye'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        return JsonResponse({
            'success': True,
            'revenue': float(revenus),
            'month': today.strftime('%B %Y')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def dashboard_weather_api(request):
    """API pour la météo (placeholder)"""
    return JsonResponse({
        'success': True,
        'weather': {
            'temperature': 22,
            'condition': 'sunny',
            'icon': 'sun'
        }
    })


@login_required
def dashboard_alerts_api(request):
    """API pour les alertes"""
    try:
        alerts = []
        
        # Contrats expirant bientôt
        expiring_contracts = RentalContract.objects.filter(
            statut='actif',
            date_fin__lte=timezone.now().date() + timedelta(days=30)
        ).count()
        
        if expiring_contracts > 0:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-file-contract',
                'message': f'{expiring_contracts} contrat(s) expire(nt) dans 30 jours',
                'url': '/contracts/'
            })
        
        # Interventions urgentes
        urgent_interventions = Intervention.objects.filter(
            statut='signale',
            priorite='urgente'
        ).count() if hasattr(Intervention, 'priorite') else 0
        
        if urgent_interventions > 0:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-exclamation-triangle',
                'message': f'{urgent_interventions} intervention(s) urgente(s)',
                'url': '/maintenance/interventions/'
            })
        
        # Factures impayées
        unpaid_invoices = Invoice.objects.filter(
            statut='en_attente',
            date_echeance__lt=timezone.now().date()
        ).count()
        
        if unpaid_invoices > 0:
            alerts.append({
                'type': 'warning',
                'icon': 'fa-exclamation-circle',
                'message': f'{unpaid_invoices} facture(s) impayée(s)',
                'url': '/payments/invoices/'
            })
        
        return JsonResponse({'success': True, 'alerts': alerts})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================================================
# APIs POUR LES FORMULAIRES MODAUX
# ============================================================================

@login_required
def get_landlords_for_property(request):
    """API pour récupérer les propriétaires"""
    try:
        proprietaires = Tiers.objects.filter(type_tiers='proprietaire', statut='actif')
        data = [
            {
                'id': p.id,
                'name': p.nom_complet,
                'email': p.email
            }
            for p in proprietaires
        ]
        return JsonResponse({'success': True, 'landlords': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_residences_by_landlord(request, landlord_id):
    """API pour récupérer les résidences d'un propriétaire"""
    try:
        residences = Residence.objects.filter(proprietaire_id=landlord_id)
        data = [
            {
                'id': r.id,
                'name': r.nom,
                'address': r.adresse_complete
            }
            for r in residences
        ]
        return JsonResponse({'success': True, 'residences': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_appartements_by_residence(request, residence_id):
    """API pour récupérer les appartements d'une résidence"""
    try:
        appartements = Appartement.objects.filter(residence_id=residence_id)
        data = [
            {
                'id': a.id,
                'name': a.nom,
                'available': a.statut_occupation in ['libre', 'available'],
                'loyer': float(a.loyer_base)
            }
            for a in appartements
        ]
        return JsonResponse({'success': True, 'appartements': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_all_properties(request):
    """API pour récupérer toutes les propriétés"""
    try:
        appartements = Appartement.objects.select_related('residence').all()
        data = [
            {
                'id': a.id,
                'name': f"{a.residence.nom} - {a.nom}",
                'available': a.statut_occupation in ['libre', 'available']
            }
            for a in appartements
        ]
        return JsonResponse({'success': True, 'properties': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_all_appartements(request):
    """API pour récupérer tous les appartements"""
    try:
        appartements = Appartement.objects.select_related('residence').all()
        data = [
            {
                'id': a.id,
                'name': a.nom,
                'residence': a.residence.nom,
                'available': a.statut_occupation in ['libre', 'available'],
                'loyer': float(a.loyer_base)
            }
            for a in appartements
        ]
        return JsonResponse({'success': True, 'appartements': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_technicians_api(request):
    """API pour récupérer les techniciens"""
    try:
        technicians = CustomUser.objects.filter(
            user_type__in=['technician', 'technicien', 'field_agent'],
            is_active=True
        )
        data = [
            {
                'id': t.id,
                'name': t.get_full_name(),
                'email': t.email
            }
            for t in technicians
        ]
        return JsonResponse({'success': True, 'technicians': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_tenants_api(request):
    """API pour récupérer les locataires"""
    try:
        locataires = Tiers.objects.filter(type_tiers='locataire', statut='actif')
        data = [
            {
                'id': l.id,
                'name': l.nom_complet,
                'email': l.email
            }
            for l in locataires
        ]
        return JsonResponse({'success': True, 'tenants': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_appartement_info_api(request, appartement_id):
    """API pour récupérer les infos d'un appartement"""
    try:
        appartement = Appartement.objects.select_related('residence').get(id=appartement_id)
        data = {
            'id': appartement.id,
            'nom': appartement.nom,
            'residence': appartement.residence.nom,
            'loyer_base': float(appartement.loyer_base),
            'charges': float(appartement.charges),
            'available': appartement.statut_occupation in ['libre', 'available']
        }
        return JsonResponse({'success': True, 'appartement': data})
    except Appartement.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Appartement non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================================================
# ACTIONS RAPIDES
# ============================================================================

@login_required
def dashboard_quick_action(request):
    """Action rapide générique"""
    action = request.POST.get('action')
    
    if action == 'refresh_stats':
        return dashboard_stats_api(request)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Action non reconnue'
        })


@login_required
def quick_add_property(request):
    """Redirection vers l'ajout de bien"""
    return redirect('dashboard:nouveau_bien')


@login_required
def quick_add_residence(request):
    """Redirection vers l'ajout de résidence"""
    return redirect('dashboard:nouvelle_residence')


@login_required
def quick_add_landlord(request):
    """Redirection vers l'ajout de bailleur"""
    return redirect('dashboard:nouveau_bailleur')


@login_required
def quick_add_task(request):
    """Redirection vers l'ajout de tâche"""
    return redirect('dashboard:nouvelle_tache')


@login_required
def quick_add_appartement(request):
    """Redirection vers l'ajout d'appartement"""
    return redirect('dashboard:nouveau_appartement')


# ============================================================================
# NOUVELLES APIS POUR GESTION HIÉRARCHIQUE
# ============================================================================

@login_required
def residence_stats_api(request, residence_id):
    """API pour les stats d'une résidence"""
    try:
        residence = get_object_or_404(Residence, id=residence_id)
        appartements = residence.appartements.all()
        
        stats = {
            'total_appartements': appartements.count(),
            'appartements_libres': appartements.filter(
                statut_occupation__in=['libre', 'available']
            ).count(),
            'appartements_occupes': appartements.filter(
                statut_occupation__in=['occupe', 'occupied']
            ).count(),
        }
        
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def update_appartement_status(request, appartement_id):
    """API pour mettre à jour le statut d'un appartement"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        appartement = get_object_or_404(Appartement, id=appartement_id)
        new_status = request.POST.get('status')
        
        if new_status in ['libre', 'available', 'occupe', 'occupied', 'maintenance']:
            appartement.statut_occupation = new_status
            appartement.save()
            return JsonResponse({'success': True, 'message': 'Statut mis à jour'})
        else:
            return JsonResponse({'success': False, 'error': 'Statut invalide'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def residences_dashboard_stats(request):
    """API pour les stats du dashboard des résidences"""
    try:
        stats = {
            'total_residences': Residence.objects.count(),
            'total_appartements': Appartement.objects.count(),
            'taux_occupation': 0
        }
        
        total = stats['total_appartements']
        if total > 0:
            occupes = Appartement.objects.filter(
                statut_occupation__in=['occupe', 'occupied']
            ).count()
            stats['taux_occupation'] = round((occupes / total) * 100, 1)
        
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def recent_activities_api(request):
    """API pour récupérer les activités récentes"""
    try:
        activities = []
        recent_date = timezone.now() - timedelta(days=7)
        
        # Contrats récents
        recent_contracts = RentalContract.objects.filter(
            created_at__gte=recent_date
        ).order_by('-created_at')[:3]
        
        for contract in recent_contracts:
            activities.append({
                'title': f'Contrat "{contract.numero_contrat}" créé',
                'date': contract.created_at.strftime('%d/%m à %H:%M'),
                'icon': 'fas fa-file-contract',
                'color': 'blue',
                'status': 'Nouveau'
            })
        
        # Résidences récentes
        recent_residences = Residence.objects.filter(
            created_at__gte=recent_date
        ).order_by('-created_at')[:3]
        
        for residence in recent_residences:
            activities.append({
                'title': f'Résidence "{residence.nom}" créée',
                'date': residence.created_at.strftime('%d/%m à %H:%M'),
                'icon': 'fas fa-building',
                'color': 'purple',
                'status': 'Nouveau'
            })
        
        # Appartements récents
        recent_appartements = Appartement.objects.filter(
            created_at__gte=recent_date
        ).order_by('-created_at')[:3]
        
        for appartement in recent_appartements:
            activities.append({
                'title': f'Appartement "{appartement.nom}" créé',
                'date': appartement.created_at.strftime('%d/%m à %H:%M'),
                'icon': 'fas fa-home',
                'color': 'blue',
                'status': 'Nouveau'
            })
        
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'activities': activities[:5]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============================================================================
# VUES D'ENREGISTREMENT (Formulaires modaux AJAX)
# ============================================================================

@login_required
def enregistrements_view(request):
    """Vue page des enregistrements avec statistiques"""
    from apps.maintenance.models.travail import Travail
    from datetime import datetime

    # Date du mois en cours
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    # Statistiques Tiers
    stats = {}
    stats['proprietaires'] = Tiers.objects.filter(type_tiers='proprietaire').count()
    stats['locataires'] = Tiers.objects.filter(type_tiers='locataire').count()
    stats['prestataires'] = Tiers.objects.filter(type_tiers='prestataire').count()

    # Statistiques Biens
    stats['appartements_libres'] = Appartement.objects.filter(statut_occupation='libre').count()
    stats['appartements_occupes'] = Appartement.objects.filter(statut_occupation='occupe').count()

    # Statistiques Contrats
    stats['contrats_actifs'] = RentalContract.objects.filter(statut='actif').count()
    stats['contrats_expirent_soon'] = RentalContract.objects.filter(
        statut='actif',
        date_fin__lte=today + timedelta(days=30)
    ).count()

    # Statistiques Travaux
    stats['travaux_urgents'] = Travail.objects.filter(priorite__in=['urgente', 'haute']).exclude(statut__in=['termine', 'annule']).count()
    stats['travaux_en_cours'] = Travail.objects.filter(statut__in=['en_cours', 'assigne', 'en_attente_materiel']).count()

    # Statistiques Demandes d'Achat
    stats['demandes_en_attente'] = Invoice.objects.filter(
        type_facture='demande_achat',
        etape_workflow__in=['en_attente', 'valide_responsable', 'comptable', 'validation_dg']
    ).count()
    stats['demandes_validees'] = Invoice.objects.filter(
        type_facture='demande_achat',
        etape_workflow__in=['approuve', 'en_cours_achat', 'recue']
    ).count()

    # Statistiques Paiements
    total_paiements = Payment.objects.filter(
        date_paiement__gte=start_of_month,
        date_paiement__lte=today
    ).aggregate(total=Sum('montant'))['total']
    stats['total_paiements_mois'] = total_paiements if total_paiements else 0

    context = {
        'stats': stats
    }

    return render(request, 'dashboard/enregistrements.html', context)


@login_required
def nouveau_bien(request):
    """Vue pour créer un nouveau bien (appartement)"""
    if  request.user.user_type not in ['manager', 'accountant']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'})
        return redirect('properties:appartement_create')
    
    if request.method == 'GET':
        # Retourner le formulaire HTML pour le modal
        residences = Residence.objects.filter(statut='active').order_by('nom')
        type_bien_choices = [
            ('appartement', 'Appartement'),
            ('studio', 'Studio'),
            ('duplex', 'Duplex'),
            ('villa', 'Villa'),
            ('bureau', 'Bureau'),
            ('commerce', 'Commerce'),
        ]
        
        context = {
            'residences': residences,
            'type_bien_choices': type_bien_choices,
        }
        return render(request, 'dashboard/forms/nouveau_bien.html', context)
    
    elif request.method == 'POST':
        try:
            # Récupération des données
            nom = request.POST.get('nom', '').strip()
            residence_id = request.POST.get('residence_id')
            type_bien = request.POST.get('type_bien', 'appartement')
            etage = request.POST.get('etage', 0)
            superficie = request.POST.get('superficie')
            nb_pieces = request.POST.get('nb_pieces', 1)
            nb_chambres = request.POST.get('nb_chambres', 1)
            loyer_base = request.POST.get('loyer_base', 0)
            charges = request.POST.get('charges', 0)
            depot_garantie = request.POST.get('depot_garantie', 0)
            
            # Validations
            if not nom:
                raise ValueError("Le nom est obligatoire")
            if not residence_id:
                raise ValueError("La résidence est obligatoire")
            
            residence = get_object_or_404(Residence, id=residence_id)
            
            # Créer l'appartement
            appartement = Appartement.objects.create(
                nom=nom,
                residence=residence,
                type_bien=type_bien,
                etage=int(etage) if etage else 0,
                superficie=Decimal(str(superficie)) if superficie else None,
                nb_pieces=int(nb_pieces) if nb_pieces else 1,
                nb_chambres=int(nb_chambres) if nb_chambres else 1,
                loyer_base=Decimal(str(loyer_base)) if loyer_base else Decimal('0'),
                charges=Decimal(str(charges)) if charges else Decimal('0'),
                depot_garantie=Decimal(str(depot_garantie)) if depot_garantie else Decimal('0'),
                statut_occupation='libre',
            )
            
            messages.success(request, f'Appartement "{appartement.nom}" créé avec succès!')
            
            return JsonResponse({
                'success': True,
                'message': f'Appartement "{appartement.nom}" créé avec succès!',
                'appartement_id': appartement.id,
                'appartement_nom': appartement.nom,
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            })


@login_required
def nouvelle_residence(request):
    """Vue pour créer une nouvelle résidence"""
    if  request.user.user_type not in ['manager', 'accountant']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'})
        return redirect('properties:residence_create')
    
    if request.method == 'GET':
        # Retourner le formulaire HTML pour le modal
        proprietaires = Tiers.objects.filter(type_tiers='proprietaire', statut='actif').order_by('nom', 'prenom')

        context = {
            'proprietaires': proprietaires,
        }
        return render(request, 'dashboard/forms/nouvelle_residence.html', context)
    
    elif request.method == 'POST':
        try:
            # Récupération des données
            nom = request.POST.get('nom', '').strip()
            proprietaire_id = request.POST.get('proprietaire_id') or request.POST.get('bailleur_id')
            adresse = request.POST.get('adresse', '').strip()
            ville = request.POST.get('ville', '').strip()
            code_postal = request.POST.get('code_postal', '').strip()
            quartier = request.POST.get('quartier', '').strip()

            # Validations
            if not nom:
                raise ValueError("Le nom est obligatoire")
            if not proprietaire_id:
                raise ValueError("Le propriétaire est obligatoire")
            if not adresse:
                raise ValueError("L'adresse est obligatoire")

            proprietaire = get_object_or_404(Tiers, id=proprietaire_id, type_tiers='proprietaire')

            # Créer la résidence
            residence = Residence.objects.create(
                nom=nom,
                proprietaire=proprietaire,
                adresse=adresse,
                ville=ville,
                code_postal=code_postal,
                quartier=quartier,
                statut='active',
            )
            
            messages.success(request, f'Résidence "{residence.nom}" créée avec succès!')
            
            return JsonResponse({
                'success': True,
                'message': f'Résidence "{residence.nom}" créée avec succès!',
                'residence_id': residence.id,
                'residence_nom': residence.nom,
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            })


@login_required
def nouveau_locataire(request):
    """Vue pour créer un nouveau locataire (Tiers)"""
    if request.user.user_type not in ['manager', 'accountant']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'})
        return redirect('tenants:create')

    if request.method == 'GET':
        # Retourner le formulaire HTML pour le modal
        return render(request, 'dashboard/forms/nouveau_locataire.html')

    elif request.method == 'POST':
        try:
            # Récupération des données
            prenom = request.POST.get('first_name', '').strip() or request.POST.get('prenom', '').strip()
            nom = request.POST.get('last_name', '').strip() or request.POST.get('nom', '').strip()
            email = request.POST.get('email', '').strip()
            telephone = request.POST.get('phone', '').strip() or request.POST.get('telephone', '').strip()
            date_entree = request.POST.get('date_entree')
            piece_identite_numero = request.POST.get('piece_identite', '').strip() or request.POST.get('piece_identite_numero', '').strip()

            # Validations
            if not all([nom, prenom, email]):
                raise ValueError("Le nom, prénom et email sont obligatoires")

            # Créer le compte utilisateur optionnel
            user = None
            username = None
            temp_password = None

            if request.POST.get('create_account') == 'true':
                # Générer un username unique
                username = f"{prenom.lower()}.{nom.lower()}"
                base_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Générer un mot de passe temporaire
                import random
                import string
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                # Créer l'utilisateur
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=prenom,
                    last_name=nom,
                    phone=telephone,
                    user_type='tenant',
                    password=temp_password
                )

            # Créer le Tiers locataire
            locataire = Tiers.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                type_tiers='locataire',
                statut='actif',
                user=user,
                date_entree=date_entree if date_entree else None,
                piece_identite_numero=piece_identite_numero,
            )

            messages.success(request, f'Locataire "{locataire.nom_complet}" créé avec succès!')

            response_data = {
                'success': True,
                'message': f'Locataire "{locataire.nom_complet}" créé avec succès!',
                'locataire_id': locataire.id,
            }

            if username and temp_password:
                response_data['username'] = username
                response_data['password'] = temp_password

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            })


@login_required
def nouveau_bailleur(request):
    """Vue pour créer un nouveau propriétaire (Tiers)"""
    if request.user.user_type not in ['manager', 'accountant']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'})
        return redirect('landlords:create')

    if request.method == 'GET':
        # Retourner le formulaire HTML pour le modal
        type_bailleur_choices = [
            ('particulier', 'Particulier'),
            ('societe', 'Société'),
        ]

        context = {
            'type_bailleur_choices': type_bailleur_choices,
        }
        return render(request, 'dashboard/forms/nouveau_bailleur.html', context)

    elif request.method == 'POST':
        try:
            # Récupération des données
            prenom = request.POST.get('first_name', '').strip() or request.POST.get('prenom', '').strip()
            nom = request.POST.get('last_name', '').strip() or request.POST.get('nom', '').strip()
            email = request.POST.get('email', '').strip()
            telephone = request.POST.get('phone', '').strip() or request.POST.get('telephone', '').strip()
            landlord_type = request.POST.get('landlord_type', 'particulier') or request.POST.get('type_bailleur', 'particulier')
            entreprise = request.POST.get('company_name', '').strip() or request.POST.get('entreprise', '').strip()

            # Validations
            if not email:
                raise ValueError("L'email est obligatoire")

            if landlord_type == 'societe' and not entreprise:
                raise ValueError("Le nom de la société est obligatoire")

            if landlord_type == 'particulier' and not all([nom, prenom]):
                raise ValueError("Le nom et prénom sont obligatoires pour un particulier")

            # Créer le compte utilisateur optionnel
            user = None
            username = None
            temp_password = None

            if request.POST.get('create_account') == 'true':
                # Générer un username unique
                username = f"{prenom.lower()}.{nom.lower()}"
                base_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Générer un mot de passe temporaire
                import random
                import string
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                # Créer l'utilisateur
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=prenom,
                    last_name=nom,
                    phone=telephone,
                    user_type='landlord',
                    password=temp_password
                )

            # Créer le Tiers propriétaire
            proprietaire = Tiers.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                type_tiers='proprietaire',
                statut='actif',
                user=user,
                type_bailleur=landlord_type,
                entreprise=entreprise if landlord_type == 'societe' else '',
            )

            messages.success(request, f'Propriétaire "{proprietaire.nom_complet}" créé avec succès!')

            response_data = {
                'success': True,
                'message': f'Propriétaire "{proprietaire.nom_complet}" créé avec succès!',
                'bailleur_id': proprietaire.id,
            }

            if username and temp_password:
                response_data['username'] = username
                response_data['password'] = temp_password

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            })


@login_required
def nouveau_contrat(request):
    """Vue pour créer un nouveau contrat"""
    if request.user.user_type not in ['manager', 'accountant']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'})
        return redirect('contracts:create')
    
    if request.method == 'GET':
        # Retourner le formulaire HTML pour le modal
        appartements = Appartement.objects.filter(
            statut_occupation__in=['libre', 'available']
        ).select_related('residence').order_by('residence__nom', 'nom')

        locataires = Tiers.objects.filter(
            type_tiers='locataire',
            statut='actif'
        ).order_by('nom', 'prenom')

        context = {
            'appartements': appartements,
            'locataires': locataires,
        }
        return render(request, 'dashboard/forms/nouveau_contrat.html', context)
    
    elif request.method == 'POST':
        try:
            # Récupération des données
            appartement_id = request.POST.get('appartement_id')
            locataire_id = request.POST.get('locataire_id')
            loyer_mensuel = request.POST.get('loyer_mensuel')
            charges_mensuelles = request.POST.get('charges_mensuelles', '0')
            depot_garantie = request.POST.get('depot_garantie')
            duree_mois = request.POST.get('duree_mois', '12')
            date_debut = request.POST.get('date_debut')
            
            # Validations
            if not all([appartement_id, locataire_id, loyer_mensuel, depot_garantie, date_debut]):
                raise ValueError("Tous les champs obligatoires doivent être remplis")

            appartement = get_object_or_404(Appartement, id=appartement_id)
            locataire = get_object_or_404(Tiers, id=locataire_id, type_tiers='locataire')
            
            # Calculer la date de fin
            from datetime import datetime, timedelta
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            date_fin = date_debut_obj + timedelta(days=int(duree_mois) * 30)
            
            # Générer un numéro de contrat unique
            import random
            numero_contrat = f"CNT-{timezone.now().year}-{random.randint(1000, 9999)}"
            while RentalContract.objects.filter(numero_contrat=numero_contrat).exists():
                numero_contrat = f"CNT-{timezone.now().year}-{random.randint(1000, 9999)}"
            
            # Créer le contrat
            contrat = RentalContract.objects.create(
                numero_contrat=numero_contrat,
                appartement=appartement,
                locataire=locataire,
                date_debut=date_debut_obj,
                date_fin=date_fin,
                duree_mois=int(duree_mois),
                loyer_mensuel=Decimal(str(loyer_mensuel)),
                charges_mensuelles=Decimal(str(charges_mensuelles)),
                depot_garantie=Decimal(str(depot_garantie)),
                statut='actif',
                cree_par=request.user,
            )
            
            # Mettre à jour le statut de l'appartement
            appartement.statut_occupation = 'occupe'
            appartement.save()
            
            messages.success(request, f'Contrat "{contrat.numero_contrat}" créé avec succès!')
            
            return JsonResponse({
                'success': True,
                'message': f'Contrat "{contrat.numero_contrat}" créé avec succès!',
                'contrat_id': contrat.id,
                'numero_contrat': contrat.numero_contrat,
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            })


@login_required
def nouvelle_tache(request):
    """Vue pour créer une nouvelle tâche"""
    return redirect('employees:task_create')


@login_required
def nouvel_employe(request):
    """Vue pour créer un nouvel employé"""
    if request.user.user_type not in ['manager', 'accountant']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Permission refusée'})
        return redirect('dashboard:index')
    
    if request.method == 'GET':
        # Retourner le formulaire HTML pour le modal
        # ✅ Types standardisés - seulement 2 types principaux
        type_employe_choices = [
            ('field_agent', 'Agent de terrain'),
            ('technician', 'Technicien'),
        ]
        
        context = {
            'type_employe_choices': type_employe_choices,
        }
        return render(request, 'dashboard/forms/nouvel_employe.html', context)
    
    elif request.method == 'POST':
        try:
            # Récupération des données
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            user_type = request.POST.get('user_type', 'technician')
            specialite = request.POST.get('specialite', '').strip()
            
            # Validations
            if not all([first_name, last_name, email]):
                raise ValueError("Nom, prénom et email sont obligatoires")
            
            # ✅ Vérifier que le type est valide
            if user_type not in ['field_agent', 'technician']:
                user_type = 'technician'  # Par défaut
            
            # Générer un username unique
            username = f"{first_name.lower()}.{last_name.lower()}"
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Générer un mot de passe temporaire
            import random
            import string
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # Créer l'utilisateur
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                user_type=user_type,
                password=temp_password
            )
            
            # Créer le profil employé si le modèle existe
            try:
                from apps.employees.models.employee import Employee
                employe = Employee.objects.create(
                    user=user,
                    specialite=specialite,
                    statut='actif',
                )
                employe_id = employe.id
            except (ImportError, AttributeError):
                employe_id = user.id
            
            messages.success(request, f'Employé "{user.get_full_name()}" créé avec succès!')
            
            return JsonResponse({
                'success': True,
                'message': f'Employé "{user.get_full_name()}" créé avec succès!',
                'employe_id': employe_id,
                'username': username,
                'password': temp_password,
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la création: {str(e)}'
            })


@login_required
def nouvelle_intervention(request):
    """Vue pour créer une nouvelle intervention"""
    return redirect('maintenance:intervention_create')


@login_required
def nouveau_paiement(request):
    """Vue pour créer un nouveau paiement"""
    return redirect('payments:payment_create')


@login_required
def documents_center(request):
    """Centre de documents"""
    return render(request, 'dashboard/documents.html')


# ============================================================================
# ACTIONS SUR TÂCHES (Redirections vers employees app)
# ============================================================================

@login_required
def task_start_action(request, task_id):
    """Redirection vers l'action de démarrage de tâche"""
    return redirect('employees:task_start', task_id=task_id)


@login_required
def task_complete_action(request, task_id):
    """Redirection vers l'action de complétion de tâche"""
    return redirect('employees:task_complete', task_id=task_id)


@login_required
def task_pause_action(request, task_id):
    """Action de pause d'une tâche (à implémenter dans employees)"""
    messages.info(request, "Fonction pause - À implémenter")
    return redirect('employees:task_detail', task_id=task_id)


@login_required
def task_cancel_action(request, task_id):
    """Action d'annulation d'une tâche (à implémenter dans employees)"""
    messages.info(request, "Fonction annulation - À implémenter")
    return redirect('employees:task_detail', task_id=task_id)


# ============================================================================
# GESTION DES MÉDIAS (Placeholders)
# ============================================================================

@login_required
def upload_media_ajax(request):
    """Upload de média via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    messages.info(request, "Upload de média - À implémenter")
    return JsonResponse({'success': False, 'error': 'Non implémenté'})


@login_required
def delete_media_ajax(request, media_id):
    """Suppression de média via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    return JsonResponse({'success': False, 'error': 'Non implémenté'})


# ============================================================================
# EXPORTS ET RAPPORTS (Placeholders)
# ============================================================================

@login_required
def export_residences(request):
    """Export des résidences en CSV"""
    return JsonResponse({'success': False, 'error': 'Non implémenté'})


@login_required
def export_appartements(request):
    """Export des appartements en CSV"""
    return JsonResponse({'success': False, 'error': 'Non implémenté'})


@login_required
def rapport_occupation(request):
    """Rapport d'occupation"""
    return render(request, 'dashboard/reports/occupation.html')


# ============================================================================
# APIS EMPLOYÉS (Placeholders - logique dans employees app)
# ============================================================================

@login_required
def get_employee_availability(request, employee_id):
    """API pour récupérer la disponibilité d'un employé"""
    return JsonResponse({'success': False, 'error': 'Voir employees app'})


@login_required
def quick_add_task_ajax(request):
    """Ajout rapide de tâche via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    return JsonResponse({'success': False, 'error': 'Voir employees app'})


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_user_permissions(user):
    """Retourne les permissions selon le type d'utilisateur"""
    permissions = {
        'can_create_residence': False,
        'can_create_appartement': False,
        'can_create_contrat': False,
        'can_view_finances': False,
        'can_manage_users': False,
    }
    
    if user.user_type in ['manager', 'accountant']:
        permissions.update({
            'can_create_residence': True,
            'can_create_appartement': True,
            'can_create_contrat': True,
            'can_view_finances': True,
            'can_manage_users': True,
        })
    
    return permissions