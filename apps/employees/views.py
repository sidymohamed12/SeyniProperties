# apps/employees/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, datetime, date
import base64

from apps.employees.models.employee import Employee
from apps.notifications.utils import notify_task_assigned_with_email

# ✅ IMPORTS CORRECTS SELON LES MODÈLES EXISTANTS
from .models.task import Task, TaskMedia
from apps.maintenance.models import Intervention, InterventionMedia
from django.views.decorators.csrf import csrf_exempt

# ✅ FORMS CORRECTS
from .forms import TaskForm, EmployeeForm
from django.urls import reverse, reverse_lazy
from django.core.paginator import Paginator
from apps.properties.models import Property

User = get_user_model()


@login_required
def employees_list_view(request):
    """Liste des employés OU dashboard employé selon le type d'utilisateur - VUE CORRIGÉE"""
    user = request.user
    
    # ✅ CORRECTION: Types d'employés étendus
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    # DEBUG: Afficher les informations utilisateur
    print(f"DEBUG EMPLOYEES - Utilisateur: {user.username}")
    print(f"DEBUG EMPLOYEES - user_type: {user.user_type}")
    print(f"DEBUG EMPLOYEES - est employé: {user.user_type in employee_types}")
    print(f"DEBUG EMPLOYEES - username starts with tech: {user.username.startswith('tech_')}")
    
    # Si c'est un manager ou comptable -> vue liste des employés
    if user.user_type in ['manager', 'accountant']:
        employees = Employee.objects.select_related('user').filter(statut='actif')
        
        context = {
            'employees': employees,
            'total_employees': employees.count(),
            'available_employees': employees.filter(is_available=True).count(),
        }
        
        # Utiliser un template différent pour les managers (créer si nécessaire)
        return render(request, 'employees/manager_list.html', context)
    
    # ✅ CORRECTION: Si c'est un employé OU username commence par tech_ -> rediriger vers dashboard mobile
    elif user.user_type in employee_types or user.username.startswith('tech_'):
        print(f"DEBUG EMPLOYEES - Redirection vers dashboard mobile")
        return redirect('employees_mobile:dashboard')
    
    # Sinon -> redirection vers dashboard général
    else:
        messages.error(request, "Accès non autorisé pour ce type d'utilisateur.")
        return redirect('dashboard:index')


class TasksListView(LoginRequiredMixin, ListView):
    """DEPRECATED: Redirige vers le système Travaux unifié"""
    model = Task

    def dispatch(self, request, *args, **kwargs):
        # Rediriger vers le système Travaux unifié
        messages.info(request, "Le système de tâches a été unifié dans le module Travaux.")
        return redirect('maintenance:travail_list')


@login_required
def task_detail_view(request, task_id):
    """DEPRECATED: Redirige vers le système Travaux unifié ou l'interface mobile"""
    task = get_object_or_404(Task, id=task_id)

    # Rediriger les employés vers l'interface mobile (ils ont encore besoin d'accéder aux tâches existantes)
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']

    if request.user.user_type in employee_types or request.user.username.startswith('tech_'):
        # Vérifier que c'est sa tâche
        if task.assigne_a != request.user:
            messages.error(request, "Vous ne pouvez voir que vos propres tâches.")
            return redirect('employees_mobile:tasks')
        return redirect('employees_mobile:task_detail', task_id=task_id)

    # Managers/comptables sont redirigés vers le système Travaux
    messages.info(request, "Le système de tâches a été unifié dans le module Travaux.")
    return redirect('maintenance:travail_list')


@login_required
@require_http_methods(["POST"])
def task_start(request, task_id):
    """Démarrer une tâche - VERSION SIMPLIFIÉE SANS MÉTHODES MODÈLE - VUE CORRIGÉE"""
    task = get_object_or_404(Task, id=task_id)
    
    # ✅ CORRECTION: Vérifications de permissions
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if request.user.user_type in employee_types or request.user.username.startswith('tech_'):
        # Les employés ne peuvent démarrer que leurs propres tâches
        if task.assigne_a != request.user:
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    elif request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    
    if task.statut != 'planifie':
        return JsonResponse({'success': False, 'error': 'Tâche non démarrable'}, status=400)
    
    # ✅ DÉMARRER LA TÂCHE SANS start_task()
    task.statut = 'en_cours'
    task.date_debut = timezone.now()
    task.save()
    
    messages.success(request, f"Tâche '{task.titre}' démarrée!")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Tâche démarrée!'})
    
    return redirect('employees:task_detail', task_id=task.id)


@login_required
@require_http_methods(["GET", "POST"])
def task_complete(request, task_id):
    """Terminer une tâche - VERSION SIMPLIFIÉE - VUE CORRIGÉE"""
    task = get_object_or_404(Task, id=task_id)
    
    # ✅ CORRECTION: Vérifications de permissions
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if request.user.user_type in employee_types or request.user.username.startswith('tech_'):
        # Les employés ne peuvent terminer que leurs propres tâches
        if task.assigne_a != request.user:
            messages.error(request, "Vous n'êtes pas autorisé à terminer cette tâche.")
            return redirect('employees_mobile:tasks')
    elif request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de terminer cette tâche.")
        return redirect('dashboard:index')
    
    if task.statut != 'en_cours':
        messages.error(request, "Cette tâche ne peut pas être terminée dans son état actuel.")
        if request.user.user_type in employee_types:
            return redirect('employees_mobile:task_detail', task_id=task.id)
        else:
            return redirect('employees:task_detail', task_id=task.id)
    
    if request.method == 'GET':
        # ✅ FORMULAIRE SIMPLE SANS TaskCompletionForm
        template = 'employees/mobile/task_complete_form.html' if request.user.user_type in employee_types else 'employees/task_complete_form.html'
        return render(request, template, {
            'task': task,
        })
    
    elif request.method == 'POST':
        # ✅ TRAITEMENT MANUEL SANS FORM
        commentaire = request.POST.get('commentaire', '')
        temps_passe = request.POST.get('temps_passe')
        
        # Terminer la tâche
        task.statut = 'complete'
        task.date_fin = timezone.now()
        task.commentaire = commentaire
        
        if temps_passe:
            try:
                task.temps_passe = int(temps_passe)
            except ValueError:
                pass
        
        task.save()
        
        # ✅ CRÉER RÉCURRENCE MANUELLEMENT SI NÉCESSAIRE
        if task.is_recurrente:
            create_recurrent_task_manual(task)
        
        messages.success(request, f"Tâche '{task.titre}' terminée avec succès!")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Tâche terminée!',
                'redirect_url': reverse('employees_mobile:tasks') if request.user.user_type in employee_types else reverse('employees:tasks')
            })
        
        if request.user.user_type in employee_types:
            return redirect('employees_mobile:tasks')
        else:
            return redirect('employees:tasks')


def create_recurrent_task_manual(task):
    """Créer la prochaine occurrence d'une tâche récurrente - FONCTION MANUELLE"""
    if not task.is_recurrente or not task.recurrence_type:
        return
    
    # Calculer la prochaine date
    if task.recurrence_type == 'quotidien':
        next_date = task.date_prevue + timedelta(days=1)
    elif task.recurrence_type == 'hebdomadaire':
        next_date = task.date_prevue + timedelta(weeks=1)
    elif task.recurrence_type == 'mensuel':
        next_date = task.date_prevue + timedelta(days=30)
    else:
        return
    
    # Vérifier si on n'a pas dépassé la date de fin
    if task.recurrence_fin and next_date.date() > task.recurrence_fin:
        return
    
    # Créer la nouvelle tâche
    Task.objects.create(
        titre=task.titre,
        description=task.description,
        type_tache=task.type_tache,
        bien=task.bien,
        assigne_a=task.assigne_a,
        cree_par=task.cree_par,
        date_prevue=next_date,
        duree_estimee=task.duree_estimee,
        priorite=task.priorite,
        is_recurrente=task.is_recurrente,
        recurrence_type=task.recurrence_type,
        recurrence_fin=task.recurrence_fin,
    )


