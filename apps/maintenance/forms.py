# apps/maintenance/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models.intervention import Intervention, InterventionMedia
from .models.travail import Travail, TravailMedia
from apps.properties.models.properties import Property
from apps.properties.models.appartement import Appartement
from apps.properties.models.residence import Residence
from apps.tiers.models import Tiers
from django.utils import timezone

User = get_user_model()


# ============================================================================
# FORMULAIRES TRAVAIL (NOUVEAU SYSTÈME UNIFIÉ)
# ============================================================================

class TravailForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un travail (système unifié)
    Remplace InterventionForm pour le nouveau modèle Travail
    """

    # Champ personnalisé pour l'employé assigné
    assigne_a = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="-- Assigner plus tard --",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Employé assigné'
    )

    class Meta:
        model = Travail
        fields = [
            'titre', 'description', 'type_travail', 'priorite',
            'appartement', 'residence', 'signale_par', 'assigne_a',
            'date_prevue', 'cout_estime', 'recurrence'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ex: Fuite d\'eau, Panne électrique...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Décrivez le problème en détail, localisation exacte, urgence...',
                'required': True
            }),
            'type_travail': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'priorite': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'appartement': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'residence': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'signale_par': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'date_prevue': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'type': 'date'
            }),
            'cout_estime': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01'
            }),
            'recurrence': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

        labels = {
            'titre': 'Titre du travail',
            'description': 'Description détaillée',
            'type_travail': 'Type de travail',
            'priorite': 'Priorité',
            'appartement': 'Appartement concerné (optionnel)',
            'residence': 'Résidence concernée (optionnel)',
            'signale_par': 'Signalé par (optionnel)',
            'assigne_a': 'Employé assigné',
            'date_prevue': 'Date prévue',
            'cout_estime': 'Coût estimé (FCFA)',
            'recurrence': 'Récurrence',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configuration des querysets optimisés
        self.fields['appartement'].queryset = Appartement.objects.select_related('residence').order_by('residence__nom', 'nom')
        self.fields['appartement'].empty_label = "-- Aucun appartement spécifique --"
        self.fields['appartement'].required = False

        self.fields['residence'].queryset = Residence.objects.order_by('nom')
        self.fields['residence'].empty_label = "-- Aucune résidence spécifique --"
        self.fields['residence'].required = False

        # Configuration locataires (Tiers de type locataire)
        self.fields['signale_par'].queryset = Tiers.objects.filter(
            type_tiers='locataire',
            statut='actif'
        ).order_by('nom', 'prenom')
        self.fields['signale_par'].empty_label = "-- Aucun locataire --"
        self.fields['signale_par'].required = False

        # Configuration employés (user_type='employe')
        employes_queryset = User.objects.filter(
            user_type='employe',
            is_active=True
        ).order_by('first_name', 'last_name')

        self.fields['assigne_a'].queryset = employes_queryset

        # Valeurs par défaut pour nouveau travail
        if not self.instance.pk:
            self.fields['priorite'].initial = 'normale'
            self.fields['recurrence'].initial = 'aucune'

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        appartement = cleaned_data.get('appartement')
        residence = cleaned_data.get('residence')

        # Au moins un lieu doit être spécifié
        if not appartement and not residence:
            raise ValidationError(
                "Vous devez spécifier au moins un appartement ou une résidence."
            )

        # Si appartement est spécifié, on peut auto-remplir residence
        if appartement and not residence:
            cleaned_data['residence'] = appartement.residence

        return cleaned_data

    def clean_titre(self):
        """Validation du titre"""
        titre = self.cleaned_data.get('titre')
        if titre and len(titre.strip()) < 5:
            raise ValidationError("Le titre doit contenir au moins 5 caractères.")
        return titre

    def clean_description(self):
        """Validation de la description"""
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise ValidationError("La description doit contenir au moins 10 caractères.")
        return description

    def clean_cout_estime(self):
        """Validation du coût estimé"""
        cout = self.cleaned_data.get('cout_estime')
        if cout and cout > 10000000:  # Plus de 10 millions FCFA
            raise ValidationError("Le coût estimé semble très élevé. Veuillez vérifier.")
        return cout

    def clean_date_prevue(self):
        """Validation de la date prévue"""
        date_prevue = self.cleaned_data.get('date_prevue')
        # Pas de validation particulière pour l'instant
        return date_prevue


# ============================================================================
# FORMULAIRES INTERVENTION (ANCIEN SYSTÈME - DÉPRÉCIÉ)
# ============================================================================

class InterventionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une intervention - VERSION CORRIGÉE"""
    
    # ✅ CORRECTION: Définir un queryset par défaut au lieu de None
    technicien = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),  # ✅ Queryset par défaut
        required=False,
        empty_label="-- Assigner plus tard --",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        label='Technicien assigné'
    )
    
    class Meta:
        model = Intervention
        fields = [
            'titre', 'description', 'type_intervention', 'priorite',
            'appartement', 'locataire', 'technicien', 'cout_estime'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Ex: Fuite d\'eau, Panne électrique...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Décrivez le problème en détail, localisation exacte, urgence...',
                'required': True
            }),
            'type_intervention': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'priorite': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'appartement': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': True
            }),
            'locataire': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'cout_estime': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01'
            }),
        }
        
        labels = {
            'titre': 'Titre de l\'intervention',
            'description': 'Description du problème',
            'type_intervention': 'Type d\'intervention',
            'priorite': 'Priorité',
            'appartement': 'Appartement concerné',
            'locataire': 'Locataire (optionnel)',
            'cout_estime': 'Coût estimé (FCFA)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ CONFIGURATION APPARTEMENT
        if APPARTEMENT_AVAILABLE:
            appartements_queryset = Appartement.objects.select_related('residence').order_by('residence__nom', 'nom')
            self.fields['appartement'].queryset = appartements_queryset
            self.fields['appartement'].empty_label = "-- Sélectionner un appartement --"
        elif PROPERTY_AVAILABLE:
            self.fields['appartement'].queryset = Property.objects.order_by('name')
            self.fields['appartement'].empty_label = "-- Sélectionner une propriété --"
        else:
            self.fields['appartement'].queryset = self.fields['appartement'].queryset.none()
        
        # ✅ CONFIGURATION LOCATAIRE (Tiers de type locataire)
        if TIERS_AVAILABLE:
            active_locataires = Tiers.objects.filter(
                type_tiers='locataire',
                statut='actif'
            ).order_by('nom', 'prenom')
            self.fields['locataire'].queryset = active_locataires
            self.fields['locataire'].empty_label = "-- Aucun locataire --"
        else:
            self.fields['locataire'].queryset = self.fields['locataire'].queryset.none()
        
        self.fields['locataire'].required = False
        
        # ✅ CORRECTION CRITIQUE: Remplacer le queryset par défaut par le bon
        try:
            # Essayer d'abord avec les techniciens spécifiques
            technicians_queryset = User.objects.filter(
                user_type__in=['technicien', 'technician', 'employee', 'field_agent'],
                is_active=True
            ).order_by('first_name', 'last_name')
            
            # Si aucun technicien trouvé, prendre tous les utilisateurs actifs
            if not technicians_queryset.exists():
                technicians_queryset = User.objects.filter(
                    is_active=True
                ).exclude(
                    user_type__in=['manager', 'accountant', 'tenant', 'locataire']
                ).order_by('first_name', 'last_name')
            
            self.fields['technicien'].queryset = technicians_queryset
            
        except Exception as e:
            # En cas d'erreur, utiliser tous les utilisateurs actifs
            print(f"DEBUG Form - Erreur lors de la récupération des techniciens: {e}")
            self.fields['technicien'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Debug
        print(f"DEBUG Form - Techniciens disponibles: {self.fields['technicien'].queryset.count()}")
        for tech in self.fields['technicien'].queryset[:5]:  # Limiter à 5 pour les logs
            print(f"  - {tech.get_full_name()} (ID: {tech.id}, Type: {getattr(tech, 'user_type', 'N/A')})")
        
        # Valeurs par défaut
        if not self.instance.pk:
            self.fields['priorite'].initial = 'normale'
            self.fields['type_intervention'].initial = 'reparation'

    def clean_technicien(self):
        """✅ VALIDATION CUSTOM - Accepter tous les techniciens actifs"""
        technicien = self.cleaned_data.get('technicien')
        
        if technicien:
            # Vérifier que le technicien existe et est actif
            if not technicien.is_active:
                raise ValidationError("Ce technicien n'est plus actif.")
            
            print(f"DEBUG Form - Technicien validé: {technicien.get_full_name()} (ID: {technicien.id})")
        
        return technicien

    def clean_titre(self):
        """Validation du titre"""
        titre = self.cleaned_data.get('titre')
        if titre and len(titre.strip()) < 5:
            raise ValidationError("Le titre doit contenir au moins 5 caractères.")
        return titre

    def clean_description(self):
        """Validation de la description"""
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise ValidationError("La description doit contenir au moins 10 caractères pour être utile au technicien.")
        return description

    def clean_cout_estime(self):
        """Validation du coût estimé"""
        cout = self.cleaned_data.get('cout_estime')
        if cout and cout > 1000000:  # Plus d'1 million FCFA
            raise ValidationError("Le coût estimé semble très élevé. Veuillez vérifier.")
        return cout



class InterventionFilterForm(forms.Form):
    """Formulaire de filtrage des interventions"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...'
        }),
        label='Recherche'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + [
            ('signale', 'Signalé'),
            ('assigne', 'Assigné'),
            ('en_cours', 'En cours'),
            ('complete', 'Terminé'),
            ('annule', 'Annulé'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Statut'
    )
    
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'Toutes les priorités')] + [
            ('basse', 'Basse'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
            ('urgente', 'Urgente'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Priorité'
    )
    
    type_intervention = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les types')] + [
            ('plomberie', 'Plomberie'),
            ('electricite', 'Électricité'),
            ('menage', 'Ménage'),
            ('reparation', 'Réparation générale'),
            ('peinture', 'Peinture'),
            ('serrurerie', 'Serrurerie'),
            ('climatisation', 'Climatisation'),
            ('jardinage', 'Jardinage'),
            ('maintenance_preventive', 'Maintenance préventive'),
            ('autres', 'Autres'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type'
    )
    
    technicien = forms.ModelChoiceField(
        queryset=User.objects.filter(
            user_type='technicien',
            is_active=True
        ).order_by('first_name', 'last_name'),
        required=False,
        empty_label="Tous les techniciens",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Technicien'
    )


class InterventionAssignForm(forms.Form):
    """Formulaire d'assignation simplifié"""
    
    technicien = forms.ModelChoiceField(
        queryset=User.objects.filter(
            user_type='technicien',
            is_active=True
        ).order_by('first_name', 'last_name'),
        empty_label="-- Sélectionner un technicien --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Technicien'
    )
    
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Instructions particulières...'
        }),
        label='Commentaire (optionnel)'
    )
    
    date_planifiee = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Date planifiée (optionnel)'
    )


