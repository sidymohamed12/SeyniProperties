# apps/maintenance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import timedelta
import json

from apps.notifications.utils import notify_intervention_assigned_with_email

# Imports des modèles
from .models.travail import Travail, TravailMedia
from .models.intervention import Intervention, InterventionMedia
from .forms import InterventionForm, TravailForm
from django.views.decorators.csrf import csrf_exempt

# Imports des modèles de properties et tiers
from apps.properties.models.properties import Property
from apps.properties.models.appartement import Appartement
from apps.properties.models.residence import Residence
from apps.tiers.models import Tiers

User = get_user_model()

# ================= FORMS MANQUANTS À CRÉER DANS forms.py =================
"""
Les forms suivants doivent être créés dans maintenance/forms.py :

class InterventionFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Rechercher...',
        'class': 'form-control'
    }))
    status = forms.ChoiceField(
        choices=[('', 'Tous')] + Travail.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'Toutes')] + Travail.PRIORITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    type_intervention = forms.ChoiceField(
        choices=[('', 'Tous')] + Travail.TYPE_TRAVAIL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class InterventionAssignForm(forms.Form):
    technicien = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='technicien', is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Technicien'
    )
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Commentaire'
    )
    date_planifiee = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Date planifiée'
    )

class InterventionCompleteForm(forms.Form):
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label='Rapport final'
    )
    cout_reel = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Coût réel'
    )
    duree_reelle = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Durée réelle (minutes)'
    )
    satisfaction_locataire = forms.ChoiceField(
        choices=[(i, f'{i}/5') for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Satisfaction locataire'
    )

class SimpleInterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ['titre', 'description', 'type_intervention', 'priorite', 'bien', 'technicien', 'cout_estime']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_intervention': forms.Select(attrs={'class': 'form-select'}),
            'priorite': forms.Select(attrs={'class': 'form-select'}),
            'bien': forms.Select(attrs={'class': 'form-select'}),
            'technicien': forms.Select(attrs={'class': 'form-select'}),
            'cout_estime': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
"""