@login_required
def planning_view(request):
    """Vue du planning des tâches - VUE CORRIGÉE"""
    # ✅ CORRECTION: Rediriger les employés vers l'interface mobile
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if request.user.user_type in employee_types or request.user.username.startswith('tech_'):
        return redirect('employees_mobile:dashboard')
    
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
        return redirect('dashboard:index')
    
    # Récupérer les tâches de la semaine
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    tasks = Task.objects.filter(
        date_prevue__date__range=[start_week, end_week]
    ).select_related('assigne_a', 'bien').order_by('date_prevue')
    
    # Organiser par jour
    planning_data = {}
    for i in range(7):
        day = start_week + timedelta(days=i)
        planning_data[day] = tasks.filter(date_prevue__date=day)
    
    context = {
        'planning_data': planning_data,
        'current_week_start': start_week,
        'current_week_end': end_week,
    }
    
    return render(request, 'employees/planning.html', context)


@login_required
def tasks_calendar_api(request):
    """API pour récupérer les tâches au format calendrier - VUE CORRIGÉE"""
    # ✅ CORRECTION: Gérer les permissions selon le type d'utilisateur
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in ['manager', 'accountant'] or 
            request.user.user_type in employee_types or 
            request.user.username.startswith('tech_')):
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    tasks_query = Task.objects.select_related('assigne_a', 'bien')
    
    # Si employé, ne voir que ses tâches
    if request.user.user_type in employee_types or request.user.username.startswith('tech_'):
        tasks_query = tasks_query.filter(assigne_a=request.user)
    
    if start_date and end_date:
        tasks_query = tasks_query.filter(
            date_prevue__date__range=[start_date, end_date]
        )
    
    events = []
    for task in tasks_query:
        # Couleurs selon le statut
        color_map = {
            'planifie': '#3B82F6',    # Bleu
            'en_cours': '#F59E0B',    # Orange
            'complete': '#10B981',    # Vert
            'annule': '#EF4444',      # Rouge
        }
        
        events.append({
            'id': task.id,
            'title': task.titre,
            'start': task.date_prevue.isoformat(),
            'end': (task.date_prevue + timedelta(minutes=task.duree_estimee or 60)).isoformat(),
            'color': color_map.get(task.statut, '#6B7280'),
            'extendedProps': {
                'status': task.statut,
                'priority': task.priorite,
                'employee': task.assigne_a.get_full_name(),
                'property': task.bien.name if task.bien else None,
                'type': task.type_tache,
            }
        })
    
    return JsonResponse(events, safe=False)


@login_required
def task_stats_api(request):
    """API pour les statistiques des tâches - VUE CORRIGÉE"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    # Statistiques par employé
    employee_stats = Task.objects.values(
        'assigne_a__first_name', 'assigne_a__last_name'
    ).annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(statut='complete')),
        pending=Count('id', filter=Q(statut='planifie')),
        in_progress=Count('id', filter=Q(statut='en_cours'))
    )
    
    # Statistiques par type de tâche
    type_stats = Task.objects.values('type_tache').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Performance cette semaine
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    weekly_performance = Task.objects.filter(
        date_prevue__date__range=[start_week, end_week]
    ).aggregate(
        planned=Count('id'),
        completed=Count('id', filter=Q(statut='complete')),
        completion_rate=Avg('duree_estimee')
    )
    
    return JsonResponse({
        'employee_stats': list(employee_stats),
        'type_stats': list(type_stats),
        'weekly_performance': weekly_performance,
    })


@login_required
def employee_detail_view(request, employee_id):
    """Détail d'un employé - VUE CORRIGÉE"""
    employee = get_object_or_404(Employee, id=employee_id)

    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
        return redirect('dashboard:index')

    # Récupérer les travaux (interventions) assignés
    from apps.maintenance.models import Intervention
    travaux_assignes = Intervention.objects.filter(
        technicien=employee.user
    ).select_related('appartement__residence').order_by('-date_signalement')

    # Statistiques des travaux
    travaux_stats = {
        'total': travaux_assignes.count(),
        'signale': travaux_assignes.filter(statut='signale').count(),
        'assigne': travaux_assignes.filter(statut='assigne').count(),
        'en_cours': travaux_assignes.filter(statut='en_cours').count(),
        'termine': travaux_assignes.filter(statut='termine').count(),
    }

    # Statistiques de l'employé (anciennes tâches)
    stats = {
        'total_tasks': Task.objects.filter(assigne_a=employee.user).count(),
        'completed_tasks': Task.objects.filter(assigne_a=employee.user, statut='complete').count(),
        'pending_tasks': Task.objects.filter(assigne_a=employee.user, statut='planifie').count(),
        'in_progress_tasks': Task.objects.filter(assigne_a=employee.user, statut='en_cours').count(),
    }

    # Tâches récentes
    recent_tasks = Task.objects.filter(
        assigne_a=employee.user
    ).order_by('-date_prevue')[:10]

    context = {
        'employee': employee,
        'stats': stats,
        'recent_tasks': recent_tasks,
        'travaux_assignes': travaux_assignes[:20],  # 20 travaux les plus récents
        'travaux_stats': travaux_stats,
    }

    return render(request, 'employees/employee_detail.html', context)