class InterventionCompleteForm(forms.Form):
    """Formulaire de finalisation d'intervention"""
    
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Décrivez le travail effectué...'
        }),
        label='Rapport d\'intervention',
        required=True
    )
    
    cout_reel = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Coût réel (FCFA)'
    )
    
    duree_reelle = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Durée en minutes',
            'min': '5'
        }),
        label='Durée réelle (minutes)'
    )
    
    satisfaction_locataire = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Non renseigné'),
            (1, '1 - Très insatisfait'),
            (2, '2 - Insatisfait'),
            (3, '3 - Neutre'),
            (4, '4 - Satisfait'),
            (5, '5 - Très satisfait'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Satisfaction du locataire'
    )


class InterventionMediaUploadForm(forms.Form):
    """Formulaire pour uploader des médias d'intervention"""
    
    TYPE_CHOICES = [
        ('photo_avant', 'Photo avant intervention'),
        ('photo_apres', 'Photo après intervention'),
        ('facture', 'Facture/Devis'),
        ('rapport', 'Rapport technique'),
        ('autre', 'Autre'),
    ]
    
    fichier = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf,.doc,.docx'
        }),
        label='Fichier'
    )
    
    type_media = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type de fichier'
    )
    
    description = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Description du fichier...'
        }),
        label='Description (optionnel)'
    )
    
    def clean_fichier(self):
        fichier = self.cleaned_data.get('fichier')
        
        if fichier:
            # Vérifier la taille (max 10MB)
            if fichier.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    "La taille du fichier ne doit pas dépasser 10 MB."
                )
            
            # Vérifier le type de fichier
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']
            file_extension = fichier.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    "Type de fichier non autorisé. Extensions autorisées : " + 
                    ", ".join(allowed_extensions)
                )
        
        return fichier