class TravauxListView(LoginRequiredMixin, ListView):
    """Vue liste des travaux pour les managers"""
    model = Travail
    template_name = 'maintenance/travail_list.html'
    context_object_name = 'travaux'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions manager
        if request.user.user_type not in ['manager', 'accountant']:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Filtrer les travaux selon les paramètres"""
        queryset = Travail.objects.select_related('assigne_a').order_by('-date_signalement')
        
        # Relations pour optimisation
        queryset = queryset.select_related('appartement__residence')

        # Récupérer les filtres depuis kwargs (pour les URLs spécialisées)
        status_filter = self.kwargs.get('status')
        priority_filter = self.kwargs.get('priority')

        # Appliquer les filtres depuis l'URL
        if status_filter:
            queryset = queryset.filter(statut=status_filter)
        if priority_filter:
            queryset = queryset.filter(priorite=priority_filter)

        # Filtres depuis les paramètres GET
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(titre__icontains=search) |
                Q(description__icontains=search) |
                Q(numero_travail__icontains=search) |
                Q(appartement__nom__icontains=search) |
                Q(appartement__residence__nom__icontains=search)
            )

        status = self.request.GET.get('status')
        if status and not status_filter:  # Éviter le double filtrage
            queryset = queryset.filter(statut=status)

        priority = self.request.GET.get('priority')
        if priority and not priority_filter:  # Éviter le double filtrage
            queryset = queryset.filter(priorite=priority)

        type_travail = self.request.GET.get('type')
        if type_travail:
            queryset = queryset.filter(type_travail=type_travail)

        technician = self.request.GET.get('technician')
        if technician:
            queryset = queryset.filter(assigne_a_id=technician)

        appartement_filter = self.request.GET.get('appartement')
        if appartement_filter:
            queryset = queryset.filter(appartement_id=appartement_filter)

        residence_filter = self.request.GET.get('residence')
        if residence_filter:
            queryset = queryset.filter(residence_id=residence_filter)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiques globales
        all_travaux = Travail.objects.all()

        context.update({
            # Filtres actuels
            'current_filters': {
                'status': self.kwargs.get('status') or self.request.GET.get('status'),
                'priority': self.kwargs.get('priority') or self.request.GET.get('priority'),
                'type': self.request.GET.get('type'),
                'technician': self.request.GET.get('technician'),
                'appartement': self.request.GET.get('appartement'),
                'residence': self.request.GET.get('residence'),
                'search': self.request.GET.get('search'),
            },

            # Statistiques
            'stats': {
                'total': all_travaux.count(),
                'urgents': all_travaux.filter(
                    priorite='urgente',
                    statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
                ).count(),
                'en_cours': all_travaux.filter(statut='en_cours').count(),
                'attente_materiel': all_travaux.filter(statut='en_attente_materiel').count(),
                'en_retard': all_travaux.filter(
                    date_prevue__lt=timezone.now().date(),
                    statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
                ).count(),
                'signale': all_travaux.filter(statut='signale').count(),
                'assigne': all_travaux.filter(statut='assigne').count(),
                'complete': all_travaux.filter(statut='complete').count(),
            },

            # Données pour les filtres
            'technicians': User.objects.filter(user_type='technicien', is_active=True),
            'appartements': Appartement.objects.select_related('residence').all()[:100],
            'residences': Residence.objects.all(),

            # Choix pour les filtres
            'travail_types': Travail.TYPE_TRAVAIL_CHOICES,
            'priorities': Travail.PRIORITE_CHOICES,
            'statuses': Travail.STATUT_CHOICES,
            'natures': Travail.NATURE_CHOICES,
        })

        return context


class TravailCreateView(LoginRequiredMixin, CreateView):
    """Vue pour créer un nouveau travail"""
    model = Travail
    form_class = TravailForm
    template_name = 'maintenance/travail_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de créer des travaux.")
            return redirect('maintenance:travail_list')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """✅ Créer un nouveau travail - utilise le modèle Travail unifié"""
        try:
            post_data = request.POST

            # Créer le travail directement
            travail = Travail()

            # Champs de base
            travail.titre = post_data.get('titre', '').strip()
            if not travail.titre:
                messages.error(request, "Le titre est obligatoire")
                return self.get(request, *args, **kwargs)

            travail.description = post_data.get('description', '').strip() or 'Travail à effectuer'

            # Type de travail
            type_travail = post_data.get('type_travail', '')
            if not type_travail:
                messages.error(request, "Le type de travail est obligatoire")
                return self.get(request, *args, **kwargs)
            travail.type_travail = type_travail

            # Priorité
            travail.priorite = post_data.get('priorite', 'normale')

            # Nature du travail
            nature = post_data.get('nature', '')
            if nature:
                travail.nature = nature
            else:
                travail.nature = 'reactif'  # Par défaut

            # Localisation - Appartement
            appartement_id = post_data.get('appartement')
            if appartement_id:
                try:
                    travail.appartement = Appartement.objects.get(id=appartement_id)
                    print(f"✅ Appartement assigné: {travail.appartement.nom}")
                except Exception as e:
                    print(f"⚠️ Erreur récupération appartement: {e}")

            # Localisation - Résidence (si pas d'appartement)
            if not appartement_id:
                residence_id = post_data.get('residence')
                if residence_id:
                    try:
                        travail.residence = Residence.objects.get(id=residence_id)
                        print(f"✅ Résidence assignée: {travail.residence.nom}")
                    except Exception as e:
                        print(f"⚠️ Erreur récupération résidence: {e}")

            # Coût estimé
            cout_estime = post_data.get('cout_estime', '')
            if cout_estime:
                try:
                    travail.cout_estime = float(cout_estime)
                except:
                    pass

            # Champs automatiques
            travail.cree_par = request.user
            travail.date_signalement = timezone.now()

            # ✅ Employé assigné
            assigne_a_id = post_data.get('assigne_a')
            if assigne_a_id:
                try:
                    employe = User.objects.get(id=assigne_a_id, is_active=True)
                    travail.assigne_a = employe
                    travail.statut = 'assigne'
                    travail.date_assignation = timezone.now()
                    print(f"✅ Employé assigné: {employe.get_full_name()} (ID: {employe.id})")
                except Exception as e:
                    print(f"⚠️ Erreur assignation employé: {e}")
                    travail.statut = 'signale'
            else:
                travail.statut = 'signale'

            # Date prévue
            date_prevue = post_data.get('date_prevue')
            if date_prevue:
                travail.date_prevue = date_prevue

            # Récurrence
            recurrence = post_data.get('recurrence', 'aucune')
            travail.recurrence = recurrence

            # Générer le numéro de travail
            if not travail.numero_travail:
                try:
                    from apps.core.utils import generate_unique_reference
                    travail.numero_travail = generate_unique_reference('TRAV')
                except:
                    import uuid
                    travail.numero_travail = f"TRAV-{str(uuid.uuid4())[:8].upper()}"

            # Sauvegarder
            travail.save()

            messages.success(request, f"✅ Travail '{travail.titre}' créé avec succès!")
            print(f"✅ Travail créé: {travail.numero_travail}")

            # Redirection selon l'action
            action = post_data.get('action', 'save')

            if action == 'save_and_create_demande':
                # Rediriger vers le formulaire de demande d'achat avec le travail pré-rempli
                return redirect(f"{reverse('payments:demande_achat_create')}?travail_id={travail.id}")
            else:
                # Redirection normale vers le détail
                return redirect('maintenance:travail_detail', travail_id=travail.id)

        except Exception as e:
            error_message = f"Erreur lors de la création: {str(e)}"
            print(f"❌ Erreur création: {error_message}")
            import traceback
            traceback.print_exc()

            messages.error(request, error_message)
            return self.get(request, *args, **kwargs)

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Importer les modèles nécessaires
        from apps.properties.models.residence import Residence
        from apps.properties.models.appartement import Appartement
        from apps.accounts.models.custom_user import CustomUser

        # Ajouter les données pour les dropdowns du formulaire
        context.update({
            'title': 'Nouvelle intervention',
            'edit_mode': False,
            'residences': Residence.objects.all().order_by('nom'),
            'appartements': Appartement.objects.select_related('residence').all().order_by('residence__nom', 'nom'),
            'employes': CustomUser.objects.filter(
                user_type__in=['technicien', 'technician', 'field_agent', 'employee'],
                is_active=True
            ).order_by('first_name', 'last_name'),
        })
        return context


class TravailUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier un travail"""
    model = Travail
    form_class = TravailForm
    template_name = 'maintenance/travail_form.html'
    pk_url_kwarg = 'travail_id'

    def dispatch(self, request, *args, **kwargs):
        if request.user.user_type not in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de modifier ce travail.")
            return redirect('maintenance:travail_list')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """✅ BYPASS pour l'édition aussi - même logique que la création"""
        self.object = self.get_object()

        try:
            post_data = request.POST
            intervention = self.object

            # Champs de base
            titre = post_data.get('titre', '').strip()
            if titre:
                intervention.titre = titre

            description = post_data.get('description', '').strip()
            if description:
                intervention.description = description

            # Type de travail
            type_travail = post_data.get('type_travail', '')
            if type_travail:
                intervention.type_intervention = type_travail

            # Priorité
            priorite = post_data.get('priorite', '')
            if priorite:
                intervention.priorite = priorite

            # Nature du travail
            nature = post_data.get('nature', '')
            if hasattr(intervention, 'nature') and nature:
                intervention.nature = nature

            # Localisation - Appartement
            appartement_id = post_data.get('appartement', '')
            if appartement_id:
                try:
                    from apps.properties.models.appartement import Appartement
                    intervention.appartement = Appartement.objects.get(id=appartement_id)
                except:
                    pass
            elif appartement_id == '':  # Si vide, on enlève l'assignation
                intervention.appartement = None

            # Localisation - Résidence
            residence_id = post_data.get('residence', '')
            if residence_id and hasattr(intervention, 'residence'):
                try:
                    from apps.properties.models.residence import Residence
                    intervention.residence = Residence.objects.get(id=residence_id)
                except:
                    pass
            elif residence_id == '' and hasattr(intervention, 'residence'):
                intervention.residence = None

            # Coût estimé
            cout_estime = post_data.get('cout_estime', '')
            if cout_estime:
                try:
                    intervention.cout_estime = float(cout_estime)
                except:
                    pass

            # Lieu précis
            lieu_precis = post_data.get('lieu_precis', '')
            if hasattr(intervention, 'lieu_precis'):
                intervention.lieu_precis = lieu_precis

            # ✅ Technicien assigné - gérer le changement d'assignation
            old_technicien = intervention.technicien
            assigne_a = post_data.get('assigne_a', '')

            if assigne_a:
                try:
                    from apps.accounts.models.custom_user import CustomUser
                    new_technicien = CustomUser.objects.get(id=assigne_a, is_active=True)

                    if new_technicien != old_technicien:
                        intervention.technicien = new_technicien
                        # Si c'était signalé et qu'on assigne maintenant
                        if intervention.statut == 'signale':
                            intervention.statut = 'assigne'
                            intervention.date_assignation = timezone.now()
                            print(f"✅ Technicien assigné: {new_technicien.get_full_name()}")
                except Exception as e:
                    print(f"⚠️ Erreur assignation technicien: {e}")
            elif assigne_a == '':  # Si on enlève l'assignation
                if old_technicien and intervention.statut == 'assigne':
                    intervention.technicien = None
                    intervention.statut = 'signale'
                    intervention.date_assignation = None
                    print("✅ Assignation supprimée")

            # Dates
            date_prevue = post_data.get('date_prevue', '')
            if date_prevue and hasattr(intervention, 'date_prevue'):
                intervention.date_prevue = date_prevue
            elif date_prevue == '' and hasattr(intervention, 'date_prevue'):
                intervention.date_prevue = None

            date_limite = post_data.get('date_limite', '')
            if date_limite and hasattr(intervention, 'date_limite'):
                intervention.date_limite = date_limite
            elif date_limite == '' and hasattr(intervention, 'date_limite'):
                intervention.date_limite = None

            # Sauvegarder
            intervention.save()

            messages.success(request, f"✅ Travail '{intervention.titre}' modifié avec succès!")
            print(f"✅ Intervention modifiée: {intervention.numero_intervention}")

            # Redirection
            return redirect('maintenance:travail_detail', travail_id=travail.id)

        except Exception as e:
            error_message = f"Erreur lors de la modification: {str(e)}"
            print(f"❌ Erreur modification: {error_message}")
            import traceback
            traceback.print_exc()

            messages.error(request, error_message)
            return self.get(request, *args, **kwargs)
    
    def form_valid(self, form):
        # ✅ LOGIQUE DE MISE À JOUR DU STATUT
        old_technicien = self.object.technicien
        new_technicien = form.instance.technicien
        
        # Si on assigne un technicien pour la première fois
        if not old_technicien and new_technicien and form.instance.statut == 'signale':
            form.instance.statut = 'assigne'
            form.instance.date_assignation = timezone.now()
        # Si on enlève l'assignation
        elif old_technicien and not new_technicien and form.instance.statut == 'assigne':
            form.instance.statut = 'signale'
            form.instance.date_assignation = None
        
        response = super().form_valid(form)
        messages.success(self.request, f"Intervention '{self.object.titre}' modifiée avec succès!")
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('maintenance:travail_detail', kwargs={'intervention_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Importer les modèles nécessaires
        from apps.properties.models.residence import Residence
        from apps.properties.models.appartement import Appartement
        from apps.accounts.models.custom_user import CustomUser

        # Ajouter les données pour les dropdowns du formulaire
        context.update({
            'title': f'Modifier l\'intervention "{self.object.titre}"',
            'edit_mode': True,
            'travail': self.object,  # Ajouter 'travail' pour le template
            'intervention': self.object,
            'residences': Residence.objects.all().order_by('nom'),
            'appartements': Appartement.objects.select_related('residence').all().order_by('residence__nom', 'nom'),
            'employes': CustomUser.objects.filter(
                user_type__in=['technicien', 'technician', 'field_agent', 'employee'],
                is_active=True
            ).order_by('first_name', 'last_name'),
        })
        return context


@login_required
def travail_detail_view(request, travail_id):
    """Vue détail d'un travail avec timeline"""
    travail = get_object_or_404(Travail, id=travail_id)

    # Vérification des permissions
    can_view = (
        request.user.user_type in ['manager', 'accountant'] or
        travail.assigne_a == request.user or
        getattr(travail, 'signale_par', None) == request.user
    )

    if not can_view:
        messages.error(request, "Vous n'avez pas accès à ce travail.")
        return redirect('maintenance:travail_list')

    # Récupérer les médias associés
    medias = TravailMedia.objects.filter(travail=travail).order_by('-created_at')

    # ✅ ARCHITECTURE 1-to-Many: Les demandes d'achat sont accessibles via travail.demandes_achat.all()
    # Plus besoin de passer demande_achat au contexte, le template y accède directement

    # Récupérer la liste des techniciens (pour le modal d'assignation)
    technicians = []
    try:
        from django.contrib.auth import get_user_model
        user = get_user_model()
        technicians = user.objects.filter(
            user_type__in=['technician', 'technicien', 'field_agent']
        ).order_by('first_name', 'last_name')
    except:
        pass
    
    # Créer la timeline
    timeline = []

    # 1. Signalement
    if travail.date_signalement:
        signale_par_nom = 'Système'
        if travail.signale_par:
            signale_par_nom = travail.signale_par.get_full_name()

        timeline.append({
            'action': 'Travail signalé',
            'user': signale_par_nom,
            'date': travail.date_signalement,
            'icon': 'fa-exclamation',
            'color': 'red'
        })

    # 2. Assignation
    if travail.date_assignation and travail.assigne_a:
        timeline.append({
            'action': f'Assigné à {travail.assigne_a.get_full_name()}',
            'user': 'Manager',
            'date': travail.date_assignation,
            'icon': 'fa-user-plus',
            'color': 'blue'
        })

    # 3. Début du travail
    if travail.date_debut:
        timeline.append({
            'action': 'Travail démarré',
            'user': travail.assigne_a.get_full_name() if travail.assigne_a else 'Employé',
            'date': travail.date_debut,
            'icon': 'fa-play',
            'color': 'orange'
        })

    # 4. Demandes d'achat créées (si elles existent) - Architecture 1-to-Many
    for demande in travail.demandes_achat.all():
        if demande.date_demande:
            timeline.append({
                'action': f'Demande d\'achat créée ({demande.numero_facture})',
                'user': demande.demandeur.get_full_name() if demande.demandeur else 'Système',
                'date': demande.date_demande,
                'icon': 'fa-shopping-cart',
                'color': 'purple'
            })

    # 5. Fin du travail
    if travail.date_fin:
        timeline.append({
            'action': 'Travail terminé',
            'user': travail.assigne_a.get_full_name() if travail.assigne_a else 'Employé',
            'date': travail.date_fin,
            'icon': 'fa-check',
            'color': 'green'
        })
    
    # Trier la timeline par date (chronologique pour l'affichage)
    # Normaliser les dates pour éviter les erreurs de comparaison
    from datetime import datetime, date

    def normalize_date(d):
        """Convertit date en datetime aware pour permettre la comparaison"""
        if d is None:
            return timezone.now()

        # Convertir date en datetime
        if isinstance(d, date) and not isinstance(d, datetime):
            d = datetime.combine(d, datetime.min.time())

        # Rendre aware si naive
        if isinstance(d, datetime) and timezone.is_naive(d):
            d = timezone.make_aware(d)

        return d

    timeline.sort(key=lambda x: normalize_date(x['date']))

    # Calculer la progression de la checklist (si elle existe)
    checklist_total = 0
    checklist_completed = 0
    checklist_progress = 0

    if hasattr(travail, 'checklist'):
        try:
            checklist_items = travail.checklist.all()
            checklist_total = checklist_items.count()
            checklist_completed = checklist_items.filter(est_complete=True).count()
            if checklist_total > 0:
                checklist_progress = int((checklist_completed / checklist_total) * 100)
        except:
            pass

    context = {
        'travail': travail,
        'medias': medias,
        'timeline': timeline,
        'technicians': technicians,
        # ✅ SUPPRIMÉ: 'demande_achat' - Plus besoin, accessible via travail.demandes_achat.all() dans le template
        'can_edit': request.user.user_type in ['manager', 'accountant'],
        'can_assign': request.user.user_type in ['manager', 'accountant'] and travail.statut == 'signale',
        'can_start': travail.statut == 'assigne' and travail.assigne_a == request.user,
        'can_complete': travail.statut == 'en_cours' and travail.assigne_a == request.user,
        # Checklist progression
        'checklist_total': checklist_total,
        'checklist_completed': checklist_completed,
        'checklist_progress': checklist_progress,
    }

    return render(request, 'maintenance/travail_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def travail_assign_view(request, travail_id):
    """Vue pour assigner une intervention à un technicien - VERSION AVEC EMAIL"""
    travail = get_object_or_404(Travail, id=travail_id)
    
    # Vérifier les permissions
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation d'assigner cette travail.")
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    if travail.statut not in ['signale', 'assigne']:
        messages.error(request, "Cette intervention ne peut plus être assignée dans son état actuel.")
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    if request.method == 'GET':
        # ✅ FORMULAIRE SIMPLE SANS InterventionAssignForm
        technicians = User.objects.filter(user_type='technicien', is_active=True)
        return render(request, 'maintenance/intervention_assign.html', {
            'travail': travail,
            'technicians': technicians,
        })
    
    elif request.method == 'POST':
        try:
            # ✅ TRAITEMENT MANUEL SANS FORM
            technicien_id = request.POST.get('technicien_id')
            commentaire = request.POST.get('commentaire', '').strip()
            
            if not technicien_id:
                raise ValueError("Veuillez sélectionner un technicien")
            
            technicien = get_object_or_404(User, id=technicien_id, user_type='technicien', is_active=True)
            
            # Assigner l'intervention
            travail.technicien = technicien
            travail.statut = 'assigne'
            travail.date_assignation = timezone.now()
            
            if commentaire:
                travail.commentaire_assignation = commentaire
            
            travail.save()
            
            # ✅ ENVOYER NOTIFICATION + EMAIL
            try:
                notify_intervention_assigned_with_email(intervention, technicien)
                email_status = " (notification email envoyée)"
            except Exception as e:
                # Si l'email échoue, on log mais on ne bloque pas
                print(f"Erreur envoi email: {str(e)}")
                email_status = " (notification envoyée)"
            
            messages.success(request, f"Travail assigné à {technicien.get_full_name()}{email_status}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Travail assigné à {technicien.get_full_name()}!',
                    'redirect_url': reverse('maintenance:travail_detail', kwargs={'travail_id': travail.id})
                })
            
            return redirect('maintenance:travail_detail', travail_id=travail.id)
            
        except Exception as e:
            error_msg = f"Erreur lors de l'assignation: {str(e)}"
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            technicians = User.objects.filter(user_type='technicien', is_active=True)
            return render(request, 'maintenance/intervention_assign.html', {
                'travail': travail,
                'technicians': technicians,
                'error': error_msg
            })


@login_required
@require_http_methods(["POST"])
def travail_start_view(request, travail_id):
    """Démarrer une intervention - VERSION SIMPLIFIÉE"""
    travail = get_object_or_404(Travail, id=travail_id)
    
    # Vérifications
    if travail.technicien != request.user and request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    
    if travail.statut != 'assigne':
        return JsonResponse({'success': False, 'error': 'Intervention non démarrable'}, status=400)
    
    try:
        # ✅ DÉMARRER L'INTERVENTION MANUELLEMENT
        travail.statut = 'en_cours'
        travail.date_debut = timezone.now()
        travail.save()
        
        messages.success(request, f"Intervention '{travail.titre}' démarrée!")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Intervention démarrée!'})
        
        return redirect('maintenance:travail_detail', travail_id=travail.id)
        
    except Exception as e:
        error_msg = f"Erreur: {str(e)}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        
        messages.error(request, error_msg)
        return redirect('maintenance:travail_detail', travail_id=travail.id)


@login_required
@require_http_methods(["GET", "POST"])
def travail_complete_view(request, travail_id):
    """Terminer une intervention - VERSION SIMPLIFIÉE"""
    travail = get_object_or_404(Travail, id=travail_id)
    
    # Vérifications
    if travail.technicien != request.user and request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'êtes pas autorisé à terminer cette travail.")
        return redirect('maintenance:interventions_list')
    
    if travail.statut != 'en_cours':
        messages.error(request, "Cette intervention ne peut pas être terminée dans son état actuel.")
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    if request.method == 'GET':
        # ✅ FORMULAIRE SIMPLE SANS InterventionCompleteForm
        return render(request, 'maintenance/intervention_complete_form.html', {
            'travail': travail,
        })
    
    elif request.method == 'POST':
        try:
            # ✅ TRAITEMENT MANUEL SANS FORM
            commentaire = request.POST.get('commentaire', '').strip()
            cout_reel = request.POST.get('cout_reel', '').strip()
            duree_reelle = request.POST.get('duree_reelle', '').strip()
            satisfaction = request.POST.get('satisfaction_locataire', '').strip()
            
            if not commentaire:
                raise ValueError("Le commentaire de finalisation est obligatoire")
            
            # Terminer l'intervention
            travail.statut = 'complete'
            travail.date_fin = timezone.now()
            
            # ✅ UTILISER LES CHAMPS CORRECTS SELON LE MODÈLE
            if hasattr(intervention, 'commentaire_completion'):
                travail.commentaire_completion = commentaire
            elif hasattr(intervention, 'commentaire_fin'):
                travail.commentaire_fin = commentaire
            elif hasattr(intervention, 'commentaire_technicien'):
                travail.commentaire_technicien = commentaire
            
            if cout_reel:
                try:
                    if hasattr(intervention, 'cout_reel'):
                        travail.cout_reel = float(cout_reel)
                    elif hasattr(intervention, 'cout_final'):
                        travail.cout_final = float(cout_reel)
                except ValueError:
                    pass
            
            if duree_reelle:
                try:
                    travail.duree_reelle = int(duree_reelle)
                except ValueError:
                    pass
            
            if satisfaction:
                try:
                    travail.satisfaction_locataire = int(satisfaction)
                except ValueError:
                    pass
            
            travail.save()
            
            messages.success(request, f"Intervention '{travail.titre}' terminée avec succès!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Intervention terminée!',
                    'redirect_url': reverse('maintenance:interventions_list')
                })
            
            return redirect('maintenance:interventions_list')
            
        except Exception as e:
            error_msg = f"Erreur lors de la finalisation: {str(e)}"
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            return render(request, 'maintenance/intervention_complete_form.html', {
                'travail': travail,
                'error': error_msg
            })


@login_required
def travail_delete_view(request, travail_id):
    """Supprimer une intervention"""
    travail = get_object_or_404(Travail, id=travail_id)
    
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer des interventions.")
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    if request.method == 'POST':
        intervention_title = travail.titre
        travail.delete()
        messages.success(request, f'Intervention "{intervention_title}" supprimée avec succès')
        return redirect('maintenance:interventions_list')
    
    context = {
        'travail': intervention,
    }
    
    return render(request, 'maintenance/intervention_confirm_delete.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def travail_upload_media_view(request, travail_id):
    """Vue pour uploader des médias pour une intervention"""
    travail = get_object_or_404(Travail, id=travail_id)
    
    # Vérifier les permissions
    can_upload = (
        request.user.user_type in ['manager', 'accountant'] or
        travail.technicien == request.user
    )
    
    if not can_upload:
        messages.error(request, "Vous n'avez pas l'autorisation d'uploader des fichiers pour cette travail.")
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    if request.method == 'POST':
        try:
            # ✅ TRAITEMENT SIMPLE D'UPLOAD
            if 'file' in request.FILES:
                file = request.FILES['file']
                type_media = request.POST.get('type_media', 'photo_apres')
                description = request.POST.get('description', '')
                
                # Créer le média
                media_data = {
                    'travail': travail,
                    'type_media': type_media,
                    'fichier': file,
                    'description': description,
                }
                
                # Ajouter le champ utilisateur selon le modèle
                if hasattr(InterventionMedia, 'ajoute_par'):
                    media_data['ajoute_par'] = request.user
                elif hasattr(InterventionMedia, 'uploaded_by'):
                    media_data['uploaded_by'] = request.user
                
                media = InterventionMedia.objects.create(**media_data)
                
                messages.success(request, "Fichier uploadé avec succès!")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Fichier uploadé!',
                        'media_id': media.id
                    })
            else:
                raise ValueError("Aucun fichier fourni")
                
        except Exception as e:
            error_msg = f"Erreur upload: {str(e)}"
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
        
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    return render(request, 'maintenance/intervention_upload_media.html', {
        'travail': intervention
    })