@login_required
def employee_create_view(request):
    """Créer un nouvel employé"""
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des employés.")
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()

            # Récupérer les identifiants générés
            credentials = employee._login_credentials if hasattr(employee, '_login_credentials') else None

            if credentials:
                messages.success(
                    request,
                    f"Employé {employee.user.get_full_name()} créé avec succès! "
                    f"Identifiants: {credentials['username']} / {credentials['password']}"
                )
            else:
                messages.success(request, f"Employé {employee.user.get_full_name()} créé avec succès!")

            return redirect('employees:employee_detail', employee_id=employee.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = EmployeeForm()

    context = {
        'form': form,
        'title': 'Nouvel employé',
    }

    return render(request, 'employees/employee_form.html', context)


class TaskCreateView(LoginRequiredMixin, CreateView):
    """DEPRECATED: Redirige vers le système Travaux unifié"""
    model = Task

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Le système de tâches a été unifié dans le module Travaux. Créez un nouveau travail à la place.")
        return redirect('maintenance:travail_create')


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """DEPRECATED: Redirige vers le système Travaux unifié"""
    model = Task
    pk_url_kwarg = 'task_id'

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Le système de tâches a été unifié dans le module Travaux.")
        return redirect('maintenance:travail_list')


@login_required
def task_delete_view(request, task_id):
    """DEPRECATED: Redirige vers le système Travaux unifié"""
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer des travaux.")
        return redirect('dashboard:index')

    messages.info(request, "Le système de tâches a été unifié dans le module Travaux.")
    return redirect('maintenance:travail_list')


# ============ VUES MOBILES SIMPLIFIÉES - CORRIGÉES ============

@login_required
def employee_dashboard_mobile(request):
    """Dashboard mobile pour employés - Utilise le modèle Travail unifié"""
    from django.utils import timezone
    from django.urls import reverse
    from datetime import date, timedelta
    from apps.maintenance.models import Travail

    today = date.today()
    now = timezone.now()

    # Récupérer TOUS les travaux assignés à l'utilisateur
    user_travaux = Travail.objects.filter(
        assigne_a=request.user
    ).select_related(
        'appartement',
        'appartement__residence',
        'residence'
    ).order_by('-date_prevue', '-priorite')

    # UNIFICATION: Créer une liste de travaux pour affichage
    today_work = []
    upcoming_work = []

    # Traiter tous les travaux
    for travail in user_travaux:
        # Déterminer le nom du bien
        bien_nom = ''
        if travail.appartement:
            bien_nom = f"{travail.appartement.residence.nom} - {travail.appartement.nom}"
        elif travail.residence:
            bien_nom = travail.residence.nom

        work_item = {
            'id': travail.id,
            'type': 'travail',
            'numero': travail.numero_travail,
            'titre': travail.titre,
            'description': travail.description or '',
            'statut': travail.statut,
            'statut_display': travail.get_statut_display(),
            'priorite': travail.priorite,
            'priorite_display': travail.get_priorite_display(),
            'type_travail': travail.type_travail,
            'type_travail_display': travail.get_type_travail_display(),
            'bien_nom': bien_nom,
            'appartement': travail.appartement,
            'residence': travail.residence,
            'date_prevue': travail.date_prevue,
            'cout_estime': travail.cout_estime,
            'detail_url': reverse('employees_mobile:travail_detail', args=[travail.id]),
            'heure_affichage': travail.date_prevue.strftime('%H:%M') if travail.date_prevue else '',
            'date_affichage': travail.date_prevue.strftime('%d/%m à %H:%M') if travail.date_prevue else 'Non planifié',
        }

        # Classer selon la date et le statut
        if travail.statut in ['assigne', 'en_cours']:
            # Travaux en cours ou assignés = aujourd'hui
            today_work.append(work_item)
        elif travail.statut == 'signale':
            # Travaux signalés = à venir
            upcoming_work.append(work_item)
        elif travail.date_prevue:
            # Sinon classer selon la date
            if travail.date_prevue.date() == today:
                today_work.append(work_item)
            elif travail.date_prevue.date() > today:
                upcoming_work.append(work_item)
    
    # Trier les listes
    today_work.sort(key=lambda x: (
        x.get('date_prevue') or timezone.now(),
        x['priorite'] == 'urgente',
        x['priorite'] == 'haute'
    ))

    upcoming_work.sort(key=lambda x: (
        x.get('date_prevue') or timezone.now(),
        x['priorite'] == 'urgente',
        x['priorite'] == 'haute'
    ))

    # STATISTIQUES BASÉES SUR LE MODÈLE TRAVAIL
    total_pending = user_travaux.filter(statut__in=['signale', 'assigne']).count()
    total_in_progress = user_travaux.filter(statut='en_cours').count()
    total_completed_today = user_travaux.filter(
        statut='termine',
        date_fin__date=today
    ).count()

    # Travaux en retard (date prévue dépassée et pas encore terminés)
    total_overdue = user_travaux.filter(
        statut__in=['signale', 'assigne', 'en_cours'],
        date_prevue__lt=now
    ).count()

    # Nombre de travaux à venir
    upcoming_count = len(upcoming_work)
    
    context = {
        # DONNÉES UNIFIÉES
        'today_work': today_work,
        'upcoming_work': upcoming_work[:5],  # Limiter à 5 pour l'affichage
        
        # STATISTIQUES GLOBALES
        'total_pending': total_pending,
        'total_in_progress': total_in_progress,
        'total_completed_today': total_completed_today,
        'total_overdue': total_overdue,
        'upcoming_count': upcoming_count,
        
        # INFOS UTILISATEUR
        'user': request.user,
        'current_time': now,
        'today_date': today,
    }
    
    return render(request, 'employees/mobile/dashboard.html', context)


@login_required
def travail_detail_mobile(request, travail_id):
    """Vue détail d'un travail pour le portail mobile employé"""
    from apps.maintenance.models import Travail, TravailMedia, TravailChecklist
    from django.urls import reverse

    # Récupérer le travail
    travail = get_object_or_404(
        Travail.objects.select_related(
            'appartement__residence',
            'residence',
            'assigne_a',
            'cree_par'
        ),
        id=travail_id
    )

    # Vérifier que l'utilisateur est bien assigné à ce travail
    if travail.assigne_a != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à voir ce travail.")
        return redirect('employees_mobile:dashboard')

    # Récupérer les médias et checklist
    medias = TravailMedia.objects.filter(travail=travail).order_by('-created_at')
    checklist_items = TravailChecklist.objects.filter(travail=travail).order_by('ordre', 'id')

    # Calculer la progression de la checklist
    total_checklist = checklist_items.count()
    completed_checklist = checklist_items.filter(is_completed=True).count()
    checklist_progress = (completed_checklist / total_checklist * 100) if total_checklist > 0 else 0

    # Déterminer le nom du bien
    bien_nom = ''
    bien_adresse = ''
    if travail.appartement:
        bien_nom = f"{travail.appartement.residence.nom} - {travail.appartement.nom}"
        bien_adresse = travail.appartement.residence.adresse if hasattr(travail.appartement.residence, 'adresse') else ''
    elif travail.residence:
        bien_nom = travail.residence.nom
        bien_adresse = travail.residence.adresse if hasattr(travail.residence, 'adresse') else ''

    # Actions disponibles selon le statut
    can_start = travail.statut in ['signale', 'assigne']
    can_pause = travail.statut == 'en_cours'
    can_complete = travail.statut == 'en_cours'
    can_reopen = travail.statut == 'termine'

    context = {
        'travail': travail,
        'bien_nom': bien_nom,
        'bien_adresse': bien_adresse,
        'medias': medias,
        'checklist_items': checklist_items,
        'total_checklist': total_checklist,
        'completed_checklist': completed_checklist,
        'checklist_progress': checklist_progress,
        'can_start': can_start,
        'can_pause': can_pause,
        'can_complete': can_complete,
        'can_reopen': can_reopen,
    }

    return render(request, 'employees/mobile/travail_detail.html', context)


@login_required
def travail_start_mobile(request, travail_id):
    """Démarrer un travail"""
    from apps.maintenance.models import Travail

    travail = get_object_or_404(Travail, id=travail_id, assigne_a=request.user)

    if travail.statut in ['signale', 'assigne']:
        travail.statut = 'en_cours'
        travail.date_debut = timezone.now()
        travail.save()
        messages.success(request, f"Travail '{travail.titre}' démarré!")
    else:
        messages.warning(request, "Ce travail ne peut pas être démarré dans son état actuel.")

    return redirect('employees_mobile:travail_detail', travail_id=travail_id)


@login_required
def travail_complete_mobile(request, travail_id):
    """Terminer un travail avec rapport et photos"""
    from apps.maintenance.models import Travail, TravailMedia

    travail = get_object_or_404(Travail, id=travail_id, assigne_a=request.user)

    if request.method == 'POST':
        if travail.statut == 'en_cours':
            # Récupérer les données du formulaire
            notes = request.POST.get('notes', '').strip()
            temps_passe = request.POST.get('temps_passe', '')

            # Validation du rapport
            if not notes or len(notes) < 20:
                messages.error(request, "Le rapport doit contenir au moins 20 caractères.")
                return redirect('employees_mobile:travail_complete', travail_id=travail_id)

            # Mettre à jour le travail
            travail.statut = 'termine'
            travail.date_fin = timezone.now()
            travail.notes_completion = notes

            # Temps passé (optionnel)
            if temps_passe:
                try:
                    travail.temps_passe = float(temps_passe)
                except ValueError:
                    pass  # Ignorer si valeur invalide

            travail.save()

            # Gérer les photos uploadées
            photos = request.FILES.getlist('photos')
            for photo in photos:
                TravailMedia.objects.create(
                    travail=travail,
                    file=photo,
                    uploaded_by=request.user,
                    description=f"Photo de fin de travail - {travail.titre}"
                )

            messages.success(request, f"Travail '{travail.titre}' terminé avec succès!")
            return redirect('employees_mobile:dashboard')
        else:
            messages.warning(request, "Ce travail ne peut pas être terminé dans son état actuel.")
            return redirect('employees_mobile:travail_detail', travail_id=travail_id)

    # GET: afficher le formulaire de complétion
    context = {
        'travail': travail,
    }
    return render(request, 'employees/mobile/travail_complete_form.html', context)


@login_required
def travail_checklist_toggle(request, travail_id, checklist_id):
    """Toggle une checklist item"""
    from apps.maintenance.models import Travail, TravailChecklist

    if request.method == 'POST':
        travail = get_object_or_404(Travail, id=travail_id, assigne_a=request.user)
        checklist_item = get_object_or_404(TravailChecklist, id=checklist_id, travail=travail)

        # Toggle l'état
        checklist_item.is_completed = not checklist_item.is_completed
        if checklist_item.is_completed:
            checklist_item.completed_by = request.user
            checklist_item.date_completion = timezone.now()
        else:
            checklist_item.completed_by = None
            checklist_item.date_completion = None
        checklist_item.save()

        return JsonResponse({
            'success': True,
            'is_completed': checklist_item.is_completed,
            'message': 'Tâche mise à jour'
        })

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@login_required
def travail_demande_materiel(request, travail_id):
    """
    Formulaire mobile simplifié pour qu'un employé demande du matériel pour un travail
    """
    from apps.maintenance.models import Travail
    from apps.payments.models import Invoice, LigneDemandeAchat, HistoriqueValidation
    from decimal import Decimal
    import re

    travail = get_object_or_404(Travail, id=travail_id, assigne_a=request.user)

    if request.method == 'POST':
        motif_principal = request.POST.get('motif_principal', '').strip()

        if not motif_principal:
            messages.error(request, 'Le motif est obligatoire')
            return redirect('employees_mobile:travail_demande_materiel', travail_id=travail_id)

        # Parser les articles depuis le formulaire
        articles = []
        post_data = request.POST

        # Trouver tous les indices d'articles
        pattern = re.compile(r'articles\[(\d+)\]\[designation\]')
        indices = set()
        for key in post_data.keys():
            match = pattern.match(key)
            if match:
                indices.add(int(match.group(1)))

        # Extraire les données de chaque article
        for idx in sorted(indices):
            designation = post_data.get(f'articles[{idx}][designation]', '').strip()
            quantite = post_data.get(f'articles[{idx}][quantite]', '').strip()
            unite = post_data.get(f'articles[{idx}][unite]', 'unité').strip()
            prix_estime = post_data.get(f'articles[{idx}][prix_estime]', '0').strip()
            fournisseur = post_data.get(f'articles[{idx}][fournisseur]', '').strip()

            if designation and quantite:
                try:
                    articles.append({
                        'designation': designation,
                        'quantite': Decimal(quantite),
                        'unite': unite or 'unité',
                        'prix_unitaire': Decimal(prix_estime) if prix_estime else Decimal('0'),
                        'fournisseur': fournisseur,
                        'motif': motif_principal
                    })
                except (ValueError, Decimal.InvalidOperation):
                    pass

        if not articles:
            messages.error(request, 'Veuillez ajouter au moins un article')
            return redirect('employees_mobile:travail_demande_materiel', travail_id=travail_id)

        # Utiliser la méthode du modèle Travail pour créer la demande
        try:
            demande = travail.creer_demande_achat(
                demandeur=request.user,
                service_fonction=f"{request.user.get_user_type_display()}",
                motif_principal=motif_principal,
                articles=articles
            )

            # Notification de succès
            messages.success(
                request,
                f'Demande de matériel {demande.numero_facture} créée avec succès! '
                f'Elle sera envoyée à votre responsable pour validation.'
            )

            # Rediriger vers le détail du travail
            return redirect('employees_mobile:travail_detail', travail_id=travail.id)

        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la demande: {str(e)}')
            return redirect('employees_mobile:travail_demande_materiel', travail_id=travail_id)

    # GET - Afficher le formulaire
    context = {
        'travail': travail,
    }

    return render(request, 'employees/mobile/travail_demande_materiel.html', context)


@login_required
def confirmer_reception_materiel(request, demande_id):
    """
    L'employé confirme avoir reçu le matériel sur le terrain
    Déclenche le déblocage du travail si tout le matériel est reçu
    """
    from apps.payments.models import Invoice, HistoriqueValidation
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    demande = get_object_or_404(
        Invoice,
        id=demande_id,
        type_facture='demande_achat'
    )

    travail = demande.travail_lie
    if not travail:
        return JsonResponse({'success': False, 'error': 'Aucun travail lié'}, status=400)

    # Vérifier que c'est bien l'employé assigné au travail
    if travail.assigne_a != request.user:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

    # Vérifier que la demande est payée mais pas encore réceptionnée
    if demande.etape_workflow != 'paye':
        return JsonResponse({
            'success': False,
            'error': f'Demande en statut {demande.get_etape_workflow_display()}. Doit être payée pour être réceptionnée.'
        }, status=400)

    # Marquer comme reçue
    demande.etape_workflow = 'recue'
    demande.date_reception = timezone.now()
    demande.receptionne_par = request.user

    # Remarques optionnelles
    remarques = request.POST.get('remarques', '').strip()
    if remarques:
        demande.remarques_reception = remarques

    demande.save()

    # Créer l'historique
    HistoriqueValidation.objects.create(
        demande=demande,
        action='reception',
        effectue_par=request.user,
        commentaire=f"Matériel réceptionné sur site par {request.user.get_full_name()}"
    )

    # ✅ LOGIQUE DE DÉBLOCAGE AUTOMATIQUE
    # Vérifier si TOUT le matériel du travail est maintenant reçu
    statut_materiel = travail.statut_materiel

    if statut_materiel == 'materiel_recu':
        # Tout le matériel est reçu → débloquer le travail
        ancien_statut = travail.statut
        travail.statut = 'en_cours'  # ✅ Passer en cours (plus logique que 'assigne')

        # Si le travail n'avait pas encore de date de début, la définir maintenant
        if not travail.date_debut_reel:
            travail.date_debut_reel = timezone.now()

        travail.save()

        messages.success(
            request,
            f'✅ Matériel confirmé ! Tout le matériel est reçu. '
            f'Le travail est maintenant en cours, vous pouvez continuer.'
        )

        return JsonResponse({
            'success': True,
            'message': 'Matériel confirmé ! Travail débloqué.',
            'travail_debloque': True,
            'ancien_statut': ancien_statut,
            'nouveau_statut': travail.statut,
            'statut_materiel': statut_materiel
        })
    else:
        # Il reste d'autres demandes en attente
        messages.info(
            request,
            f'Matériel confirmé. En attente de {travail.demandes_achat.exclude(etape_workflow="recue").count()} autre(s) commande(s).'
        )

        return JsonResponse({
            'success': True,
            'message': 'Matériel confirmé. En attente des autres commandes.',
            'travail_debloque': False,
            'statut_materiel': statut_materiel,
            'demandes_restantes': travail.demandes_achat.exclude(etape_workflow='recue').count()
        })


@login_required
def my_tasks_mobile(request):
    """
    Vue unifiée des travaux mobile - UTILISE MODÈLE TRAVAIL UNIFIÉ
    """
    from apps.maintenance.models import Travail
    from django.urls import reverse

    user = request.user

    # Récupération des paramètres
    tab = request.GET.get('tab', 'all')
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    type_filter = request.GET.get('type', 'all')
    page = request.GET.get('page', 1)

    # Obtenir les travaux de l'utilisateur avec le modèle Travail unifié
    travaux = Travail.objects.filter(
        assigne_a=user
    ).select_related(
        'appartement__residence',
        'residence'
    ).order_by('-date_prevue', '-priorite')

    # Unification des données
    work_list = []

    # Traitement des travaux
    for travail in travaux:
        # Déterminer le nom du bien
        bien_nom = ''
        if travail.appartement:
            bien_nom = f"{travail.appartement.residence.nom} - {travail.appartement.nom}"
        elif travail.residence:
            bien_nom = travail.residence.nom

        work_item = {
            'id': travail.id,
            'type': 'travail',  # Type unifié
            'numero': travail.numero_travail,
            'titre': travail.titre,
            'title': travail.titre,  # Compatibilité template
            'description': travail.description,
            'statut': travail.statut,
            'status': travail.statut,  # Compatibilité
            'status_display': travail.get_statut_display(),
            'get_statut_display': travail.get_statut_display(),
            'priorite': travail.priorite,
            'priority': travail.priorite,  # Compatibilité
            'priority_display': travail.get_priorite_display(),
            'get_priorite_display': travail.get_priorite_display(),
            'type_travail': travail.type_travail,
            'type_travail_display': travail.get_type_travail_display(),
            'date_prevue': travail.date_prevue,
            'scheduled_date': travail.date_prevue,
            'scheduled_display': travail.date_prevue.strftime('%d/%m à %H:%M') if travail.date_prevue else '',
            'bien_nom': bien_nom,
            'property_name': bien_nom,  # Compatibilité
            'relative_time': _calculate_relative_time(travail.date_prevue) if travail.date_prevue else '',
            'is_overdue': travail.date_prevue < timezone.now() if travail.date_prevue and travail.statut in ['signale', 'assigne', 'en_cours'] else False,
            'detail_url': reverse('employees_mobile:travail_detail', args=[travail.id]),
            'created_at': travail.created_at if hasattr(travail, 'created_at') else travail.date_prevue
        }
        work_list.append(work_item)

    # Application des filtres
    work_list = _apply_work_filters(work_list, tab, status_filter, priority_filter, type_filter)

    # Tri par date (les plus récents/urgents en premier)
    work_list.sort(key=lambda x: x['scheduled_date'] or x['created_at'] or timezone.now(), reverse=False)

    # Calcul des statistiques
    today = date.today()
    total_work_count = len(work_list)
    today_work_count = len([w for w in work_list if w['scheduled_date'] and w['scheduled_date'].date() == today])
    pending_work_count = len([w for w in work_list if w['statut'] in ['signale', 'assigne']])
    in_progress_count = len([w for w in work_list if w['statut'] == 'en_cours'])

    # Pagination
    paginator = Paginator(work_list, 10)
    page_obj = paginator.get_page(page)

    context = {
        'page_obj': page_obj,
        'current_tab': tab,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'type': type_filter,
        },
        'total_work_count': total_work_count,
        'today_work_count': today_work_count,
        'pending_work_count': pending_work_count,
        'in_progress_count': in_progress_count,
    }

    return render(request, 'employees/mobile/work_list.html', context)


