# apps/properties/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum
from django.urls import reverse_lazy, reverse
from .forms import EtatDesLieuxForm, EtatDesLieuxDetailFormSet, RemiseDesClesForm
from .models import EtatDesLieux, EtatDesLieuxDetail, RemiseDesCles
from django.utils import timezone
from .utils import generate_etat_lieux_pdf, generate_etat_lieux_filename, generate_remise_cles_pdf, generate_remise_cles_filename
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.http import HttpResponse
import json

# ✅ IMPORTS CORRECTS SELON LES MODÈLES EXISTANTS
from .models import Residence, Appartement, AppartementMedia
from .forms import ResidenceForm, AppartementForm, AppartementMediaForm

# ✅ IMPORTS CONDITIONNELS POUR ÉVITER LES ERREURS
try:
    from .models import Property  # Pour compatibilité
except ImportError:
    Property = None

try:
    from .forms import AppartementFilterForm, QuickAppartementForm
except ImportError:
    AppartementFilterForm = None
    QuickAppartementForm = None

# Import direct de Tiers (remplace l'ancien Bailleur)
from apps.tiers.models import Tiers


# ================= FORMS MANQUANTS À CRÉER DANS forms.py =================
"""
Les forms suivants doivent être créés dans properties/forms.py :

class AppartementFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Rechercher...',
        'class': 'form-control'
    }))
    type_bien = forms.ChoiceField(
        choices=[('', 'Tous')] + Appartement.TYPE_BIEN_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    statut = forms.ChoiceField(
        choices=[('', 'Tous')] + Appartement.STATUT_OCCUPATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    residence = forms.ModelChoiceField(
        queryset=Residence.objects.filter(statut='active'),
        required=False,
        empty_label="Toutes les résidences",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class QuickAppartementForm(forms.ModelForm):
    class Meta:
        model = Appartement
        fields = ['nom', 'residence', 'type_bien', 'etage', 'superficie', 'nb_pieces', 'loyer_base']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'residence': forms.Select(attrs={'class': 'form-select'}),
            'type_bien': forms.Select(attrs={'class': 'form-select'}),
            'etage': forms.NumberInput(attrs={'class': 'form-control'}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nb_pieces': forms.NumberInput(attrs={'class': 'form-control'}),
            'loyer_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
"""


# ============ VUES DE REDIRECTION ============

@login_required
def properties_redirect_view(request):
    """Redirige vers le dashboard des biens"""
    return redirect('dashboard:properties_overview')


@login_required
def appartement_detail_redirect(request, pk):
    """Redirige intelligemment vers le détail d'appartement"""
    try:
        # Essayer d'abord avec Appartement
        appartement = get_object_or_404(Appartement, pk=pk)
        return redirect('properties:appartement_detail', pk=pk)
    except:
        # Sinon essayer avec l'ancien Property
        if Property:
            try:
                property = get_object_or_404(Property, pk=pk)
                # Rediriger vers l'admin pour l'ancien modèle
                return redirect(f'/admin/properties/property/{pk}/change/')
            except:
                pass
        raise Http404("Bien non trouvé")


@login_required
def appartement_edit_redirect(request, pk):
    """Redirige intelligemment vers l'édition d'appartement"""
    try:
        appartement = get_object_or_404(Appartement, pk=pk)
        return redirect('properties:appartement_edit', pk=pk)
    except:
        if Property:
            try:
                property = get_object_or_404(Property, pk=pk)
                return redirect(f'/admin/properties/property/{pk}/change/')
            except:
                pass
        raise Http404("Bien non trouvé")


# ============ VUES RESIDENCES ============

class ResidenceListView(LoginRequiredMixin, ListView):
    """Vue liste des résidences"""
    model = Residence
    template_name = 'properties/residences_list.html'
    context_object_name = 'residences'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # ✅ QUERYSET SIMPLE SANS ANNOTATIONS
        queryset = Residence.objects.all()

        # ✅ RELATIONS AVEC TIERS
        queryset = queryset.select_related('proprietaire')
        queryset = queryset.prefetch_related('appartements')

        # Filtres
        search = self.request.GET.get('search', '')
        if search:
            filters = Q(nom__icontains=search) | Q(quartier__icontains=search) | Q(ville__icontains=search)
            filters |= Q(proprietaire__nom__icontains=search) | Q(proprietaire__prenom__icontains=search)
            queryset = queryset.filter(filters)

        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ✅ CALCUL MANUEL DES STATISTIQUES GLOBALES SEULEMENT
        all_residences = Residence.objects.prefetch_related('appartements').all()
        total_appartements = 0
        total_libres = 0
        total_occupes = 0
        
        for residence in all_residences:
            appartements = residence.appartements.all()
            total_appartements += appartements.count()
            total_libres += appartements.filter(statut_occupation__in=['libre', 'available']).count()
            total_occupes += appartements.filter(statut_occupation__in=['occupe', 'occupied']).count()
        
        context.update({
            'search': self.request.GET.get('search', ''),
            'total_residences': all_residences.count(),
            'total_appartements': total_appartements,
            'total_libres': total_libres,
            'total_occupes': total_occupes,
        })
        
        return context


class ResidenceDetailView(LoginRequiredMixin, DetailView):
    """Vue détail d'une résidence avec ses appartements"""
    model = Residence
    template_name = 'properties/residence_detail.html'
    context_object_name = 'residence'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        appartements = self.object.appartements.all().order_by('etage', 'nom')
        
        context.update({
            'appartements': appartements,
            'stats': {
                'total': appartements.count(),
                'libres': appartements.filter(statut_occupation__in=['libre', 'available']).count(),
                'occupes': appartements.filter(statut_occupation__in=['occupe', 'occupied']).count(),
                'maintenance': appartements.filter(statut_occupation='maintenance').count(),
            }
        })
        
        return context