class QuickInterventionForm(forms.Form):
    """Formulaire rapide pour créer une intervention depuis mobile"""
    
    titre = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Titre de l\'intervention'
        }),
        label='Titre'
    )
    
    type_intervention = forms.ChoiceField(
        choices=[
            ('plomberie', 'Plomberie'),
            ('electricite', 'Électricité'),
            ('menage', 'Ménage'),
            ('reparation', 'Réparation générale'),
            ('peinture', 'Peinture'),
            ('serrurerie', 'Serrurerie'),
            ('climatisation', 'Climatisation'),
            ('jardinage', 'Jardinage'),
            ('maintenance_preventive', 'Maintenance préventive'),
            ('autres', 'Autres'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type'
    )
    
    priorite = forms.ChoiceField(
        choices=[
            ('basse', 'Basse'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
            ('urgente', 'Urgente'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Priorité',
        initial='normale'
    )
    
    bien = forms.ModelChoiceField(
        queryset=Property.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Propriété',
        empty_label="-- Sélectionner une propriété --"
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Description courte'
        }),
        label='Description',
        required=False
    )


class InterventionStatusUpdateForm(forms.Form):
    """Formulaire pour mettre à jour le statut d'une intervention"""
    
    nouveau_statut = forms.ChoiceField(
        choices=[
            ('signale', 'Signalé'),
            ('assigne', 'Assigné'),
            ('en_cours', 'En cours'),
            ('complete', 'Terminé'),
            ('annule', 'Annulé'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Nouveau statut'
    )
    
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaire sur ce changement de statut...'
        }),
        label='Commentaire (optionnel)'
    )


class InterventionRatingForm(forms.Form):
    """Formulaire pour noter une intervention"""
    
    note = forms.ChoiceField(
        choices=[
            (1, '1 - Très insatisfait'),
            (2, '2 - Insatisfait'),
            (3, '3 - Correct'),
            (4, '4 - Satisfait'),
            (5, '5 - Très satisfait'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Votre évaluation'
    )
    
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Commentaires sur l\'intervention...'
        }),
        label='Commentaires (optionnel)'
    )


class InterventionSearchForm(forms.Form):
    """Formulaire de recherche avancée"""
    
    search_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans les titres et descriptions...'
        }),
        label='Recherche textuelle'
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Date de début'
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Date de fin'
    )
    
    cout_min = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Coût minimum'
    )
    
    cout_max = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Coût maximum'
    )