def _apply_work_filters(work_list, tab, status_filter, priority_filter, type_filter):
    """
    Applique les filtres sur la liste unifiée des travaux - UTILISE MODÈLE TRAVAIL
    """
    filtered_list = work_list.copy()

    # Filtre par onglet
    if tab == 'today':
        today = date.today()
        filtered_list = [work for work in filtered_list
                        if work['scheduled_date'] and work['scheduled_date'].date() == today]
    elif tab == 'pending':
        # Travail: statuts en attente sont 'signale' et 'assigne'
        filtered_list = [work for work in filtered_list
                        if work['statut'] in ['signale', 'assigne']]
    elif tab == 'in_progress':
        filtered_list = [work for work in filtered_list
                        if work['statut'] == 'en_cours']
    elif tab == 'completed':
        filtered_list = [work for work in filtered_list
                        if work['statut'] == 'termine']

    # Filtre par type de travail
    if type_filter != 'all':
        filtered_list = [work for work in filtered_list if work.get('type_travail') == type_filter]

    # Filtre par statut
    if status_filter != 'all':
        statuses = status_filter.split(',')
        filtered_list = [work for work in filtered_list if work['statut'] in statuses]

    # Filtre par priorité
    if priority_filter != 'all':
        priorities = priority_filter.split(',')
        filtered_list = [work for work in filtered_list if work['priorite'] in priorities]

    return filtered_list


