"""
Formulaires pour le module syndic.
"""
from django import forms
from .models import (
    Copropriete, Coproprietaire, CotisationSyndic,
    PaiementCotisation, BudgetPrevisionnel, LigneBudget
)


class CoproprieteForm(forms.ModelForm):
    """Formulaire pour créer/modifier une copropriété."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les résidences de type syndic ou mixte
        from apps.properties.models.residence import Residence
        self.fields['residence'].queryset = Residence.objects.filter(
            type_gestion__in=['syndic', 'mixte']
        ).order_by('nom')

    class Meta:
        model = Copropriete
        fields = [
            'residence', 'nombre_tantiemes_total', 'periode_cotisation',
            'budget_annuel', 'date_debut_gestion', 'compte_bancaire',
            'is_active', 'notes'
        ]
        widgets = {
            'residence': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'nombre_tantiemes_total': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '10000'
            }),
            'periode_cotisation': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'budget_annuel': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '5000000',
                'step': '0.01'
            }),
            'date_debut_gestion': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'compte_bancaire': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'SN123456789...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Notes internes...'
            }),
        }


class CoproprietaireForm(forms.ModelForm):
    """Formulaire pour créer/modifier un copropriétaire."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les tiers de type copropriétaire
        from apps.tiers.models import Tiers
        self.fields['tiers'].queryset = Tiers.objects.filter(
            type_tiers='coproprietaire'
        ).order_by('nom', 'prenom')
        # Personnaliser l'affichage
        self.fields['tiers'].label_from_instance = lambda obj: f"{obj.nom_complet} - {obj.telephone}"

        # Optimiser les copropriétés
        self.fields['copropriete'].queryset = Copropriete.objects.select_related('residence').filter(is_active=True)
        self.fields['copropriete'].label_from_instance = lambda obj: obj.residence.nom

    class Meta:
        model = Coproprietaire
        fields = [
            'tiers', 'copropriete', 'nombre_tantiemes',
            'lots', 'date_entree', 'date_sortie', 'is_active', 'notes'
        ]
        widgets = {
            'tiers': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'copropriete': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'nombre_tantiemes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '250'
            }),
            'lots': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'size': '5'
            }),
            'date_entree': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'date_sortie': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4
            }),
        }


class CotisationSyndicForm(forms.ModelForm):
    """Formulaire pour créer/modifier une cotisation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optimiser la requête pour les copropriétaires
        self.fields['coproprietaire'].queryset = Coproprietaire.objects.select_related(
            'tiers', 'copropriete__residence'
        ).filter(is_active=True).order_by('tiers__nom', 'tiers__prenom')
        # Personnaliser l'affichage
        self.fields['coproprietaire'].label_from_instance = lambda obj: f"{obj.tiers.nom_complet} - {obj.copropriete.residence.nom} ({obj.quote_part:.2f}%)"

    class Meta:
        model = CotisationSyndic
        fields = [
            'coproprietaire', 'periode', 'annee', 'montant_theorique',
            'date_emission', 'date_echeance', 'statut', 'notes'
        ]
        widgets = {
            'coproprietaire': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'periode': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Q1, Q2, M01, etc.'
            }),
            'annee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '2025'
            }),
            'montant_theorique': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01'
            }),
            'date_emission': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'date_echeance': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4
            }),
        }


class PaiementCotisationForm(forms.ModelForm):
    """Formulaire pour enregistrer un paiement de cotisation."""

    def __init__(self, *args, **kwargs):
        # Extraire la cotisation si passée en paramètre
        self.cotisation = kwargs.pop('cotisation', None)
        super().__init__(*args, **kwargs)

        # Si une cotisation est fournie, exclure le champ du formulaire
        if self.cotisation:
            self.fields.pop('cotisation', None)

    class Meta:
        model = PaiementCotisation
        fields = [
            'montant', 'mode_paiement',
            'date_paiement', 'reference_paiement', 'notes'
        ]
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '150000'
            }),
            'mode_paiement': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'date_paiement': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'reference_paiement': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'N° chèque, référence virement, etc.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3
            }),
        }


class BudgetPrevisionnelForm(forms.ModelForm):
    """Formulaire pour créer/modifier un budget prévisionnel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optimiser les copropriétés
        self.fields['copropriete'].queryset = Copropriete.objects.select_related('residence').filter(is_active=True)
        self.fields['copropriete'].label_from_instance = lambda obj: obj.residence.nom

    class Meta:
        model = BudgetPrevisionnel
        fields = [
            'copropriete', 'annee', 'montant_total',
            'date_ag', 'date_vote', 'statut', 'document', 'notes'
        ]
        widgets = {
            'copropriete': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'annee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '2025'
            }),
            'montant_total': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '5000000'
            }),
            'date_ag': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'date_vote': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'document': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4
            }),
        }


class LigneBudgetForm(forms.ModelForm):
    """Formulaire pour créer/modifier une ligne de budget."""

    class Meta:
        model = LigneBudget
        fields = [
            'budget', 'categorie', 'description',
            'montant_prevu', 'montant_realise', 'notes'
        ]
        widgets = {
            'budget': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'categorie': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Ex: Entretien ascenseur trimestriel'
            }),
            'montant_prevu': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '50000'
            }),
            'montant_realise': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3
            }),
        }