class BulkInterventionActionForm(forms.Form):
    """Formulaire pour les actions en masse sur les interventions"""
    
    ACTION_CHOICES = [
        ('assign', 'Assigner à un technicien'),
        ('change_priority', 'Changer la priorité'),
        ('change_status', 'Changer le statut'),
        ('export', 'Exporter la sélection'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Action à effectuer'
    )
    
    technicien = forms.ModelChoiceField(
        queryset=User.objects.filter(
            user_type='technicien',
            is_active=True
        ).order_by('first_name', 'last_name'),
        required=False,
        empty_label="-- Sélectionner un technicien --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Technicien (pour assignation)'
    )
    
    nouvelle_priorite = forms.ChoiceField(
        choices=[
            ('basse', 'Basse'),
            ('normale', 'Normale'),
            ('haute', 'Haute'),
            ('urgente', 'Urgente'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Nouvelle priorité'
    )
    
    nouveau_statut = forms.ChoiceField(
        choices=[
            ('signale', 'Signalé'),
            ('assigne', 'Assigné'),
            ('en_cours', 'En cours'),
            ('complete', 'Terminé'),
            ('annule', 'Annulé'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Nouveau statut'
    )
    
    selected_interventions = forms.CharField(
        widget=forms.HiddenInput(),
        label='Interventions sélectionnées'
    )


class InterventionPlanningForm(forms.Form):
    """Formulaire pour planifier une intervention"""
    
    date_planifiee = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Date et heure planifiées'
    )
    
    duree_estimee = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Durée en minutes',
            'min': '15',
            'step': '15'
        }),
        label='Durée estimée (minutes)',
        initial=120
    )
    
    instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Instructions spéciales pour le technicien...'
        }),
        label='Instructions spéciales'
    )
    
    materiel_requis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Liste du matériel nécessaire...'
        }),
        label='Matériel requis'
    )
    
    def clean_date_planifiee(self):
        date_planifiee = self.cleaned_data.get('date_planifiee')
        if date_planifiee and date_planifiee < timezone.now():
            raise ValidationError("La date planifiée ne peut pas être dans le passé.")
        return date_planifiee