def _calculate_relative_time(date_time):
    """
    Calcule le temps relatif par rapport à maintenant
    """
    if not date_time:
        return ''
    
    now = timezone.now()
    diff = date_time - now
    
    if diff.total_seconds() > 0:
        # Dans le futur
        if diff.days > 0:
            return f"dans {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"dans {hours}h"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"dans {minutes}min"
        else:
            return "bientôt"
    else:
        # Dans le passé
        diff = now - date_time
        if diff.days > 0:
            return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"il y a {hours}h"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"il y a {minutes}min"
        else:
            return "à l'instant"


@login_required
def task_detail_mobile(request, task_id):
    """Détail d'une tâche - Vue mobile avec actions - VUE CORRIGÉE"""
    task = get_object_or_404(Task, id=task_id)
    
    # ✅ CORRECTION: Accepter tous les types d'employés ET tech_
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        messages.error(request, "Accès réservé aux employés.")
        return redirect('dashboard:index')
    
    if task.assigne_a != request.user:
        messages.error(request, "Vous ne pouvez voir que vos propres tâches.")
        return redirect('employees_mobile:tasks')
    
    # Médias associés
    medias = TaskMedia.objects.filter(task=task).order_by('-created_at')
    
    # Historique simplifié
    history = []
    if task.date_debut:
        history.append({
            'date': task.date_debut,
            'action': 'Tâche démarrée',
            'icon': 'play',
            'color': 'blue'
        })
    if task.date_fin:
        history.append({
            'date': task.date_fin,
            'action': 'Tâche terminée',
            'icon': 'check',
            'color': 'green'
        })
    
    context = {
        'task': task,
        'medias': medias,
        'history': history,
        'can_start': task.statut == 'planifie',
        'can_complete': task.statut == 'en_cours',
        'can_upload': task.statut in ['en_cours', 'complete'],
    }
    
    return render(request, 'employees/mobile/task_detail.html', context)


@login_required
@require_http_methods(["POST"])
def task_start_mobile(request, task_id):
    """Démarrer une tâche depuis l'interface mobile - VUE CORRIGÉE"""
    task = get_object_or_404(Task, id=task_id)
    
    # ✅ CORRECTION: Accepter tous les types d'employés ET tech_
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    
    if task.assigne_a != request.user:
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    
    if task.statut != 'planifie':
        return JsonResponse({
            'success': False, 
            'error': 'Cette tâche ne peut pas être démarrée'
        })
    
    try:
        # ✅ DÉMARRER MANUELLEMENT SANS start_task()
        task.statut = 'en_cours'
        task.date_debut = timezone.now()
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Tâche démarrée avec succès !',
            'new_status': 'en_cours',
            'status_text': 'En cours',
            'status_color': 'orange'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def task_complete_mobile(request, task_id):
    """Terminer une tâche depuis l'interface mobile - VUE CORRIGÉE"""
    task = get_object_or_404(Task, id=task_id)
    
    # Vérifier les permissions
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    
    if task.assigne_a != request.user:
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    
    if task.statut != 'en_cours':
        return JsonResponse({
            'success': False, 
            'error': 'Cette tâche ne peut pas être terminée'
        })
    
    try:
        commentaire = request.POST.get('commentaire', '').strip()
        
        # CORRECTION: Vérifier si un commentaire existe déjà OU si un nouveau est fourni
        commentaire_existant = task.commentaire if hasattr(task, 'commentaire') and task.commentaire else ''
        
        # Si aucun commentaire existant ET aucun nouveau commentaire
        if not commentaire_existant and not commentaire:
            return JsonResponse({
                'success': False,
                'error': 'Un rapport est obligatoire pour terminer cette tâche. Veuillez d\'abord rédiger un rapport.'
            })
        
        # Terminer la tâche
        task.statut = 'complete'
        task.date_fin = timezone.now()
        
        # Utiliser le nouveau commentaire s'il existe, sinon garder l'ancien
        if commentaire:
            task.commentaire = commentaire
        
        task.save()
        
        # Créer récurrence si nécessaire
        if hasattr(task, 'is_recurrente') and task.is_recurrente:
            create_recurrent_task_manual(task)
        
        return JsonResponse({
            'success': True,
            'message': 'Tâche terminée avec succès !',
            'new_status': 'complete',
            'status_text': 'Terminée',
            'status_color': 'green'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ PWA SUPPORT ============


@login_required
def get_employee_sync_data(request):
    """API pour données offline PWA - VUE AJOUTÉE"""
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from apps.maintenance.models import Intervention
    
    # Données essentielles pour fonctionnement offline
    today = timezone.now().date()
    
    # ✅ INTERVENTIONS ASSIGNÉES À CET EMPLOYÉ
    interventions = Intervention.objects.filter(
        technicien=request.user,
        statut__in=['assigne', 'en_cours']
    ).select_related('bien')
    
    interventions_data = []
    for intervention in interventions:
        interventions_data.append({
            'id': intervention.id,
            'numero_intervention': getattr(intervention, 'numero_intervention', f'INT-{intervention.id}'),
            'titre': intervention.titre,
            'description': intervention.description,
            'type_intervention': intervention.type_intervention,
            'priorite': intervention.priorite,
            'statut': intervention.statut,
            'date_signalement': intervention.date_signalement.isoformat(),
            'date_assignation': intervention.date_assignation.isoformat() if intervention.date_assignation else None,
            'bien_nom': intervention.bien.name if intervention.bien else None,
            'bien_adresse': getattr(intervention.bien, 'address', None) if intervention.bien else None,
        })
    
    # Tâches des 7 prochains jours
    end_date = today + timedelta(days=7)
    tasks = Task.objects.filter(
        assigne_a=request.user,
        date_prevue__date__range=[today, end_date]
    ).select_related('bien')
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'titre': task.titre,
            'description': task.description,
            'type_tache': task.type_tache,
            'priorite': task.priorite,
            'statut': task.statut,
            'date_prevue': task.date_prevue.isoformat(),
            'bien_nom': task.bien.name if task.bien else None,
            'bien_adresse': getattr(task.bien, 'address', None) if task.bien else None,
            'duree_estimee': task.duree_estimee,
        })
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'user_type': request.user.user_type,
        },
        'interventions': interventions_data,
        'tasks': tasks_data,
        'sync_timestamp': timezone.now().isoformat(),
    })


