"""
Formulaires pour la gestion des tiers
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Tiers, TiersBien


class TiersForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un tiers
    """

    class Meta:
        model = Tiers
        fields = [
            'nom',
            'prenom',
            'type_tiers',
            'telephone',
            'telephone_secondaire',
            'email',
            'adresse',
            'ville',
            'quartier',
            'code_postal',
            'statut',
            'piece_identite',
            'autre_document',
            'notes',
        ]

        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Nom de famille ou raison sociale'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Prénom (pour les particuliers)'
            }),
            'type_tiers': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '+221 XX XXX XX XX'
            }),
            'telephone_secondaire': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '+221 XX XXX XX XX (optionnel)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'email@example.com'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Ville'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Quartier (optionnel)'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Code postal (optionnel)'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'piece_identite': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': 'image/*,application/pdf'
            }),
            'autre_document': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': 'image/*,application/pdf'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Notes et observations (optionnel)'
            }),
        }

    def clean_email(self):
        """Valider l'unicité de l'email"""
        email = self.cleaned_data.get('email')

        # Vérifier si un tiers avec cet email existe déjà (sauf pour l'édition)
        queryset = Tiers.objects.filter(email=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("Un tiers avec cet email existe déjà.")

        return email

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()

        # Validation personnalisée si nécessaire
        return cleaned_data


class TiersBienForm(forms.ModelForm):
    """
    Formulaire pour lier un tiers à un bien immobilier
    """

    class Meta:
        model = TiersBien
        fields = [
            'tiers',
            'appartement',
            'residence',
            'type_contrat',
            'type_mandat',
            'date_debut',
            'date_fin',
            'statut',
            'montant_commission',
            'pourcentage_commission',
            'contrat_signe',
            'mandat_document',
            'notes',
        ]

        widgets = {
            'tiers': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'appartement': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'residence': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'type_contrat': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'type_mandat': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'date'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'montant_commission': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Montant en FCFA',
                'step': '0.01'
            }),
            'pourcentage_commission': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Pourcentage (%)',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'contrat_signe': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': 'application/pdf,image/*'
            }),
            'mandat_document': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'accept': 'application/pdf,image/*'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Notes et observations (optionnel)'
            }),
        }

    def clean(self):
        """Validation personnalisée"""
        cleaned_data = super().clean()

        appartement = cleaned_data.get('appartement')
        residence = cleaned_data.get('residence')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        # S'assurer qu'au moins un bien est sélectionné
        if not appartement and not residence:
            raise ValidationError(
                "Vous devez sélectionner au moins un bien (appartement ou résidence)"
            )

        # Vérifier les dates
        if date_fin and date_debut and date_fin < date_debut:
            raise ValidationError(
                "La date de fin ne peut pas être antérieure à la date de début"
            )

        return cleaned_data


class TiersSearchForm(forms.Form):
    """
    Formulaire de recherche de tiers
    """

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Rechercher par nom, prénom, email, téléphone...'
        })
    )

    type_tiers = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les types')] + list(Tiers.TYPE_TIERS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )

    statut = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les statuts')] + list(Tiers.STATUT_CHOICES),
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )

    ville = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ville'
        })
    )