# ============ VUES API ============

@login_required
def travaux_stats_api(request):
    """API pour les statistiques des interventions"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # Statistiques générales
    total = Travail.objects.count()
    pending = Travail.objects.filter(statut='signale').count()
    in_progress = Travail.objects.filter(statut='en_cours').count()
    completed = Travail.objects.filter(statut='complete').count()
    
    # ✅ STATISTIQUES CONDITIONNELLES SELON LES CHAMPS DISPONIBLES
    priority_stats = {}
    if hasattr(Intervention, 'PRIORITE_CHOICES'):
        for priority, label in Travail.PRIORITE_CHOICES:
            priority_stats[priority] = Travail.objects.filter(priorite=priority).count()
    
    type_stats = {}
    if hasattr(Intervention, 'TYPE_INTERVENTION_CHOICES'):
        for type_intervention, label in Travail.TYPE_TRAVAIL_CHOICES:
            type_stats[type_intervention] = Travail.objects.filter(type_intervention=type_intervention).count()
    
    data = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'priority_stats': priority_stats,
        'type_stats': type_stats,
    }
    
    return JsonResponse(data)


@login_required
def travail_calendar_api(request):
    """API pour le calendrier des interventions"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # ✅ RÉCUPÉRER SELON LES CHAMPS DISPONIBLES
    date_field = None
    if hasattr(Intervention._meta.get_field('date_planifiee'), 'name'):
        date_field = 'date_planifiee'
    elif hasattr(Intervention._meta.get_field('date_assignation'), 'name'):
        date_field = 'date_assignation'
    
    if not date_field:
        return JsonResponse([])
    
    interventions = Travail.objects.filter(**{f'{date_field}__isnull': False}).select_related('technicien')
    
    if Property:
        interventions = interventions.select_related('bien')
    
    events = []
    for intervention in interventions:
        date_value = getattr(intervention, date_field)
        
        events.append({
            'id': travail.id,
            'title': travail.titre,
            'start': date_value.isoformat(),
            'url': reverse('maintenance:travail_detail', kwargs={'travail_id': travail.id}),
            'color': {
                'urgente': '#ef4444',
                'haute': '#f97316',
                'normale': '#3b82f6',
                'basse': '#10b981',
            }.get(getattr(intervention, 'priorite', 'normale'), '#6b7280'),
            'extendedProps': {
                'priority': getattr(intervention, 'priorite', ''),
                'status': travail.statut,
                'technician': travail.technicien.get_full_name() if travail.technicien else None,
                'property': travail.bien.name if Property and travail.bien else None,
            }
        })
    
    return JsonResponse(events, safe=False)


