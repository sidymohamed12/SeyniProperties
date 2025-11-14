# apps/employees/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.employees.models.employee import Employee
from apps.employees.models.task import Task
from apps.properties.models import Property
from apps.maintenance.models.intervention import Intervention, InterventionMedia
from datetime import datetime
import random
import string

User = get_user_model()

# ✅ IMPORT SÉCURISÉ DES MODÈLES
try:
    from apps.properties.models import Property
    PROPERTY_AVAILABLE = True
except ImportError:
    PROPERTY_AVAILABLE = False

try:
    from apps.properties.models import Appartement
    APPARTEMENT_AVAILABLE = True
except ImportError:
    APPARTEMENT_AVAILABLE = False



# ✅ GARDER EmployeeForm INTACT (il marche déjà bien)
class EmployeeForm(forms.ModelForm):
    # Champs utilisateur
    first_name = forms.CharField(max_length=150, label="Prénom")
    last_name = forms.CharField(max_length=150, label="Nom")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(max_length=20, label="Téléphone")
    user_type = forms.ChoiceField(
        choices=[('agent_terrain', 'Agent de terrain'), ('technicien', 'Technicien')],
        label="Type d'employé"
    )
    
    class Meta:
        model = Employee
        fields = ['specialite', 'date_embauche', 'salaire']
        widgets = {
            'specialite': forms.Select(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salaire': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # S'assurer que date_embauche a une valeur par défaut pour les nouveaux employés
        if not self.instance.pk:
            self.fields['date_embauche'].initial = timezone.now().date()
    
    def save(self, commit=True):
        # Générer un mot de passe aléatoire
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        # Créer d'abord l'utilisateur avec le mot de passe
        user = User.objects.create_user(
            username=f"{self.cleaned_data['user_type']}_{User.objects.count() + 1:03d}",
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            user_type=self.cleaned_data['user_type'],
            phone=self.cleaned_data['phone'],
            password=password
        )

        # Marquer le mot de passe comme temporaire pour forcer le changement à la première connexion
        user.mot_de_passe_temporaire = True
        user.save()

        # Créer le profil employé
        employee = super().save(commit=False)
        employee.user = user

        # S'assurer que date_embauche est définie
        if not employee.date_embauche:
            employee.date_embauche = timezone.now().date()

        # Sauvegarder le mot de passe temporaire
        employee.mot_de_passe_temporaire = password

        if commit:
            employee.save()

        # Stocker les identifiants pour l'affichage
        employee._login_credentials = {
            'username': user.username,
            'password': password
        }

        return employee


# ✅ FORMULAIRE TASKFORM CORRIGÉ ET SIMPLIFIÉ
class TaskForm(forms.ModelForm):
    """Formulaire pour créer/modifier une tâche - VERSION CORRIGÉE POUR APPARTEMENTS"""
    
    # ✅ AJOUT D'UN CHAMP PERSONNALISÉ POUR LES APPARTEMENTS
    appartement_choice = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="-- Sélectionner un appartement (optionnel) --",
        label="Appartement concerné",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Task
        fields = [
            'titre', 'description', 'type_tache', 'priorite', 
            'assigne_a', 'date_prevue', 'duree_estimee'  # ✅ RETIRÉ 'bien' de la Meta
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la tâche',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée de la tâche...'
            }),
            'type_tache': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'assigne_a': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'date_prevue': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'duree_estimee': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Durée en minutes'
            }),
        }
        
        labels = {
            'titre': 'Titre de la tâche',
            'description': 'Description',
            'type_tache': 'Type de tâche',
            'priorite': 'Priorité',
            'assigne_a': 'Assigné à',
            'date_prevue': 'Date et heure prévues',
            'duree_estimee': 'Durée estimée (minutes)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ✅ CONFIGURATION DU CHAMP APPARTEMENT
        print("=== DÉBUT CONFIGURATION APPARTEMENT ===")
        
        if APPARTEMENT_AVAILABLE:
            from apps.properties.models import Appartement
            appartements_queryset = Appartement.objects.select_related('residence').order_by('residence__nom', 'nom')
            appartements_count = appartements_queryset.count()
            print(f"Nombre d'appartements trouvés: {appartements_count}")
            
            self.fields['appartement_choice'].queryset = appartements_queryset
            
            # Afficher quelques appartements pour débogage
            for apt in appartements_queryset[:3]:
                print(f"Appartement: {apt.residence.nom} - {apt.nom}")
            
            # Personnaliser l'affichage des appartements
            def appartement_label(obj):
                return f"{obj.residence.nom} - {obj.nom} ({obj.type_bien})"
            self.fields['appartement_choice'].label_from_instance = appartement_label
            
            # Pré-remplir si on modifie une tâche existante
            if self.instance.pk and self.instance.bien:
                print(f"Tâche existante avec bien: {self.instance.bien}")
                # Chercher l'appartement correspondant au bien
                try:
                    # Si il y a une relation ou un mapping entre Property et Appartement
                    appartement = Appartement.objects.filter(
                        residence__nom__icontains=self.instance.bien.name
                    ).first()
                    if appartement:
                        self.fields['appartement_choice'].initial = appartement
                        print(f"Appartement trouvé pour pré-remplissage: {appartement}")
                except Exception as e:
                    print(f"Erreur lors du pré-remplissage: {e}")
        else:
            print("❌ Modèle Appartement non disponible")
            self.fields['appartement_choice'].queryset = self.fields['appartement_choice'].queryset.none()
        
        print("=== FIN CONFIGURATION APPARTEMENT ===")
        
        # ✅ CONFIGURATION DES EMPLOYÉS
        active_employees = User.objects.filter(
            user_type__in=['agent_terrain', 'technicien'],
            is_active=True
        ).order_by('first_name', 'last_name')
        
        self.fields['assigne_a'].queryset = active_employees
        self.fields['assigne_a'].empty_label = "-- Sélectionner un employé --"
        
        # Personnaliser l'affichage des employés
        def employee_label(obj):
            user_type_display = obj.user_type.replace('_', ' ').title()
            return f"{obj.get_full_name()} ({user_type_display})"
        self.fields['assigne_a'].label_from_instance = employee_label
        
        # ✅ VALEURS PAR DÉFAUT
        if not self.instance.pk:  # Seulement pour les nouvelles tâches
            # Date par défaut à maintenant + 1 heure
            default_date = timezone.now() + timezone.timedelta(hours=1)
            self.fields['date_prevue'].initial = default_date.strftime('%Y-%m-%dT%H:%M')
            
            # Priorité par défaut
            self.fields['priorite'].initial = 'normale'

    def save(self, commit=True):
        """Surcharger save pour gérer la conversion appartement -> bien"""
        instance = super().save(commit=False)
        
        # ✅ GESTION DE LA CONVERSION APPARTEMENT -> BIEN
        appartement_choice = self.cleaned_data.get('appartement_choice')
        if appartement_choice and PROPERTY_AVAILABLE:
            from apps.properties.models import Property
            
            # Chercher ou créer un Property correspondant à l'appartement
            try:
                # Essayer de trouver un Property existant
                property_obj = Property.objects.filter(
                    name__icontains=appartement_choice.nom
                ).first()
                
                if not property_obj:
                    # Créer un nouveau Property basé sur l'appartement
                    property_obj = Property.objects.create(
                        name=f"{appartement_choice.residence.nom} - {appartement_choice.nom}",
                        address=appartement_choice.residence.adresse,
                        city=appartement_choice.residence.ville,
                        property_type=appartement_choice.type_bien,
                        surface_area=appartement_choice.superficie or 0,
                        rooms_count=appartement_choice.nb_pieces or 1,
                        rent_amount=appartement_choice.loyer_base or 0,
                        landlord=appartement_choice.residence.bailleur if hasattr(appartement_choice.residence, 'bailleur') else None
                    )
                
                instance.bien = property_obj
            except Exception as e:
                # En cas d'erreur, ne pas assigner de bien
                print(f"Erreur lors de la création/récupération du Property: {e}")
                instance.bien = None
        
        if commit:
            instance.save()
        return instance

    def clean_date_prevue(self):
        """Validation de la date prévue"""
        date_prevue = self.cleaned_data.get('date_prevue')
        
        if date_prevue and date_prevue < timezone.now():
            raise ValidationError("La date prévue ne peut pas être dans le passé.")
        
        return date_prevue
    
    def clean_duree_estimee(self):
        """Validation de la durée estimée"""
        duree = self.cleaned_data.get('duree_estimee')
        
        if duree and duree > 1440:  # Plus de 24 heures
            raise ValidationError("La durée ne peut pas dépasser 24 heures (1440 minutes).")
        
        return duree

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        titre = cleaned_data.get('titre')
        if titre and len(titre.strip()) < 3:
            raise ValidationError({'titre': 'Le titre doit contenir au moins 3 caractères.'})
        
        return cleaned_data



# ✅ FORMULAIRE POUR LES INTERVENTIONS
class InterventionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une intervention - VERSION CORRIGÉE"""
    
    class Meta:
        model = Intervention
        fields = [
            'titre', 'description', 'type_intervention', 'priorite',
            'bien', 'locataire', 'technicien', 'cout_estime'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Fuite d\'eau, Panne électrique...',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le problème en détail, localisation exacte, urgence...',
                'required': True
            }),
            'type_intervention': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'bien': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'locataire': forms.Select(attrs={
                'class': 'form-select'
            }),
            'technicien': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cout_estime': forms.NumberInput(attrs={
                'class': 'form-control',
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
            'bien': 'Propriété',
            'locataire': 'Locataire (optionnel)',
            'technicien': 'Technicien (optionnel)',
            'cout_estime': 'Coût estimé (FCFA)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurer les querysets
        self.fields['bien'].queryset = Property.objects.all().order_by('name')
        self.fields['bien'].empty_label = "-- Sélectionner une propriété --"
        
        # Import safe pour éviter les erreurs circulaires
        try:
            from apps.tiers.models import Tiers
            self.fields['locataire'].queryset = Tiers.objects.filter(
                type_tiers='locataire',
                statut='actif'
            ).order_by('nom', 'prenom')
        except ImportError:
            self.fields['locataire'].queryset = self.fields['locataire'].queryset.none()
        
        self.fields['locataire'].required = False
        self.fields['locataire'].empty_label = "-- Aucun locataire --"
        
        self.fields['technicien'].queryset = User.objects.filter(
            user_type='technicien',
            is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['technicien'].required = False
        self.fields['technicien'].empty_label = "-- Assigner plus tard --"


# ✅ AUTRES FORMULAIRES CORRIGÉS
class TaskCompletionForm(forms.Form):
    """Formulaire pour terminer une tâche depuis mobile"""
    
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Décrivez le travail effectué, les éventuels problèmes rencontrés...'
        }),
        label='Rapport de tâche',
        required=False,
    )
    
    temps_passe = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Temps en minutes',
            'min': '1'
        }),
        label='Temps passé (minutes)',
        required=False,
    )


class FilterTasksForm(forms.Form):
    """Formulaire pour filtrer les tâches"""
    
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Task.STATUT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=False,
        label='Statut'
    )
    
    priority = forms.ChoiceField(
        choices=[('', 'Toutes les priorités')] + Task.PRIORITE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=False,
        label='Priorité'
    )
    
    type_tache = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Task.TYPE_TACHE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=False,
        label='Type'
    )
    
    employee = forms.ModelChoiceField(
        queryset=User.objects.filter(
            user_type__in=['agent_terrain', 'technicien'],
            is_active=True
        ).order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        required=False,
        empty_label="Tous les employés",
        label='Employé'
    )


class QuickTaskForm(forms.Form):
    """Formulaire rapide pour mobile"""
    
    titre = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Titre de la tâche'
        }),
        label='Titre',
        max_length=200
    )
    
    type_tache = forms.ChoiceField(
        choices=Task.TYPE_TACHE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type de tâche'
    )
    
    priorite = forms.ChoiceField(
        choices=Task.PRIORITE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Priorité',
        initial='normale'
    )
    
    assigne_a = forms.ModelChoiceField(
        queryset=User.objects.filter(
            user_type__in=['agent_terrain', 'technicien'],
            is_active=True
        ).order_by('first_name', 'last_name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Assigné à'
    )
    
    date_prevue = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Date prévue'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Description courte (optionnel)'
        }),
        label='Description',
        required=False
    )


# ✅ FORMULAIRES POUR LE PROFIL EMPLOYÉ
class EmployeeProfileUpdateForm(forms.ModelForm):
    """Formulaire pour mettre à jour le profil employé"""
    
    class Meta:
        model = Employee
        fields = ['specialite', 'telephone_professionnel', 'niveau_competence']
        widgets = {
            'specialite': forms.Select(attrs={'class': 'form-control'}),
            'telephone_professionnel': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau_competence': forms.Select(attrs={'class': 'form-control'}),
        }


class EmployeeAvailabilityForm(forms.ModelForm):
    """Formulaire pour gérer la disponibilité d'un employé"""
    
    class Meta:
        model = Employee
        fields = ['is_available', 'statut', 'notes']
        widgets = {
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ✅ FORMULAIRES POUR LES MÉDIAS
class TaskMediaUploadForm(forms.Form):
    """Formulaire pour uploader des médias de tâche"""
    
    TYPE_CHOICES = [
        ('photo_avant', 'Photo avant'),
        ('photo_apres', 'Photo après'),
        ('document', 'Document'),
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


# ✅ FORMULAIRE DE FEEDBACK
class FeedbackForm(forms.Form):
    """Formulaire pour envoyer des retours"""
    
    TYPE_CHOICES = [
        ('bug', 'Signaler un bug'),
        ('suggestion', 'Suggestion d\'amélioration'),
        ('autre', 'Autre'),
    ]
    
    type_feedback = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Type de retour'
    )
    
    sujet = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sujet de votre retour'
        }),
        label='Sujet'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Décrivez votre retour en détail...'
        }),
        label='Votre message'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre email (optionnel)'
        }),
        label='Email de contact (optionnel)'
    )