# ✅ AJOUTER LES VUES PWA MANQUANTES

def pwa_manifest(request):
    """Manifeste PWA pour l'application mobile"""
    manifest = {
        "name": "Seyni Properties - Employés",
        "short_name": "Seyni Employés",
        "description": "Application mobile pour les employés de Seyni Properties",
        "start_url": "/employees/mobile/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#3b82f6",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/images/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["productivity", "business"],
        "lang": "fr"
    }
    
    return JsonResponse(manifest)


def service_worker(request):
    """Service Worker pour le fonctionnement offline"""
    sw_content = """
const CACHE_NAME = 'seyni-employees-v1';
const urlsToCache = [
    '/employees/mobile/',
    '/employees/mobile/tasks/',
    '/static/css/tailwind.css',
    '/static/js/app.js',
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});
"""
    
    return HttpResponse(sw_content, content_type='application/javascript')


# ============ INTERVENTIONS MOBILES (SI NÉCESSAIRE) ============

@login_required
def my_interventions_mobile(request):
    """Liste des interventions de l'employé - Vue mobile - VUE CORRIGÉE"""
    # ✅ CORRECTION: Accepter technicien ET tech_
    if not (request.user.user_type == 'technicien' or request.user.username.startswith('tech_')):
        messages.error(request, "Seuls les techniciens peuvent accéder aux interventions")
        return redirect('employees_mobile:dashboard')
    
    # Filtres
    status_filter = request.GET.get('status', 'active')
    
    # Base queryset
    interventions = Intervention.objects.filter(
        technicien=request.user
    ).order_by('-date_signalement')
    
    # Filtrage par statut
    if status_filter == 'active':
        interventions = interventions.filter(statut__in=['assigne', 'en_cours'])
    elif status_filter != 'all':
        interventions = interventions.filter(statut=status_filter)
    
    # Pagination
    paginator = Paginator(interventions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_filters': {'status': status_filter},
        'total_interventions': interventions.count(),
    }
    
    return render(request, 'employees/mobile/interventions_list.html', context)


@login_required
@require_http_methods(["POST"])
def intervention_start_mobile(request, intervention_id):
    """Démarrer une intervention depuis l'interface mobile - VUE CORRIGÉE"""
    intervention = get_object_or_404(
        Intervention, 
        id=intervention_id, 
        technicien=request.user
    )
    
    if intervention.statut != 'assigne':
        return JsonResponse({
            'success': False, 
            'error': 'Cette intervention ne peut pas être démarrée'
        })
    
    try:
        # ✅ DÉMARRER MANUELLEMENT SANS start_intervention()
        intervention.statut = 'en_cours'
        intervention.date_debut = timezone.now()
        intervention.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Intervention démarrée !',
            'new_status': 'en_cours',
            'status_text': 'En cours',
            'status_color': 'orange'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def intervention_complete_mobile(request, intervention_id):
    """Terminer une intervention depuis l'interface mobile - VUE CORRIGÉE"""
    intervention = get_object_or_404(
        Intervention, 
        id=intervention_id, 
        technicien=request.user
    )
    
    if intervention.statut != 'en_cours':
        return JsonResponse({
            'success': False, 
            'error': 'Cette intervention ne peut pas être terminée'
        })
    
    try:
        commentaire = request.POST.get('commentaire_technicien', '').strip()
        cout_reel = request.POST.get('cout_reel')
        
        # CORRECTION: Vérifier si un commentaire existe déjà OU si un nouveau est fourni
        commentaire_existant = getattr(intervention, 'commentaire_technicien', '') or ''
        
        # Si aucun commentaire existant ET aucun nouveau commentaire
        if not commentaire_existant and not commentaire:
            return JsonResponse({
                'success': False,
                'error': 'Un rapport technique est obligatoire pour terminer cette intervention. Veuillez d\'abord rédiger un rapport.'
            })
        
        # Terminer l'intervention
        intervention.statut = 'complete'
        intervention.date_fin = timezone.now()
        
        # Utiliser le nouveau commentaire s'il existe, sinon garder l'ancien
        if commentaire:
            intervention.commentaire_technicien = commentaire
        
        # Coût réel optionnel
        if cout_reel:
            try:
                intervention.cout_reel = float(cout_reel)
            except ValueError:
                pass
        
        intervention.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Intervention terminée avec succès !',
            'new_status': 'complete',
            'status_text': 'Terminée',
            'status_color': 'green'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def intervention_detail_mobile(request, intervention_id):
    """Détail d'une intervention - Vue mobile avec actions - VUE CORRIGÉE"""
    intervention = get_object_or_404(
        Intervention, 
        id=intervention_id, 
        technicien=request.user
    )
    
    # Médias associés
    medias = InterventionMedia.objects.filter(intervention=intervention).order_by('type_media', '-created_at')
    
    context = {
        'intervention': intervention,
        'medias': medias,
        'can_start': intervention.statut == 'assigne',
        'can_complete': intervention.statut == 'en_cours',
        'can_upload': intervention.statut in ['en_cours', 'complete'],
    }
    
    return render(request, 'employees/mobile/intervention_detail.html', context)