class ResidenceCreateView(LoginRequiredMixin, CreateView):
    """Vue création d'une résidence"""
    model = Residence
    form_class = ResidenceForm
    template_name = 'properties/residence_form.html'
    success_url = reverse_lazy('properties:residences_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de créer des résidences.")
            return redirect('properties:residences_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, f'Résidence "{form.instance.nom}" créée avec succès!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Nouvelle résidence',
            'edit_mode': False
        })
        return context


class ResidenceUpdateView(LoginRequiredMixin, UpdateView):
    """Vue modification d'une résidence"""
    model = Residence
    form_class = ResidenceForm
    template_name = 'properties/residence_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de modifier des résidences.")
            return redirect('properties:residence_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('properties:residence_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Résidence "{form.instance.nom}" modifiée avec succès!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Modifier la résidence "{self.object.nom}"',
            'edit_mode': True,
            'residence': self.object
        })
        return context


class ResidenceDeleteView(LoginRequiredMixin, DeleteView):
    """Vue suppression d'une résidence"""
    model = Residence
    template_name = 'properties/residence_confirm_delete.html'
    success_url = reverse_lazy('properties:residences_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de supprimer des résidences.")
            return redirect('properties:residence_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        residence = self.get_object()
        if residence.appartements.exists():
            messages.error(request, "Impossible de supprimer une résidence qui contient des appartements.")
            return redirect('properties:residence_detail', pk=residence.pk)
        
        residence_nom = residence.nom
        messages.success(request, f'Résidence "{residence_nom}" supprimée avec succès!')
        return super().delete(request, *args, **kwargs)


# ============ VUES APPARTEMENTS ============

class AppartementListView(LoginRequiredMixin, ListView):
    """Vue liste des appartements"""
    model = Appartement
    template_name = 'properties/appartements_list.html'
    context_object_name = 'appartements'
    paginate_by = 24
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Appartement.objects.select_related('residence', 'residence__proprietaire').prefetch_related('medias')

        # Filtres
        search = self.request.GET.get('search', '')
        type_bien = self.request.GET.get('type_bien', '')
        statut = self.request.GET.get('statut', '')
        residence_id = self.request.GET.get('residence', '')
        ville = self.request.GET.get('ville', '')
        
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(reference__icontains=search) |
                Q(residence__nom__icontains=search) |
                Q(residence__quartier__icontains=search)
            )
        
        if type_bien:
            queryset = queryset.filter(type_bien=type_bien)
        
        if statut:
            queryset = queryset.filter(statut_occupation=statut)
        
        if residence_id:
            queryset = queryset.filter(residence_id=residence_id)
        
        if ville:
            queryset = queryset.filter(residence__ville__icontains=ville)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        all_appartements = self.get_queryset()
        
        context.update({
            # ✅ FILTRES SIMPLES SANS FORM MANQUANT
            'current_filters': {
                'search': self.request.GET.get('search', ''),
                'type_bien': self.request.GET.get('type_bien', ''),
                'statut': self.request.GET.get('statut', ''),
                'residence': self.request.GET.get('residence', ''),
                'ville': self.request.GET.get('ville', ''),
            },
            'stats': {
                'total': all_appartements.count(),
                'libres': all_appartements.filter(statut_occupation__in=['libre', 'available']).count(),
                'occupes': all_appartements.filter(statut_occupation__in=['occupe', 'occupied']).count(),
                'maintenance': all_appartements.filter(statut_occupation='maintenance').count(),
            },
            'search': self.request.GET.get('search', ''),
            
            # Données pour les filtres
            'residences': Residence.objects.filter(statut='active')[:50],
            'type_bien_choices': getattr(Appartement, 'TYPE_BIEN_CHOICES', []),
            'statut_choices': getattr(Appartement, 'STATUT_OCCUPATION_CHOICES', []),
        })
        
        return context


class AppartementDetailView(LoginRequiredMixin, DetailView):
    """Vue détail d'un appartement"""
    model = Appartement
    template_name = 'properties/appartement_detail.html'
    context_object_name = 'appartement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Médias de l'appartement
        medias = self.object.medias.filter(is_public=True).order_by('ordre', '-created_at')
        
        # ✅ CONTRAT ACTUEL CONDITIONNEL
        contrat_actuel = None
        historique_contrats = []
        
        try:
            from apps.contracts.models import RentalContract
            contrat_actuel = getattr(self.object, 'contrat_actuel', None)
            historique_contrats = RentalContract.objects.filter(
                appartement=self.object
            ).order_by('-date_debut')[:5]
        except ImportError:
            pass
        
        context.update({
            'medias': medias,
            'contrat_actuel': contrat_actuel,
            'historique_contrats': historique_contrats,
            'can_edit': self.request.user.user_type in ['manager', 'accountant'],
        })
        
        return context


class AppartementCreateView(LoginRequiredMixin, CreateView):
    """Vue création d'un appartement"""
    model = Appartement
    form_class = AppartementForm
    template_name = 'properties/appartement_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de créer des appartements.")
            return redirect('properties:appartements_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('properties:appartement_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Appartement "{form.instance.nom}" créé avec succès!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Nouvel appartement',
            'edit_mode': False
        })
        return context


class AppartementUpdateView(LoginRequiredMixin, UpdateView):
    """Vue modification d'un appartement"""
    model = Appartement
    form_class = AppartementForm
    template_name = 'properties/appartement_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de modifier des appartements.")
            return redirect('properties:appartement_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('properties:appartement_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Appartement "{form.instance.nom}" modifié avec succès!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': f'Modifier l\'appartement "{self.object.nom}"',
            'edit_mode': True,
            'appartement': self.object
        })
        return context