# ============ VUES SIMPLIFIÉES POUR CRÉATION/MODIFICATION ============

@login_required
@require_http_methods(["GET", "POST"])
def travail_create_simple(request):
    """Vue simplifiée pour créer une intervention"""
    
    # Vérification des permissions
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des interventions.")
        return redirect('maintenance:interventions_list')
    
    if request.method == 'GET':
        # Afficher le formulaire
        return render(request, 'maintenance/intervention_form_simple.html', {
            'title': 'Nouvelle intervention',
            'edit_mode': False,
            'technicians': User.objects.filter(user_type='technicien', is_active=True),
            'properties': Property.objects.all(),
            'locataires': Tiers.objects.filter(type_tiers='locataire', statut='actif'),
            'intervention_types': getattr(Intervention, 'TYPE_INTERVENTION_CHOICES', []),
            'priorities': getattr(Intervention, 'PRIORITE_CHOICES', []),
        })
    
    elif request.method == 'POST':
        try:
            # ✅ TRAITEMENT MANUEL DES DONNÉES
            titre = request.POST.get('titre', '').strip()
            description = request.POST.get('description', '').strip()
            type_intervention = request.POST.get('type_intervention', '').strip()
            priorite = request.POST.get('priorite', 'normale')
            
            # Validations
            if not titre:
                raise ValueError("Le titre est obligatoire")
            if not description:
                raise ValueError("La description est obligatoire")
            if not type_intervention:
                raise ValueError("Le type d'intervention est obligatoire")
            
            # Créer l'intervention
            intervention_data = {
                'titre': titre,
                'description': description,
                'type_intervention': type_intervention,
                'priorite': priorite,
                'signale_par': request.user,
                'date_signalement': timezone.now(),
                'statut': 'signale',
            }
            
            # Champs optionnels
            bien_id = request.POST.get('bien_id')
            if bien_id and Property:
                try:
                    bien = Property.objects.get(id=bien_id)
                    intervention_data['bien'] = bien
                except Property.DoesNotExist:
                    pass
            
            locataire_id = request.POST.get('locataire_id')
            if locataire_id:
                try:
                    locataire = Tiers.objects.get(id=locataire_id, type_tiers='locataire')
                    intervention_data['locataire'] = locataire
                except Tiers.DoesNotExist:
                    pass
            
            technicien_id = request.POST.get('technicien_id')
            if technicien_id:
                try:
                    technicien = User.objects.get(id=technicien_id, user_type='technicien', is_active=True)
                    intervention_data['technicien'] = technicien
                    intervention_data['statut'] = 'assigne'
                    intervention_data['date_assignation'] = timezone.now()
                except User.DoesNotExist:
                    pass
            
            cout_estime = request.POST.get('cout_estime')
            if cout_estime:
                try:
                    intervention_data['cout_estime'] = float(cout_estime)
                except ValueError:
                    pass
            
            # Créer l'intervention
            intervention = Travail.objects.create(**intervention_data)
            
            messages.success(request, f"Intervention '{intervention.titre}' créée avec succès!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Intervention '{intervention.titre}' créée avec succès!",
                    'travail_id': travail.id,
                    'redirect_url': reverse('maintenance:travail_detail', kwargs={'travail_id': travail.id})
                })
            
            return redirect('maintenance:travail_detail', travail_id=travail.id)
            
        except Exception as e:
            error_msg = f"Erreur lors de la création: {str(e)}"
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            # Réafficher le formulaire avec erreur
            return render(request, 'maintenance/intervention_form_simple.html', {
                'title': 'Nouvelle intervention',
                'edit_mode': False,
                'technicians': User.objects.filter(user_type='technicien', is_active=True),
                'properties': Property.objects.all(),
                'locataires': Tiers.objects.filter(type_tiers='locataire', statut='actif'),
                'intervention_types': getattr(Intervention, 'TYPE_INTERVENTION_CHOICES', []),
                'priorities': getattr(Intervention, 'PRIORITE_CHOICES', []),
                'error': error_msg,
                'form_data': request.POST,
            })