# ============ UPLOAD DE MÉDIAS MOBILE ============

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_media_mobile(request, item_type, item_id):
    """Upload de médias depuis l'interface mobile (tâche ou intervention) - VUE CORRIGÉE"""
    try:
        # ✅ CORRECTION: Vérifier les permissions d'abord
        employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
        
        if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
            return JsonResponse({'success': False, 'error': 'Non autorisé'})
        
        # Vérifier le type d'item
        if item_type == 'task':
            item = get_object_or_404(Task, id=item_id, assigne_a=request.user)
            media_model = TaskMedia
            relation_field = 'task'
        elif item_type == 'intervention':
            item = get_object_or_404(Intervention, id=item_id, technicien=request.user)
            media_model = InterventionMedia
            relation_field = 'intervention'
        else:
            return JsonResponse({'success': False, 'error': 'Type d\'item invalide'})
        
        # Récupérer les données
        if 'file' in request.FILES:
            # Upload de fichier classique
            file = request.FILES['file']
            type_media = request.POST.get('type_media', 'photo_apres')
            description = request.POST.get('description', '')
            
        elif 'image_data' in request.POST:
            # Upload depuis caméra (base64)
            image_data = request.POST.get('image_data')
            type_media = request.POST.get('type_media', 'photo_apres')
            description = request.POST.get('description', '')
            
            # Décoder l'image base64
            try:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"{item_type}_{item_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                
                # Créer le fichier
                from django.core.files.base import ContentFile
                file = ContentFile(
                    base64.b64decode(imgstr),
                    name=filename
                )
            except Exception as e:
                return JsonResponse({'success': False, 'error': f'Erreur image: {str(e)}'})
        else:
            return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'})
        
        # Créer le média
        media_data = {
            relation_field: item,
            'type_media': type_media,
            'fichier': file,
            'description': description,
        }
        
        # Ajouter le champ uploaded_by ou ajoute_par selon le modèle
        if hasattr(media_model, 'uploaded_by'):
            media_data['uploaded_by'] = request.user
        elif hasattr(media_model, 'ajoute_par'):
            media_data['ajoute_par'] = request.user
        
        media = media_model.objects.create(**media_data)
        
        return JsonResponse({
            'success': True,
            'message': 'Fichier uploadé avec succès !',
            'media_id': media.id,
            'file_url': media.fichier.url if media.fichier else None,
            'type_media': media.get_type_media_display()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def quick_report_mobile(request, item_type, item_id):
    """Formulaire de rapport rapide mobile pour tâches et interventions"""
    try:
        # Vérifier les permissions employé
        employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
        
        if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
            return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
        
        # Traitement selon le type d'item
        if item_type == 'task':
            # Récupérer la tâche
            item = get_object_or_404(Task, id=item_id, assigne_a=request.user)
            
            # Récupérer le commentaire
            commentaire = request.POST.get('commentaire', '').strip()
            
            if not commentaire:
                return JsonResponse({
                    'success': False, 
                    'error': 'Le commentaire ne peut pas être vide'
                })
            
            # Sauvegarder le commentaire
            item.commentaire = commentaire
            item.save(update_fields=['commentaire'])
            
            return JsonResponse({
                'success': True,
                'message': 'Rapport sauvegardé avec succès !',
                'item_type': 'task',
                'item_id': item.id
            })
            
        elif item_type == 'intervention':
            # Récupérer l'intervention
            item = get_object_or_404(Intervention, id=item_id, technicien=request.user)
            
            # Récupérer les données
            commentaire = request.POST.get('commentaire_technicien', '').strip()
            cout_reel = request.POST.get('cout_reel', '').strip()
            
            if not commentaire:
                return JsonResponse({
                    'success': False, 
                    'error': 'Le rapport technique ne peut pas être vide'
                })
            
            # Sauvegarder les données
            item.commentaire_technicien = commentaire
            
            if cout_reel:
                try:
                    item.cout_reel = float(cout_reel)
                except ValueError:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Le coût doit être un nombre valide'
                    })
            
            item.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Rapport sauvegardé avec succès !',
                'item_type': 'intervention',
                'item_id': item.id
            })
            
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Type d\'item invalide: {item_type}'
            }, status=400)
            
    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tâche non trouvée'}, status=404)
    except Intervention.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Intervention non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def my_schedule_mobile(request):
    """Planning personnel de l'employé - Vue mobile - VUE CORRIGÉE"""
    # ✅ CORRECTION: Accepter tous les types d'employés ET tech_
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        messages.error(request, "Accès réservé aux employés.")
        return redirect('dashboard:index')
    
    # Date de référence
    date_param = request.GET.get('date')
    if date_param:
        try:
            reference_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            reference_date = timezone.now().date()
    else:
        reference_date = timezone.now().date()
    
    # Semaine de référence
    start_week = reference_date - timedelta(days=reference_date.weekday())
    
    # Organiser par jour de la semaine
    weekly_schedule = {}
    for i in range(7):
        day = start_week + timedelta(days=i)
        
        # Tâches du jour
        day_tasks = Task.objects.filter(
            assigne_a=request.user,
            date_prevue__date=day
        ).order_by('date_prevue')
        
        # Interventions du jour (basées sur date d'assignation)
        day_interventions = []
        if request.user.user_type == 'technicien' or request.user.username.startswith('tech_'):
            day_interventions = Intervention.objects.filter(
                technicien=request.user,
                date_assignation__date=day
            ).order_by('date_assignation')
        
        weekly_schedule[i] = {
            'date': day,
            'day_name': day.strftime('%A'),
            'day_short': day.strftime('%a'),
            'is_today': day == timezone.now().date(),
            'tasks': day_tasks,
            'interventions': day_interventions,
            'total_items': len(day_tasks) + len(day_interventions)
        }
    
    context = {
        'weekly_schedule': weekly_schedule,
        'reference_date': reference_date,
        'week_start': start_week,
        'week_end': start_week + timedelta(days=6),
        'prev_week': start_week - timedelta(days=7),
        'next_week': start_week + timedelta(days=7),
    }
    
    return render(request, 'employees/mobile/schedule.html', context)


# ============ APIs POUR DONNÉES OFFLINE ============

@login_required
def offline_data_api(request):
    """API pour données offline PWA - VUE CORRIGÉE"""
    # ✅ CORRECTION: Accepter tous les types d'employés ET tech_
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Données essentielles pour fonctionnement offline
    today = timezone.now().date()
    
    # Tâches des 7 prochains jours
    end_date = today + timedelta(days=7)
    tasks = Task.objects.filter(
        assigne_a=request.user,
        date_prevue__date__range=[today, end_date]
    ).select_related('bien')
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'titre': task.titre,
            'description': task.description,
            'type_tache': task.type_tache,
            'priorite': task.priorite,
            'statut': task.statut,
            'date_prevue': task.date_prevue.isoformat(),
            'bien_nom': task.bien.name if task.bien else None,
            'bien_adresse': task.bien.address if task.bien else None,
            'duree_estimee': task.duree_estimee,
        })
    
    # Interventions assignées
    interventions_data = []
    if request.user.user_type == 'technicien' or request.user.username.startswith('tech_'):
        interventions = Intervention.objects.filter(
            technicien=request.user,
            statut__in=['assigne', 'en_cours']
        ).select_related('bien')
        
        for intervention in interventions:
            interventions_data.append({
                'id': intervention.id,
                'numero_intervention': intervention.numero_intervention,
                'titre': intervention.titre,
                'description': intervention.description,
                'type_intervention': intervention.type_intervention,
                'priorite': intervention.priorite,
                'statut': intervention.statut,
                'date_signalement': intervention.date_signalement.isoformat(),
                'bien_nom': intervention.bien.name if intervention.bien else None,
                'bien_adresse': intervention.bien.address if intervention.bien else None,
                'cout_estime': float(intervention.cout_estime) if intervention.cout_estime else None,
            })
    
    return JsonResponse({
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'user': {
            'id': request.user.id,
            'name': request.user.get_full_name(),
            'type': request.user.user_type,
        },
        'tasks': tasks_data,
        'interventions': interventions_data,
        'constants': {
            'task_types': dict(Task.TYPE_TACHE_CHOICES),
            'priorities': dict(Task.PRIORITE_CHOICES),
            'statuses': dict(Task.STATUT_CHOICES),
        }
    })


@login_required
def my_stats_api(request):
    """API des statistiques personnelles de l'employé - VUE CORRIGÉE"""
    # ✅ CORRECTION: Accepter tous les types d'employés ET tech_
    employee_types = ['field_agent', 'technician', 'technicien', 'agent_terrain']
    
    if not (request.user.user_type in employee_types or request.user.username.startswith('tech_')):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Période (7 derniers jours par défaut)
    period_days = int(request.GET.get('days', 7))
    start_date = timezone.now().date() - timedelta(days=period_days)
    
    # Statistiques des tâches
    my_tasks = Task.objects.filter(assigne_a=request.user)
    period_tasks = my_tasks.filter(date_prevue__date__gte=start_date)
    
    task_stats = {
        'total_tasks': my_tasks.count(),
        'completed_tasks': my_tasks.filter(statut='complete').count(),
        'period_tasks': period_tasks.count(),
        'period_completed': period_tasks.filter(statut='complete').count(),
        'overdue_tasks': my_tasks.filter(
            statut__in=['planifie', 'en_cours'],
            date_prevue__lt=timezone.now()
        ).count(),
    }
    
    # Statistiques des interventions (si technicien)
    intervention_stats = {}
    if request.user.user_type == 'technicien' or request.user.username.startswith('tech_'):
        my_interventions = Intervention.objects.filter(technicien=request.user)
        period_interventions = my_interventions.filter(date_signalement__date__gte=start_date)
        
        # Satisfaction moyenne
        avg_satisfaction = my_interventions.filter(
            satisfaction_locataire__isnull=False
        ).aggregate(avg=Avg('satisfaction_locataire'))['avg']
        
        intervention_stats = {
            'total_interventions': my_interventions.count(),
            'completed_interventions': my_interventions.filter(statut='complete').count(),
            'period_interventions': period_interventions.count(),
            'period_completed': period_interventions.filter(statut='complete').count(),
            'avg_satisfaction': round(avg_satisfaction, 2) if avg_satisfaction else None,
        }
    
    return JsonResponse({
        'success': True,
        'period_days': period_days,
        'task_stats': task_stats,
        'intervention_stats': intervention_stats,
    })