class AppartementDeleteView(LoginRequiredMixin, DeleteView):
    """Vue suppression d'un appartement"""
    model = Appartement
    template_name = 'properties/appartement_confirm_delete.html'
    success_url = reverse_lazy('properties:appartements_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['manager', 'accountant']:
            messages.error(request, "Vous n'avez pas l'autorisation de supprimer des appartements.")
            return redirect('properties:appartement_detail', pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        appartement = self.get_object()
        
        # ✅ VÉRIFICATION CONDITIONNELLE DU CONTRAT ACTUEL
        has_active_contract = False
        try:
            has_active_contract = bool(getattr(appartement, 'contrat_actuel', None))
        except:
            pass
        
        if has_active_contract:
            messages.error(request, "Impossible de supprimer un appartement avec un contrat actif.")
            return redirect('properties:appartement_detail', pk=appartement.pk)
        
        appartement_nom = appartement.nom
        messages.success(request, f'Appartement "{appartement_nom}" supprimé avec succès!')
        return super().delete(request, *args, **kwargs)


# ============ ACTIONS SUR APPARTEMENTS ============

@login_required
@require_http_methods(["POST"])
def set_appartement_available(request, pk):
    """Marquer un appartement comme disponible"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    appartement = get_object_or_404(Appartement, pk=pk)
    appartement.statut_occupation = 'libre'
    appartement.save()
    
    messages.success(request, f'Appartement "{appartement.nom}" marqué comme disponible.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'statut': 'libre'})
    
    return redirect('properties:appartement_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def set_appartement_occupied(request, pk):
    """Marquer un appartement comme occupé"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    appartement = get_object_or_404(Appartement, pk=pk)
    appartement.statut_occupation = 'occupe'
    appartement.save()
    
    messages.success(request, f'Appartement "{appartement.nom}" marqué comme occupé.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'statut': 'occupe'})
    
    return redirect('properties:appartement_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def set_appartement_maintenance(request, pk):
    """Marquer un appartement en maintenance"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    appartement = get_object_or_404(Appartement, pk=pk)
    appartement.statut_occupation = 'maintenance'
    appartement.save()
    
    messages.success(request, f'Appartement "{appartement.nom}" marqué en maintenance.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'statut': 'maintenance'})
    
    return redirect('properties:appartement_detail', pk=pk)


# ============ GESTION DES MÉDIAS ============

class AppartementMediaListView(LoginRequiredMixin, ListView):
    """Vue liste des médias d'un appartement"""
    model = AppartementMedia
    template_name = 'properties/appartement_medias.html'
    context_object_name = 'medias'
    
    def get_queryset(self):
        self.appartement = get_object_or_404(Appartement, pk=self.kwargs['appartement_id'])
        return self.appartement.medias.all().order_by('ordre', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appartement'] = self.appartement
        return context


@login_required
@require_http_methods(["POST"])
def upload_appartement_media(request, appartement_id):
    """Upload d'un média pour un appartement"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    appartement = get_object_or_404(Appartement, pk=appartement_id)
    
    if request.method == 'POST' and request.FILES.get('fichier'):
        try:
            media = AppartementMedia.objects.create(
                appartement=appartement,
                type_media=request.POST.get('type_media', 'photo_interieur'),
                fichier=request.FILES['fichier'],
                titre=request.POST.get('titre', ''),
                description=request.POST.get('description', ''),
                is_principal=request.POST.get('is_principal') == 'on',
                ordre=int(request.POST.get('ordre', 0)),
            )
            
            return JsonResponse({
                'success': True,
                'media_id': media.id,
                'file_url': media.fichier.url if media.fichier else None,
                'message': 'Fichier uploadé avec succès!'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'})


@login_required
@require_http_methods(["POST"])
def delete_appartement_media(request, media_id):
    """Supprimer un média d'appartement"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    try:
        media = get_object_or_404(AppartementMedia, pk=media_id)
        media.delete()
        return JsonResponse({'success': True, 'message': 'Média supprimé avec succès'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def set_main_media(request, media_id):
    """Définir un média comme principal"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    try:
        media = get_object_or_404(AppartementMedia, pk=media_id)
        
        # Enlever le statut principal des autres médias du même appartement
        AppartementMedia.objects.filter(
            appartement=media.appartement,
            is_principal=True
        ).update(is_principal=False)
        
        # Définir celui-ci comme principal
        media.is_principal = True
        media.save()
        
        return JsonResponse({'success': True, 'message': 'Média principal défini'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ APIs POUR AJAX ============

@login_required
@require_http_methods(["GET"])
def residences_by_landlord_api(request, landlord_id):
    """API pour récupérer les résidences d'un propriétaire (Tiers)"""
    try:
        residences = Residence.objects.filter(
            proprietaire_id=landlord_id,
            statut='active'
        ).values('id', 'nom', 'quartier')

        return JsonResponse({
            'success': True,
            'residences': list(residences)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def appartements_by_residence_api(request, residence_id):
    """API pour récupérer les appartements d'une résidence"""
    try:
        appartements = Appartement.objects.filter(
            residence_id=residence_id
        ).values('id', 'nom', 'statut_occupation', 'loyer_base', 'type_bien')
        
        return JsonResponse({
            'success': True,
            'appartements': list(appartements)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def appartement_info_api(request, pk):
    """API pour récupérer les informations détaillées d'un appartement"""
    try:
        appartement = Appartement.objects.select_related('residence', 'residence__proprietaire').get(pk=pk)

        # ✅ DONNÉES PROPRIETAIRE
        proprietaire_data = {}
        if appartement.residence.proprietaire:
            proprietaire = appartement.residence.proprietaire
            proprietaire_data = {
                'nom': proprietaire.nom_complet,
                'email': proprietaire.email,
            }

        data = {
            'id': appartement.id,
            'nom': appartement.nom,
            'reference': appartement.reference,
            'residence': {
                'nom': appartement.residence.nom,
                'adresse': appartement.residence.adresse,
                'quartier': appartement.residence.quartier,
            },
            'type_bien': appartement.get_type_bien_display(),
            'superficie': float(appartement.superficie) if appartement.superficie else None,
            'nb_pieces': appartement.nb_pieces,
            'nb_chambres': getattr(appartement, 'nb_chambres', None),
            'loyer_base': float(appartement.loyer_base),
            'loyer_total': float(getattr(appartement, 'loyer_total', appartement.loyer_base)),
            'statut_occupation': appartement.get_statut_occupation_display(),
            'is_available': getattr(appartement, 'is_available', appartement.statut_occupation in ['libre', 'available']),
            'proprietaire': proprietaire_data
        }

        return JsonResponse({'success': True, 'data': data})

    except Appartement.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Appartement non trouvé'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def residence_stats_api(request, pk):
    """API pour les statistiques d'une résidence"""
    try:
        residence = get_object_or_404(Residence, pk=pk)
        
        appartements = residence.appartements.all()
        
        # ✅ CALCULS CONDITIONNELS SELON LES CHAMPS DISPONIBLES
        revenus_mensuels = 0
        try:
            revenus_mensuels = float(
                appartements.filter(
                    statut_occupation__in=['occupe', 'occupied']
                ).aggregate(total=Sum('loyer_base'))['total'] or 0
            )
        except:
            pass
        
        taux_occupation = 0
        try:
            taux_occupation = getattr(residence, 'taux_occupation', 0)
            if not taux_occupation:
                total = appartements.count()
                occupes = appartements.filter(statut_occupation__in=['occupe', 'occupied']).count()
                taux_occupation = (occupes / total * 100) if total > 0 else 0
        except:
            pass
        
        stats = {
            'total_appartements': appartements.count(),
            'appartements_libres': appartements.filter(statut_occupation__in=['libre', 'available']).count(),
            'appartements_occupes': appartements.filter(statut_occupation__in=['occupe', 'occupied']).count(),
            'appartements_maintenance': appartements.filter(statut_occupation='maintenance').count(),
            'revenus_mensuels_estimes': revenus_mensuels,
            'taux_occupation': round(taux_occupation, 1),
        }
        
        return JsonResponse({'success': True, 'stats': stats})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ EXPORTS ============

@login_required
def export_residences_csv(request):
    """Export des résidences en CSV"""
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Permission refusée")
        return redirect('properties:residences_list')
    
    try:
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="residences_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Référence', 'Nom', 'Type', 'Adresse', 'Quartier', 'Ville',
            'Nb Étages', 'Nb Appartements', 'Bailleur', 'Statut'
        ])
        
        residences = Residence.objects.select_related('proprietaire').all()

        for residence in residences:
            proprietaire_nom = ''
            if residence.proprietaire:
                proprietaire_nom = residence.proprietaire.nom_complet

            writer.writerow([
                getattr(residence, 'reference', ''),
                residence.nom,
                residence.get_type_residence_display() if hasattr(residence, 'get_type_residence_display') else '',
                residence.adresse,
                residence.quartier,
                residence.ville,
                getattr(residence, 'nb_etages', ''),
                getattr(residence, 'nb_appartements_total', residence.appartements.count()),
                proprietaire_nom,
                residence.get_statut_display() if hasattr(residence, 'get_statut_display') else residence.statut
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'export: {str(e)}")
        return redirect('properties:residences_list')


@login_required
def export_appartements_csv(request):
    """Export des appartements en CSV"""
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Permission refusée")
        return redirect('properties:appartements_list')
    
    try:
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="appartements_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Référence', 'Nom', 'Résidence', 'Type', 'Étage', 'Superficie',
            'Nb Pièces', 'Loyer Base', 'Charges', 'Statut', 'Bailleur'
        ])
        
        appartements = Appartement.objects.select_related('residence', 'residence__proprietaire')

        for appartement in appartements:
            proprietaire_nom = ''
            if appartement.residence.proprietaire:
                proprietaire_nom = appartement.residence.proprietaire.nom_complet

            writer.writerow([
                getattr(appartement, 'reference', ''),
                appartement.nom,
                appartement.residence.nom,
                appartement.get_type_bien_display() if hasattr(appartement, 'get_type_bien_display') else '',
                getattr(appartement, 'etage', ''),
                getattr(appartement, 'superficie', ''),
                getattr(appartement, 'nb_pieces', ''),
                appartement.loyer_base,
                getattr(appartement, 'charges', 0),
                appartement.get_statut_occupation_display() if hasattr(appartement, 'get_statut_occupation_display') else appartement.statut_occupation,
                proprietaire_nom
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'export: {str(e)}")
        return redirect('properties:appartements_list')


# ============ RAPPORTS ============

@login_required
def rapport_occupation_view(request):
    """Rapport d'occupation des biens"""
    if not request.user.user_type in ['manager', 'accountant']:
        return redirect('dashboard:index')
    
    # Statistiques globales
    total_appartements = Appartement.objects.count()
    appartements_libres = Appartement.objects.filter(
        statut_occupation__in=['libre', 'available']
    ).count()
    appartements_occupes = Appartement.objects.filter(
        statut_occupation__in=['occupe', 'occupied']
    ).count()
    appartements_maintenance = Appartement.objects.filter(
        statut_occupation='maintenance'
    ).count()
    
    taux_occupation_global = (appartements_occupes / total_appartements * 100) if total_appartements > 0 else 0
    
    # Occupation par résidence
    residences_stats = Residence.objects.annotate(
        total_appartements=Count('appartements'),
        appartements_libres=Count(
            'appartements',
            filter=Q(appartements__statut_occupation__in=['libre', 'available'])
        ),
        appartements_occupes=Count(
            'appartements',
            filter=Q(appartements__statut_occupation__in=['occupe', 'occupied'])
        ),
        revenus_estimes=Sum(
            'appartements__loyer_base',
            filter=Q(appartements__statut_occupation__in=['occupe', 'occupied'])
        )
    )
    
    context = {
        'stats_globales': {
            'total_appartements': total_appartements,
            'appartements_libres': appartements_libres,
            'appartements_occupes': appartements_occupes,
            'appartements_maintenance': appartements_maintenance,
            'taux_occupation_global': round(taux_occupation_global, 1),
        },
        'residences_stats': residences_stats,
    }
    
    return render(request, 'properties/rapport_occupation.html', context)


@login_required
def rapport_residences_view(request):
    """Rapport détaillé des résidences"""
    if not request.user.user_type in ['manager', 'accountant']:
        return redirect('dashboard:index')
    
    residences = Residence.objects.select_related('proprietaire').prefetch_related('appartements').annotate(
        total_appartements=Count('appartements'),
        revenus_potentiels=Sum('appartements__loyer_base'),
        revenus_actuels=Sum(
            'appartements__loyer_base',
            filter=Q(appartements__statut_occupation__in=['occupe', 'occupied'])
        )
    )

    context = {
        'residences': residences,
    }
    
    return render(request, 'properties/rapport_residences.html', context)


# ============ VUES SPÉCIALES ============

@login_required
def property_selection_view(request):
    """Vue pour sélectionner un bien (pour les contrats par exemple)"""
    appartements = Appartement.objects.select_related('residence').filter(
        statut_occupation__in=['libre', 'available']
    )
    
    # Grouper par résidence
    residences_data = {}
    for appartement in appartements:
        residence_id = appartement.residence.id
        if residence_id not in residences_data:
            residences_data[residence_id] = {
                'residence': appartement.residence,
                'appartements': []
            }
        residences_data[residence_id]['appartements'].append(appartement)
    
    context = {
        'residences_data': residences_data,
    }
    
    return render(request, 'properties/property_selection.html', context)


@login_required
def property_search_view(request):
    """Vue de recherche avancée de biens"""
    query = request.GET.get('q', '')
    type_bien = request.GET.get('type', '')
    prix_min = request.GET.get('prix_min', '')
    prix_max = request.GET.get('prix_max', '')
    ville = request.GET.get('ville', '')
    
    appartements = Appartement.objects.select_related('residence')
    
    if query:
        appartements = appartements.filter(
            Q(nom__icontains=query) |
            Q(residence__nom__icontains=query) |
            Q(residence__quartier__icontains=query)
        )
    
    if type_bien:
        appartements = appartements.filter(type_bien=type_bien)
    
    if prix_min:
        try:
            appartements = appartements.filter(loyer_base__gte=float(prix_min))
        except ValueError:
            pass
    
    if prix_max:
        try:
            appartements = appartements.filter(loyer_base__lte=float(prix_max))
        except ValueError:
            pass
    
    if ville:
        appartements = appartements.filter(residence__ville__icontains=ville)
    
    # Pagination
    paginator = Paginator(appartements, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'appartements': page_obj.object_list,
        'query': query,
        'type_bien': type_bien,
        'prix_min': prix_min,
        'prix_max': prix_max,
        'ville': ville,
        'total_results': appartements.count(),
    }
    
    return render(request, 'properties/property_search.html', context)


# ============ CRÉATIONS RAPIDES ============

@login_required
@require_http_methods(["GET", "POST"])
def quick_add_appartement(request):
    """Vue pour ajouter rapidement un appartement"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    if request.method == 'GET':
        # Retourner le formulaire de création rapide
        residences = Residence.objects.filter(statut='active')
        type_bien_choices = getattr(Appartement, 'TYPE_BIEN_CHOICES', [])
        
        return render(request, 'properties/quick_add_appartement.html', {
            'residences': residences,
            'type_bien_choices': type_bien_choices,
        })
    
    elif request.method == 'POST':
        try:
            # ✅ TRAITEMENT MANUEL SANS FORM
            nom = request.POST.get('nom', '').strip()
            residence_id = request.POST.get('residence_id')
            type_bien = request.POST.get('type_bien', 'appartement')
            etage = request.POST.get('etage', 0)
            superficie = request.POST.get('superficie', 0)
            nb_pieces = request.POST.get('nb_pieces', 1)
            loyer_base = request.POST.get('loyer_base', 0)
            
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
                superficie=float(superficie) if superficie else None,
                nb_pieces=int(nb_pieces) if nb_pieces else 1,
                loyer_base=float(loyer_base) if loyer_base else 0,
                statut_occupation='libre',
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'appartement_id': appartement.id,
                    'appartement_name': str(appartement),
                    'message': f'Appartement "{appartement.nom}" créé avec succès!'
                })
            
            messages.success(request, f'Appartement "{appartement.nom}" créé avec succès!')
            return redirect('properties:appartement_detail', pk=appartement.id)
            
        except Exception as e:
            error_msg = f"Erreur lors de la création: {str(e)}"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            messages.error(request, error_msg)
            return redirect('properties:quick_add_appartement')


@login_required
@require_http_methods(["GET", "POST"])
def quick_add_residence(request):
    """Vue pour ajouter rapidement une résidence"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    if request.method == 'GET':
        # Retourner le formulaire de création rapide
        proprietaires = Tiers.objects.filter(type_tiers='proprietaire').order_by('nom', 'prenom')

        type_residence_choices = getattr(Residence, 'TYPE_RESIDENCE_CHOICES', [])

        return render(request, 'properties/quick_add_residence.html', {
            'proprietaires': proprietaires,
            'type_residence_choices': type_residence_choices,
        })
    
    elif request.method == 'POST':
        try:
            # ✅ TRAITEMENT MANUEL SANS FORM
            nom = request.POST.get('nom', '').strip()
            adresse = request.POST.get('adresse', '').strip()
            quartier = request.POST.get('quartier', '').strip()
            ville = request.POST.get('ville', '').strip()
            type_residence = request.POST.get('type_residence', 'immeuble')
            proprietaire_id = request.POST.get('proprietaire_id')

            # Validations
            if not nom:
                raise ValueError("Le nom est obligatoire")
            if not adresse:
                raise ValueError("L'adresse est obligatoire")
            if not ville:
                raise ValueError("La ville est obligatoire")

            # Données de base
            residence_data = {
                'nom': nom,
                'adresse': adresse,
                'quartier': quartier,
                'ville': ville,
                'type_residence': type_residence,
                'statut': 'active',
            }

            # Propriétaire optionnel
            if proprietaire_id:
                try:
                    proprietaire = Tiers.objects.get(id=proprietaire_id, type_tiers='proprietaire')
                    residence_data['proprietaire'] = proprietaire
                except Tiers.DoesNotExist:
                    pass

            # Créer la résidence
            residence = Residence.objects.create(**residence_data)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'residence_id': residence.id,
                    'residence_name': str(residence),
                    'message': f'Résidence "{residence.nom}" créée avec succès!'
                })
            
            messages.success(request, f'Résidence "{residence.nom}" créée avec succès!')
            return redirect('properties:residence_detail', pk=residence.id)
            
        except Exception as e:
            error_msg = f"Erreur lors de la création: {str(e)}"
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': error_msg})
            
            messages.error(request, error_msg)
            return redirect('properties:quick_add_residence')


# ============ ACTIONS EN MASSE ============

@login_required
@require_http_methods(["POST"])
def appartements_bulk_action(request):
    """Actions en masse sur les appartements"""
    if not request.user.user_type in ['manager', 'accountant']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    action = request.POST.get('action')
    appartement_ids = request.POST.getlist('appartement_ids')
    
    if not action or not appartement_ids:
        return JsonResponse({'success': False, 'error': 'Action ou sélection manquante'})
    
    try:
        appartements = Appartement.objects.filter(id__in=appartement_ids)
        count = appartements.count()
        
        if action == 'set_available':
            appartements.update(statut_occupation='libre')
            message = f"{count} appartement(s) marqué(s) comme disponible(s)"
            
        elif action == 'set_maintenance':
            appartements.update(statut_occupation='maintenance')
            message = f"{count} appartement(s) marqué(s) en maintenance"
            
        elif action == 'delete':
            # Vérifier qu'aucun appartement n'a de contrat actif
            for appartement in appartements:
                if getattr(appartement, 'contrat_actuel', None):
                    return JsonResponse({
                        'success': False, 
                        'error': f'L\'appartement "{appartement.nom}" a un contrat actif'
                    })
            
            appartements.delete()
            message = f"{count} appartement(s) supprimé(s)"
            
        else:
            return JsonResponse({'success': False, 'error': 'Action non reconnue'})
        
        return JsonResponse({
            'success': True,
            'message': message,
            'count': count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============ TABLEAU DE BORD PROPERTIES ============

@login_required
def properties_dashboard(request):
    """Tableau de bord des propriétés"""
    if not request.user.user_type in ['manager', 'accountant']:
        return redirect('dashboard:index')
    
    # Statistiques générales
    total_residences = Residence.objects.count()
    total_appartements = Appartement.objects.count()
    appartements_libres = Appartement.objects.filter(
        statut_occupation__in=['libre', 'available']
    ).count()
    appartements_occupes = Appartement.objects.filter(
        statut_occupation__in=['occupe', 'occupied']
    ).count()
    
    # Revenus mensuels estimés
    revenus_mensuels = Appartement.objects.filter(
        statut_occupation__in=['occupe', 'occupied']
    ).aggregate(total=Sum('loyer_base'))['total'] or 0
    
    # Résidences avec plus d'infos
    residences_recent = Residence.objects.annotate(
        nb_appartements=Count('appartements'),
        taux_occupation_calc=Count(
            'appartements',
            filter=Q(appartements__statut_occupation__in=['occupe', 'occupied'])
        ) * 100.0 / Count('appartements')
    ).order_by('-created_at')[:5]
    
    # Appartements récemment libérés
    appartements_libres_recent = Appartement.objects.filter(
        statut_occupation__in=['libre', 'available']
    ).select_related('residence').order_by('-updated_at')[:10]
    
    context = {
        'stats': {
            'total_residences': total_residences,
            'total_appartements': total_appartements,
            'appartements_libres': appartements_libres,
            'appartements_occupes': appartements_occupes,
            'taux_occupation_global': (appartements_occupes / total_appartements * 100) if total_appartements > 0 else 0,
            'revenus_mensuels': float(revenus_mensuels),
        },
        'residences_recent': residences_recent,
        'appartements_libres_recent': appartements_libres_recent,
    }
    
    return render(request, 'properties/dashboard.html', context)



@login_required
def etat_lieux_list_view(request):
    """Liste des états des lieux"""
    etats = EtatDesLieux.objects.select_related(
        'appartement', 'appartement__residence', 'locataire', 'contrat'
    ).order_by('-date_etat')
    
    # Filtres
    type_filter = request.GET.get('type', '')
    appartement_filter = request.GET.get('appartement', '')
    
    if type_filter:
        etats = etats.filter(type_etat=type_filter)
    if appartement_filter:
        etats = etats.filter(appartement_id=appartement_filter)
    
    context = {
        'etats': etats,
        'type_filter': type_filter,
        'appartement_filter': appartement_filter,
    }
    
    return render(request, 'properties/etat_lieux_list.html', context)


@login_required
def etat_lieux_create_view(request):
    """Créer un nouvel état des lieux"""
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des états des lieux.")
        return redirect('properties:etat_lieux_list')

    # Récupérer les paramètres de l'URL pour pré-remplir le formulaire
    workflow_id = request.GET.get('workflow')
    contrat_id = request.GET.get('contrat')

    workflow = None
    contrat = None
    initial_data = {'type_etat': 'entree'}  # Par défaut: entrée

    if contrat_id:
        try:
            from apps.contracts.models import RentalContract
            contrat = RentalContract.objects.select_related(
                'appartement', 'locataire'
            ).get(pk=contrat_id)
            initial_data.update({
                'contrat': contrat,
                'appartement': contrat.appartement,
                'locataire': contrat.locataire,
            })
        except:
            pass

    if workflow_id:
        try:
            from apps.contracts.models import ContractWorkflow
            workflow = ContractWorkflow.objects.select_related('contrat').get(pk=workflow_id)
        except:
            pass

    if request.method == 'POST':
        form = EtatDesLieuxForm(request.POST)
        formset = EtatDesLieuxDetailFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            etat = form.save(commit=False)
            etat.cree_par = request.user
            etat.save()

            # Sauvegarder les détails
            formset.instance = etat
            formset.save()

            messages.success(request, f"État des lieux {etat.numero_etat} créé avec succès!")

            # Rediriger vers le workflow si on vient de là
            if workflow_id:
                messages.info(request, "Vous pouvez maintenant télécharger le PDF et l'uploader signé dans le workflow.")
                return redirect('properties:etat_lieux_detail', pk=etat.pk)

            return redirect('properties:etat_lieux_detail', pk=etat.pk)
    else:
        form = EtatDesLieuxForm(initial=initial_data)
        formset = EtatDesLieuxDetailFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Nouvel État des Lieux',
        'workflow': workflow,
        'from_workflow': bool(workflow_id),
    }

    return render(request, 'properties/etat_lieux_form.html', context)


@login_required
def etat_lieux_detail_view(request, pk):
    """Détail d'un état des lieux"""
    etat = get_object_or_404(
        EtatDesLieux.objects.select_related(
            'appartement', 'appartement__residence', 'locataire', 'contrat', 'cree_par'
        ).prefetch_related('details'),
        pk=pk
    )
    
    context = {
        'etat': etat,
        'details': etat.details.all().order_by('ordre', 'piece'),
    }
    
    return render(request, 'properties/etat_lieux_detail.html', context)


@login_required
def etat_lieux_edit_view(request, pk):
    """Éditer un état des lieux"""
    etat = get_object_or_404(EtatDesLieux, pk=pk)
    
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier des états des lieux.")
        return redirect('properties:etat_lieux_detail', pk=pk)
    
    if request.method == 'POST':
        form = EtatDesLieuxForm(request.POST, instance=etat)
        formset = EtatDesLieuxDetailFormSet(request.POST, instance=etat)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            messages.success(request, f"État des lieux {etat.numero_etat} modifié avec succès!")
            return redirect('properties:etat_lieux_detail', pk=etat.pk)
    else:
        form = EtatDesLieuxForm(instance=etat)
        formset = EtatDesLieuxDetailFormSet(instance=etat)
    
    context = {
        'form': form,
        'formset': formset,
        'etat': etat,
        'title': f'Modifier État des Lieux {etat.numero_etat}',
    }
    
    return render(request, 'properties/etat_lieux_form.html', context)


@login_required
def etat_lieux_download_pdf(request, pk):
    """Télécharger l'état des lieux en PDF"""
    etat = get_object_or_404(
        EtatDesLieux.objects.select_related(
            'appartement', 'appartement__residence', 'locataire'
        ).prefetch_related('details'),
        pk=pk
    )

    try:
        pdf = generate_etat_lieux_pdf(etat)
        filename = generate_etat_lieux_filename(etat)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('properties:etat_lieux_detail', pk=pk)


@login_required
def etat_lieux_preview_pdf(request, pk):
    """Prévisualiser l'état des lieux en PDF dans le navigateur"""
    etat = get_object_or_404(
        EtatDesLieux.objects.select_related(
            'appartement', 'appartement__residence', 'locataire'
        ).prefetch_related('details'),
        pk=pk
    )

    try:
        pdf = generate_etat_lieux_pdf(etat)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="etat_lieux_preview.pdf"'

        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('properties:etat_lieux_detail', pk=pk)


@login_required
def etat_lieux_delete_view(request, pk):
    """Supprimer un état des lieux"""
    etat = get_object_or_404(EtatDesLieux, pk=pk)
    
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer des états des lieux.")
        return redirect('properties:etat_lieux_detail', pk=pk)
    
    if request.method == 'POST':
        numero = etat.numero_etat
        etat.delete()
        messages.success(request, f"État des lieux {numero} supprimé avec succès!")
        return redirect('properties:etat_lieux_list')
    
    return render(request, 'properties/etat_lieux_confirm_delete.html', {'etat': etat})




@login_required
def remise_cles_list_view(request):
    """Liste des remises de clés"""
    remises = RemiseDesCles.objects.select_related(
        'appartement', 'appartement__residence', 'locataire', 'contrat'
    ).order_by('-date_remise')
    
    # Filtres
    type_filter = request.GET.get('type', '')
    appartement_filter = request.GET.get('appartement', '')
    
    if type_filter:
        remises = remises.filter(type_remise=type_filter)
    if appartement_filter:
        remises = remises.filter(appartement_id=appartement_filter)
    
    context = {
        'remises': remises,
        'type_filter': type_filter,
        'appartement_filter': appartement_filter,
    }
    
    return render(request, 'properties/remise_cles_list.html', context)


@login_required
def remise_cles_create_view(request):
    """Créer une nouvelle remise de clés"""
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des remises de clés.")
        return redirect('properties:remise_cles_list')

    # Récupérer les paramètres de l'URL pour pré-remplir le formulaire
    workflow_id = request.GET.get('workflow')
    contrat_id = request.GET.get('contrat')
    etat_lieux_id = request.GET.get('etat_lieux')

    workflow = None
    contrat = None
    initial_data = {'type_remise': 'entree'}  # Par défaut: entrée

    if contrat_id:
        try:
            from apps.contracts.models import RentalContract
            contrat = RentalContract.objects.select_related(
                'appartement', 'locataire'
            ).get(pk=contrat_id)
            initial_data.update({
                'contrat': contrat,
                'appartement': contrat.appartement,
                'locataire': contrat.locataire,
            })
        except:
            pass

    if etat_lieux_id:
        try:
            etat_lieux = EtatDesLieux.objects.get(pk=etat_lieux_id)
            initial_data['etat_lieux'] = etat_lieux
        except:
            pass

    if workflow_id:
        try:
            from apps.contracts.models import ContractWorkflow
            workflow = ContractWorkflow.objects.select_related('contrat').get(pk=workflow_id)
        except:
            pass

    if request.method == 'POST':
        form = RemiseDesClesForm(request.POST)

        if form.is_valid():
            remise = form.save(commit=False)
            remise.cree_par = request.user
            remise.save()

            messages.success(request, f"Remise de clés {remise.numero_attestation} créée avec succès!")

            # Rediriger vers le workflow si on vient de là
            if workflow_id:
                messages.info(request, "Vous pouvez maintenant télécharger le PDF et enregistrer la remise dans le workflow.")
                return redirect('properties:remise_cles_detail', pk=remise.pk)

            return redirect('properties:remise_cles_detail', pk=remise.pk)
    else:
        form = RemiseDesClesForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Nouvelle Remise de Clés',
        'workflow': workflow,
        'from_workflow': bool(workflow_id),
    }

    return render(request, 'properties/remise_cles_form.html', context)


@login_required
def remise_cles_detail_view(request, pk):
    """Détail d'une remise de clés"""
    remise = get_object_or_404(
        RemiseDesCles.objects.select_related(
            'appartement', 'appartement__residence', 'locataire',
            'contrat', 'etat_lieux', 'cree_par'
        ),
        pk=pk
    )
    
    context = {
        'remise': remise,
    }
    
    return render(request, 'properties/remise_cles_detail.html', context)


@login_required
def remise_cles_edit_view(request, pk):
    """Éditer une remise de clés"""
    remise = get_object_or_404(RemiseDesCles, pk=pk)
    
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier des remises de clés.")
        return redirect('properties:remise_cles_detail', pk=pk)
    
    if request.method == 'POST':
        form = RemiseDesClesForm(request.POST, instance=remise)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, f"Remise de clés {remise.numero_attestation} modifiée avec succès!")
            return redirect('properties:remise_cles_detail', pk=remise.pk)
    else:
        form = RemiseDesClesForm(instance=remise)
    
    context = {
        'form': form,
        'remise': remise,
        'title': f'Modifier Remise de Clés {remise.numero_attestation}',
    }
    
    return render(request, 'properties/remise_cles_form.html', context)


@login_required
def remise_cles_download_pdf(request, pk):
    """Télécharger l'attestation de remise de clés en PDF"""
    remise = get_object_or_404(
        RemiseDesCles.objects.select_related(
            'appartement', 'appartement__residence', 'locataire', 'contrat'
        ),
        pk=pk
    )

    try:
        pdf = generate_remise_cles_pdf(remise)
        filename = generate_remise_cles_filename(remise)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('properties:remise_cles_detail', pk=pk)


@login_required
def remise_cles_preview_pdf(request, pk):
    """Prévisualiser l'attestation de remise de clés en PDF dans le navigateur"""
    remise = get_object_or_404(
        RemiseDesCles.objects.select_related(
            'appartement', 'appartement__residence', 'locataire', 'contrat'
        ),
        pk=pk
    )

    try:
        pdf = generate_remise_cles_pdf(remise)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="remise_cles_preview.pdf"'

        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('properties:remise_cles_detail', pk=pk)


@login_required
def remise_cles_delete_view(request, pk):
    """Supprimer une remise de clés"""
    remise = get_object_or_404(RemiseDesCles, pk=pk)
    
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer des remises de clés.")
        return redirect('properties:remise_cles_detail', pk=pk)
    
    if request.method == 'POST':
        numero = remise.numero_attestation
        remise.delete()
        messages.success(request, f"Remise de clés {numero} supprimée avec succès!")
        return redirect('properties:remise_cles_list')

    return render(request, 'properties/remise_cles_confirm_delete.html', {'remise': remise})


# ============ PAGE D'ENREGISTREMENT UNIFIÉ ============

@login_required
def enregistrement_bien_view(request):
    """Page d'enregistrement unifiée pour résidences et appartements"""
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette page.")
        return redirect('dashboard:index')

    # Récupérer les propriétaires (Tiers de type propriétaire)
    proprietaires = Tiers.objects.filter(type_tiers='proprietaire').order_by('nom', 'prenom')

    # Récupérer les résidences actives
    residences = Residence.objects.filter(statut='active').order_by('nom')

    context = {
        'proprietaires': proprietaires,
        'residences': residences,
    }

    return render(request, 'dashboard/forms/enregistrement_bien.html', context)