@login_required
@require_http_methods(["GET", "POST"])
def travail_edit_simple(request, travail_id):
    """Vue simplifiée pour modifier une intervention"""
    
    intervention = get_object_or_404(Travail, id=travail_id)
    
    # Vérification des permissions
    if request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier cette intervention.")
        return redirect('maintenance:travail_detail', travail_id=travail.id)
    
    if request.method == 'GET':
        # Préremplir le formulaire
        return render(request, 'maintenance/intervention_form_simple.html', {
            'title': f'Modifier l\'intervention "{intervention.titre}"',
            'edit_mode': True,
            'intervention': intervention,
            'technicians': User.objects.filter(user_type='technicien', is_active=True),
            'properties': Property.objects.all(),
            'locataires': Tiers.objects.filter(type_tiers='locataire', statut='actif'),
            'intervention_types': getattr(Intervention, 'TYPE_INTERVENTION_CHOICES', []),
            'priorities': getattr(Intervention, 'PRIORITE_CHOICES', []),
        })
    
    elif request.method == 'POST':
        try:
            # ✅ TRAITEMENT MANUEL DES MODIFICATIONS
            titre = request.POST.get('titre', '').strip()
            description = request.POST.get('description', '').strip()
            type_intervention = request.POST.get('type_intervention', '').strip()
            priorite = request.POST.get('priorite', 'normale')
            
            # Validations
            if not titre:
                raise ValueError("Le titre est obligatoire")
            if not description:
                raise ValueError("La description est obligatoire")
            if not type_intervention:
                raise ValueError("Le type d'intervention est obligatoire")
            
            # Sauvegarder l'ancien technicien pour gérer le changement de statut
            old_technicien = intervention.technicien
            
            # Mettre à jour les champs de base
            intervention.titre = titre
            intervention.description = description
            intervention.type_intervention = type_intervention
            intervention.priorite = priorite
            
            # Champs optionnels
            bien_id = request.POST.get('bien_id')
            if bien_id and Property:
                try:
                    bien = Property.objects.get(id=bien_id)
                    intervention.bien = bien
                except Property.DoesNotExist:
                    intervention.bien = None
            else:
                intervention.bien = None
            
            locataire_id = request.POST.get('locataire_id')
            if locataire_id:
                try:
                    locataire = Tiers.objects.get(id=locataire_id, type_tiers='locataire')
                    intervention.locataire = locataire
                except Tiers.DoesNotExist:
                    intervention.locataire = None
            else:
                intervention.locataire = None
            
            technicien_id = request.POST.get('technicien_id')
            if technicien_id:
                try:
                    technicien = User.objects.get(id=technicien_id, user_type='technicien', is_active=True)
                    intervention.technicien = technicien
                    
                    # Si on assigne pour la première fois
                    if not old_technicien and intervention.statut == 'signale':
                        intervention.statut = 'assigne'
                        intervention.date_assignation = timezone.now()
                        
                except User.DoesNotExist:
                    pass
            else:
                intervention.technicien = None
                # Si on retire l'assignation
                if old_technicien and intervention.statut == 'assigne':
                    intervention.statut = 'signale'
                    intervention.date_assignation = None
            
            cout_estime = request.POST.get('cout_estime')
            if cout_estime:
                try:
                    intervention.cout_estime = float(cout_estime)
                except ValueError:
                    pass
            
            intervention.save()
            
            messages.success(request, f"Intervention '{intervention.titre}' modifiée avec succès!")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Intervention '{intervention.titre}' modifiée avec succès!",
                    'redirect_url': reverse('maintenance:travail_detail', kwargs={'travail_id': travail.id})
                })
            
            return redirect('maintenance:travail_detail', travail_id=travail.id)
            
        except Exception as e:
            error_msg = f"Erreur lors de la modification: {str(e)}"
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            return render(request, 'maintenance/intervention_form_simple.html', {
                'title': f'Modifier l\'intervention "{intervention.titre}"',
                'edit_mode': True,
                'intervention': intervention,
                'technicians': User.objects.filter(user_type='technicien', is_active=True),
                'properties': Property.objects.all(),
                'locataires': Tiers.objects.filter(type_tiers='locataire', statut='actif'),
                'intervention_types': getattr(Intervention, 'TYPE_INTERVENTION_CHOICES', []),
                'priorities': getattr(Intervention, 'PRIORITE_CHOICES', []),
                'error': error_msg,
            })


