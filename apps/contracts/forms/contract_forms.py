# apps/contracts/forms/contract_forms.py
"""
Formulaires pour la gestion des contrats de location
"""

from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

from ..models import RentalContract
from apps.properties.models import Appartement, Residence
from apps.tiers.models import Tiers


class RentalContractForm(forms.ModelForm):
    """Formulaire pour créer/modifier un contrat de location"""

    class Meta:
        model = RentalContract
        fields = [
            'appartement',
            'locataire',
            'date_debut',
            'date_fin',
            'type_contrat_usage',
            'loyer_mensuel',
            'charges_mensuelles',
            'frais_agence',
            'depot_garantie',
            'travaux_realises',
            'statut'
        ]

        widgets = {
            'appartement': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_appartement'
            }),
            'locataire': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_locataire'
            }),
            'date_debut': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'id': 'id_date_debut'
            }),
            'date_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input',
                'id': 'id_date_fin'
            }),
            'type_contrat_usage': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_type_contrat_usage'
            }),
            'loyer_mensuel': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_loyer_mensuel',
                'min': '0',
                'step': '0.01'
            }),
            'charges_mensuelles': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_charges_mensuelles',
                'min': '0',
                'step': '0.01',
                'value': '0'
            }),
            'frais_agence': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_frais_agence',
                'min': '0',
                'step': '0.01',
                'value': '0',
                'placeholder': 'Frais ajustables (suggéré: 5% du loyer)'
            }),
            'depot_garantie': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_depot_garantie',
                'min': '0',
                'step': '0.01'
            }),
            'travaux_realises': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id_travaux_realises',
                'min': '0',
                'step': '0.01',
                'value': '0'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_statut'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer uniquement les appartements libres pour un nouveau contrat
        if not self.instance.pk:
            self.fields['appartement'].queryset = Appartement.objects.filter(
                statut_occupation='libre'
            ).select_related('residence')

        # Filtrer uniquement les locataires actifs (Tiers de type locataire)
        self.fields['locataire'].queryset = Tiers.objects.filter(
            type_tiers='locataire',
            statut='actif'
        )

        # Valeur par défaut pour les charges
        if not self.instance.pk:
            self.fields['charges_mensuelles'].initial = 0

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        # Validation des dates
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise ValidationError({
                    'date_fin': 'La date de fin doit être postérieure à la date de début.'
                })

        return cleaned_data


class ContractFilterForm(forms.Form):
    """
    Formulaire de filtres pour la liste des contrats
    """

    STATUS_CHOICES = [
        ('', 'Tous les statuts'),
        ('brouillon', 'Brouillon'),
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('resilie', 'Résilié'),
        ('suspendu', 'Suspendu'),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par numéro, appartement ou locataire...',
            'class': 'form-control'
        }),
        label='Recherche'
    )

    statut = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Statut'
    )

    residence = forms.ModelChoiceField(
        queryset=Residence.objects.filter(statut='active'),
        required=False,
        empty_label="Toutes les résidences",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Résidence'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap4/layout/inline_field.html'

        self.helper.layout = Layout(
            Row(
                Column('search', css_class='form-group col-md-4'),
                Column('statut', css_class='form-group col-md-3'),
                Column('residence', css_class='form-group col-md-3'),
                Column(
                    Submit('filter', 'Filtrer', css_class='btn btn-primary'),
                    css_class='form-group col-md-2'
                ),
                css_class='form-row'
            )
        )


class ContractQuickCreateForm(forms.ModelForm):
    """
    Formulaire simplifié pour création rapide de contrat
    """

    class Meta:
        model = RentalContract
        fields = [
            'appartement', 'locataire', 'date_debut', 'date_fin',
            'loyer_mensuel', 'charges_mensuelles', 'depot_garantie'
        ]

        widgets = {
            'date_debut': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'date_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'loyer_mensuel': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'charges_mensuelles': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'depot_garantie': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'appartement': forms.Select(attrs={'class': 'form-control'}),
            'locataire': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
            'appartement': 'Appartement',
            'locataire': 'Locataire',
            'date_debut': 'Date début',
            'date_fin': 'Date fin',
            'loyer_mensuel': 'Loyer (FCFA)',
            'charges_mensuelles': 'Charges (FCFA)',
            'depot_garantie': 'Dépôt (FCFA)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les appartements disponibles
        self.fields['appartement'].queryset = Appartement.objects.filter(
            statut_occupation__in=['libre', 'available']
        )

        # Filtrer les locataires actifs (Tiers de type locataire)
        self.fields['locataire'].queryset = Tiers.objects.filter(
            type_tiers='locataire',
            statut='actif'
        )


class AppartementSelectionForm(forms.Form):
    """
    Formulaire pour sélectionner un appartement avec logique hiérarchique
    """

    residence = forms.ModelChoiceField(
        queryset=Residence.objects.filter(statut='active'),
        empty_label="Choisir une résidence...",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'loadAppartements(this.value)'
        }),
        label='Résidence'
    )

    appartement = forms.ModelChoiceField(
        queryset=Appartement.objects.none(),  # Vide au départ
        empty_label="Choisir d'abord une résidence",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Appartement'
    )

    def __init__(self, *args, **kwargs):
        residence_id = kwargs.pop('residence_id', None)
        super().__init__(*args, **kwargs)

        if residence_id:
            self.fields['appartement'].queryset = Appartement.objects.filter(
                residence_id=residence_id,
                statut_occupation__in=['libre', 'available']
            )


class ContractRenewalForm(forms.ModelForm):
    """
    Formulaire pour renouveler un contrat
    """

    class Meta:
        model = RentalContract
        fields = ['date_debut', 'date_fin', 'loyer_mensuel', 'charges_mensuelles']

        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'charges_mensuelles': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

        labels = {
            'date_debut': 'Nouvelle date de début',
            'date_fin': 'Nouvelle date de fin',
            'loyer_mensuel': 'Nouveau loyer mensuel (FCFA)',
            'charges_mensuelles': 'Nouvelles charges (FCFA)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pré-remplir avec les dates suggérées
        if self.instance and self.instance.pk:
            # Nouveau contrat commence à la fin de l'ancien
            self.fields['date_debut'].initial = self.instance.date_fin
            # Durée d'un an par défaut
            self.fields['date_fin'].initial = self.instance.date_fin + timedelta(days=365)


class RentalContractFormLegacy(forms.ModelForm):
    """
    Formulaire de compatibilité - À supprimer progressivement
    """

    class Meta:
        model = RentalContract
        fields = [
            'numero_contrat',
            'appartement',
            'locataire',
            'date_debut',
            'date_fin',
            'loyer_mensuel',
            'statut'
        ]

        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'numero_contrat': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'appartement': forms.Select(attrs={'class': 'form-control'}),
            'locataire': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les appartements disponibles
        self.fields['appartement'].queryset = Appartement.objects.filter(
            statut_occupation__in=['libre', 'available']
        )

        # Filtrer les locataires actifs (Tiers de type locataire)
        self.fields['locataire'].queryset = Tiers.objects.filter(
            type_tiers='locataire',
            statut='actif'
        )