# ============ VUES D'ASSIGNATION ET GESTION ============

@login_required
@require_http_methods(["POST"])
def task_assign_view(request, task_id):
    """Assigner une tâche à un employé (AJAX) - VERSION AVEC EMAIL"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    task = get_object_or_404(Task, id=task_id)
    employee_id = request.POST.get('employee_id')
    
    if not employee_id:
        return JsonResponse({'success': False, 'error': 'ID employé requis'})
    
    try:
        employee = get_object_or_404(User, 
            id=employee_id,
            user_type__in=['agent_terrain', 'technicien', 'field_agent', 'technician'],
            is_active=True
        )
        
        # Assigner la tâche
        task.assigne_a = employee
        task.statut = 'assigne'  # Mettre à jour le statut si nécessaire
        task.save()
        
        # ✅ ENVOYER NOTIFICATION + EMAIL
        email_sent = False
        try:
            notify_task_assigned_with_email(task, employee)
            email_sent = True
        except Exception as e:
            # Si l'email échoue, on log mais on ne bloque pas
            print(f"Erreur envoi email notification tâche: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Tâche assignée à {employee.get_full_name()}' + (' (email envoyé)' if email_sent else ''),
            'employee_name': employee.get_full_name(),
            'email_sent': email_sent
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def employee_workload_api(request, employee_id):
    """API pour la charge de travail d'un employé - VUE CORRIGÉE"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    try:
        employee = get_object_or_404(User, id=employee_id)
        
        # Charge de travail actuelle
        workload = {
            'planned_tasks': Task.objects.filter(
                assigne_a=employee, 
                statut='planifie'
            ).count(),
            'in_progress_tasks': Task.objects.filter(
                assigne_a=employee, 
                statut='en_cours'
            ).count(),
            'completed_today': Task.objects.filter(
                assigne_a=employee,
                statut='complete',
                date_fin__date=timezone.now().date()
            ).count(),
        }
        
        # Tâches de la semaine
        today = timezone.now().date()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        
        weekly_tasks = Task.objects.filter(
            assigne_a=employee,
            date_prevue__date__range=[start_week, end_week]
        ).count()
        
        workload['weekly_tasks'] = weekly_tasks
        workload['availability_status'] = 'available' if workload['planned_tasks'] + workload['in_progress_tasks'] < 5 else 'busy'
        
        return JsonResponse({
            'success': True,
            'workload': workload
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_employee_availability(request, employee_id):
    """API pour récupérer la disponibilité d'un employé"""
    try:
        if request.user.user_type not in ['manager', 'accountant']:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            })
        
        # Vérifier si l'employé existe
        try:
            employee_user = User.objects.get(id=employee_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Employé introuvable'
            })
        
        # Calculer la disponibilité basique
        today = timezone.now().date()
        
        # Tâches assignées aujourd'hui
        tasks_today = Task.objects.filter(
            assigne_a=employee_user,
            date_prevue__date=today,
            statut__in=['planifie', 'en_cours']
        ).count()
        
        # Interventions assignées aujourd'hui (si c'est un technicien)
        interventions_today = 0
        if employee_user.user_type in ['technicien', 'technician'] or employee_user.username.startswith('tech_'):
            from apps.maintenance.models import Intervention
            interventions_today = Intervention.objects.filter(
                technicien=employee_user,
                date_assignation__date=today,
                statut__in=['assigne', 'en_cours']
            ).count()
        
        total_workload = tasks_today + interventions_today
        
        availability_status = 'disponible'
        if total_workload >= 5:
            availability_status = 'occupé'
        elif total_workload >= 3:
            availability_status = 'chargé'
        
        return JsonResponse({
            'success': True,
            'employee': {
                'id': employee_user.id,
                'name': employee_user.get_full_name(),
                'user_type': employee_user.user_type,
            },
            'availability': {
                'status': availability_status,
                'tasks_today': tasks_today,
                'interventions_today': interventions_today,
                'total_workload': total_workload,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        })
    


def form_valid(self, form):
    response = super().form_valid(form)
    
    # Récupérer les informations de connexion générées
    if hasattr(self.object, '_login_info'):
        login_info = self.object._login_info
        
        # ✅ UTILISER le système de notification existant de enregistrements.html
        messages.success(
            self.request, 
            f"Employé '{self.object.user.get_full_name()}' créé avec succès ! "
            f"Identifiants générés"
        )
        
        # ✅ AJOUTER les données pour JavaScript dans le contexte
        # Le template enregistrements.html peut récupérer ces données
        self.request.session['employee_credentials'] = {
            'username': login_info['username'],
            'password': login_info['password'],
            'employee_name': self.object.user.get_full_name()
        }

    return response


# ═══════════════════════════════════════════════════════════════════
# CHANGEMENT DE MOT DE PASSE OBLIGATOIRE (PREMIÈRE CONNEXION)
# ═══════════════════════════════════════════════════════════════════

@login_required
def change_password_required_mobile(request):
    """
    Vue pour forcer le changement de mot de passe lors de la première connexion
    """
    from django.contrib.auth.forms import SetPasswordForm
    from django.contrib.auth import update_session_auth_hash

    # Vérifier si l'utilisateur a effectivement un mot de passe temporaire
    if not request.user.mot_de_passe_temporaire:
        # Si pas de mot de passe temporaire, rediriger vers le dashboard
        return redirect('employees_mobile:dashboard')

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Marquer le mot de passe comme permanent
            user.mot_de_passe_temporaire = False
            user.save()

            # Garder l'utilisateur connecté après le changement
            update_session_auth_hash(request, user)

            messages.success(
                request,
                "Votre mot de passe a été changé avec succès ! Bienvenue."
            )
            return redirect('employees_mobile:dashboard')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = SetPasswordForm(request.user)

    context = {
        'form': form,
        'user': request.user,
    }

    return render(request, 'employees/mobile/change_password_required.html', context)


@login_required
def employee_profile_mobile(request):
    """
    Page de profil employé - Voir et modifier ses informations
    """
    from apps.employees.models.employee import Employee
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, "Profil employé introuvable.")
        return redirect('employees_mobile:dashboard')

    # Traiter le changement de mot de passe
    if request.method == 'POST' and 'change_password' in request.POST:
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Garder connecté
            messages.success(request, "Votre mot de passe a été changé avec succès.")
            return redirect('employees_mobile:profil')
        else:
            messages.error(request, "Erreur lors du changement de mot de passe.")
    else:
        password_form = PasswordChangeForm(request.user)

    # Traiter l'upload de photo de profil
    if request.method == 'POST' and 'upload_photo' in request.POST:
        photo = request.FILES.get('profile_photo')
        if photo:
            request.user.profile_picture = photo
            request.user.save()
            messages.success(request, "Photo de profil mise à jour.")
            return redirect('employees_mobile:profil')

    # Statistiques de l'employé
    from apps.maintenance.models import Travail
    from django.db.models import Avg, Count, Q
    from datetime import timedelta

    travaux_stats = Travail.objects.filter(assigne_a=request.user).aggregate(
        total=Count('id'),
        termines=Count('id', filter=Q(statut='termine')),
        en_cours=Count('id', filter=Q(statut='en_cours')),
        temps_moyen=Avg('temps_reel', filter=Q(temps_reel__isnull=False))
    )

    # Travaux récents
    travaux_recents = Travail.objects.filter(
        assigne_a=request.user,
        statut='termine'
    ).order_by('-date_fin')[:5]

    # Taux de complétion
    total = travaux_stats['total'] or 0
    termines = travaux_stats['termines'] or 0
    taux_completion = (termines / total * 100) if total > 0 else 0

    context = {
        'employee': employee,
        'password_form': password_form,
        'travaux_stats': travaux_stats,
        'travaux_recents': travaux_recents,
        'taux_completion': round(taux_completion, 1),
    }

    return render(request, 'employees/mobile/profil.html', context)