# ============ VUES POUR TECHNICIENS ============

@login_required
def travail_checklist_view(request, travail_id):
    """Vue checklist simplifiée pour les employés (interface mobile)"""
    travail = get_object_or_404(Travail, id=travail_id)

    # Vérification des permissions - employés seulement
    employee_types = ['technicien', 'technician', 'field_agent', 'employee']
    if travail.technicien != request.user and request.user.user_type not in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas accès à ce travail.")
        # Rediriger vers la liste des interventions mobile si disponible
        try:
            return redirect('employees:mobile_interventions')
        except:
            return redirect('maintenance:travail_detail', travail_id=travail.id)

    # Récupérer les médias associés
    medias = InterventionMedia.objects.filter(travail = intervention).order_by('-created_at')

    context = {
        'travail': intervention,
        'medias': medias,
    }

    return render(request, 'employees/mobile/travail_checklist.html', context)


@login_required
def mes_travaux_view(request):
    """Liste des interventions assignées au technicien connecté"""
    if request.user.user_type != 'technicien':
        messages.error(request, "Seuls les techniciens peuvent accéder à cette page.")
        return redirect('dashboard:index')
    
    # Interventions assignées à ce technicien
    interventions = Travail.objects.filter(
        technicien=request.user
    ).order_by('-date_signalement')
    
    # Filtres
    status_filter = request.GET.get('status', 'active')
    if status_filter == 'active':
        interventions = interventions.filter(statut__in=['assigne', 'en_cours'])
    elif status_filter != 'all':
        interventions = interventions.filter(statut=status_filter)
    
    # Pagination
    paginator = Paginator(interventions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques personnelles
    stats = {
        'assigned': Travail.objects.filter(technicien=request.user, statut='assigne').count(),
        'in_progress': Travail.objects.filter(technicien=request.user, statut='en_cours').count(),
        'completed_today': Travail.objects.filter(
            technicien=request.user,
            statut='complete',
            date_fin__date=timezone.now().date()
        ).count(),
        'total_completed': Travail.objects.filter(technicien=request.user, statut='complete').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'interventions': page_obj.object_list,
        'stats': stats,
        'current_filter': status_filter,
    }
    
    return render(request, 'maintenance/my_interventions.html', context)


# ============ ACTIONS EN MASSE ============

@login_required
@require_http_methods(["POST"])
def travaux_bulk_action(request):
    """Actions en masse sur les interventions"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    action = request.POST.get('action')
    intervention_ids = request.POST.getlist('intervention_ids')
    
    if not action or not intervention_ids:
        return JsonResponse({'success': False, 'error': 'Action ou sélection manquante'})
    
    try:
        interventions = Travail.objects.filter(id__in=intervention_ids)
        count = interventions.count()
        
        if action == 'assign':
            technicien_id = request.POST.get('technicien_id')
            if not technicien_id:
                return JsonResponse({'success': False, 'error': 'Technicien requis'})
            
            technicien = get_object_or_404(User, id=technicien_id, user_type='technicien')
            interventions.filter(statut='signale').update(
                technicien=technicien,
                statut='assigne',
                date_assignation=timezone.now()
            )
            message = f"{count} intervention(s) assignée(s) à {technicien.get_full_name()}"
            
        elif action == 'delete':
            interventions.delete()
            message = f"{count} intervention(s) supprimée(s)"
            
        elif action == 'mark_urgent':
            interventions.update(priorite='urgente')
            message = f"{count} intervention(s) marquée(s) comme urgente(s)"
            
        else:
            return JsonResponse({'success': False, 'error': 'Action non reconnue'})
        
        return JsonResponse({
            'success': True,
            'message': message,
            'count': count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ RECHERCHE ET AUTOCOMPLETE ============

@login_required
def travaux_search(request):
    """Recherche rapide d'interventions"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Permissions
    if request.user.user_type in ['manager', 'accountant']:
        interventions = Travail.objects.all()
    else:
        interventions = Travail.objects.filter(technicien=request.user)
    
    interventions = interventions.filter(
        Q(titre__icontains=query) |
        Q(description__icontains=query) |
        Q(numero_intervention__icontains=query)
    )[:10]
    
    results = []
    for intervention in interventions:
        results.append({
            'id': travail.id,
            'text': travail.titre,
            'subtitle': f"#{getattr(intervention, 'numero_intervention', travail.id)} - {travail.get_statut_display()}",
            'url': reverse('maintenance:travail_detail', kwargs={'travail_id': travail.id}),
            'status': travail.statut,
            'priority': getattr(intervention, 'priorite', 'normale'),
        })
    
    return JsonResponse({'results': results})


# ============ EXPORT ET RAPPORTS ============

@login_required
def travaux_export(request):
    """Export des interventions en CSV"""
    if request.user.user_type not in ['manager', 'accountant']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    try:
        import csv
        from django.http import HttpResponse
        
        # Créer la réponse CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="interventions_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        
        # En-têtes
        headers = [
            'ID', 'Titre', 'Description', 'Type', 'Priorité', 'Statut',
            'Date signalement', 'Technicien', 'Date assignation', 'Date début', 'Date fin',
            'Coût estimé', 'Coût réel'
        ]
        
        headers.append('Bien')
        headers.append('Locataire')

        writer.writerow(headers)

        # Données
        interventions = Travail.objects.all().order_by('-date_signalement')

        for intervention in interventions:
            row = [
                travail.id,
                travail.titre,
                travail.description,
                travail.type_intervention,
                getattr(intervention, 'priorite', ''),
                travail.statut,
                travail.date_signalement.strftime('%Y-%m-%d %H:%M'),
                travail.technicien.get_full_name() if travail.technicien else '',
                travail.date_assignation.strftime('%Y-%m-%d %H:%M') if getattr(intervention, 'date_assignation', None) else '',
                travail.date_debut.strftime('%Y-%m-%d %H:%M') if getattr(intervention, 'date_debut', None) else '',
                travail.date_fin.strftime('%Y-%m-%d %H:%M') if getattr(intervention, 'date_fin', None) else '',
                getattr(intervention, 'cout_estime', ''),
                getattr(intervention, 'cout_reel', '') or getattr(intervention, 'cout_final', ''),
            ]

            row.append(travail.bien.name if travail.bien else '')
            row.append(str(travail.locataire) if travail.locataire else '')
            
            writer.writerow(row)
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ TABLEAU DE BORD MAINTENANCE ============

@login_required
def maintenance_dashboard(request):
    """Tableau de bord maintenance pour managers"""
    if request.user.user_type not in ['manager', 'accountant']:
        return redirect('dashboard:index')
    
    # Statistiques générales
    total_interventions = Travail.objects.count()
    pending_interventions = Travail.objects.filter(statut='signale').count()
    in_progress_interventions = Travail.objects.filter(statut='en_cours').count()
    completed_today = Travail.objects.filter(
        statut='complete',
        date_fin__date=timezone.now().date()
    ).count()
    
    # Interventions urgentes non assignées
    urgent_unassigned = Travail.objects.filter(
        priorite='urgente',
        statut='signale'
    )
    
    # Interventions en retard
    overdue_interventions = Travail.objects.filter(
        statut__in=['assigne', 'en_cours'],
        date_assignation__lt=timezone.now() - timedelta(days=2)
    ) if hasattr(Intervention._meta.get_field('date_assignation'), 'name') else []
    
    # Performance par technicien (dernière semaine)
    last_week = timezone.now() - timedelta(days=7)
    technician_performance = User.objects.filter(
        user_type='technicien',
        is_active=True
    ).annotate(
        completed_interventions=Count(
            'interventions_technicien',
            filter=Q(
                interventions_technicien__statut='complete',
                interventions_technicien__date_fin__gte=last_week
            )
        ),
        pending_interventions=Count(
            'interventions_technicien',
            filter=Q(interventions_technicien__statut__in=['assigne', 'en_cours'])
        )
    )
    
    context = {
        'stats': {
            'total_interventions': total_interventions,
            'pending_interventions': pending_interventions,
            'in_progress_interventions': in_progress_interventions,
            'completed_today': completed_today,
            'urgent_unassigned': urgent_unassigned.count(),
            'overdue_interventions': len(overdue_interventions),
        },
        'urgent_unassigned': urgent_unassigned[:5],
        'overdue_interventions': overdue_interventions[:5] if overdue_interventions else [],
        'technician_performance': technician_performance,
        'recent_interventions': Travail.objects.order_by('-date_signalement')[:10],
    }
    
    return render(request, 'maintenance/dashboard.html', context)