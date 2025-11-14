# apps/contracts/forms/pmo_workflow_create_form.py
"""
Formulaire pour démarrer un nouveau workflow PMO
"""

from django import forms
from django.core.exceptions import ValidationError

from apps.properties.models.appartement import Appartement
from apps.tiers.models import Tiers
from ..models import RentalContract, ContractWorkflow


class WorkflowCreateForm(forms.Form):
    """Formulaire pour créer un nouveau workflow PMO avec contrat en brouillon"""

    appartement = forms.ModelChoiceField(
        queryset=Appartement.objects.filter(statut_occupation='libre').select_related('residence'),
        label="Appartement",
        widget=forms.Select(attrs={
            'class': 'form-input w-full',
            'id': 'id_appartement'
        }),
        help_text="Sélectionnez l'appartement à louer"
    )

    locataire = forms.ModelChoiceField(
        queryset=Tiers.objects.filter(type_tiers='locataire', statut='actif'),
        label="Locataire",
        widget=forms.Select(attrs={
            'class': 'form-input w-full',
            'id': 'id_locataire'
        }),
        help_text="Sélectionnez le locataire candidat"
    )

    date_debut_prevue = forms.DateField(
        label="Date de début prévue",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input w-full',
            'id': 'id_date_debut_prevue'
        }),
        help_text="Date prévue pour le début du contrat"
    )

    duree_mois = forms.IntegerField(
        label="Durée du contrat (mois)",
        initial=12,
        min_value=1,
        max_value=60,
        widget=forms.NumberInput(attrs={
            'class': 'form-input w-full',
            'id': 'id_duree_mois',
            'min': '1',
            'max': '60',
            'value': '12'
        }),
        help_text="Durée du contrat en mois (généralement 12 mois)"
    )

    type_contrat_usage = forms.ChoiceField(
        label="Type de contrat",
        choices=[
            ('habitation', 'Contrat à Usage d\'Habitation'),
            ('professionnel', 'Contrat à Usage Professionnel'),
        ],
        initial='habitation',
        widget=forms.Select(attrs={
            'class': 'form-input w-full',
            'id': 'id_type_contrat_usage'
        }),
        help_text="Détermine les clauses applicables au contrat"
    )

    loyer_mensuel = forms.DecimalField(
        label="Loyer mensuel (FCFA)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input w-full',
            'id': 'id_loyer_mensuel',
            'min': '0',
            'step': '1000'
        })
    )

    charges_mensuelles = forms.DecimalField(
        label="Charges mensuelles (FCFA)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input w-full',
            'id': 'id_charges_mensuelles',
            'min': '0',
            'step': '1000',
            'value': '0'
        })
    )

    frais_agence = forms.DecimalField(
        label="Frais d'agence (FCFA)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input w-full',
            'id': 'id_frais_agence',
            'min': '0',
            'step': '1000',
            'value': '0',
            'placeholder': 'Suggéré: 5% du loyer mensuel'
        }),
        help_text="Frais d'agence ajustables - peut être modifié selon négociation"
    )

    depot_garantie = forms.DecimalField(
        label="Dépôt de garantie (FCFA)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input w-full',
            'id': 'id_depot_garantie',
            'min': '0',
            'step': '1000'
        })
    )

    travaux_realises = forms.DecimalField(
        label="Travaux réalisés (FCFA)",
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input w-full',
            'id': 'id_travaux_realises',
            'min': '0',
            'step': '1000',
            'value': '0'
        }),
        help_text="Coût des travaux de rénovation ou d'aménagement avant la location"
    )

    notes_initiales = forms.CharField(
        label="Notes / Observations",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-input w-full',
            'id': 'id_notes_initiales',
            'rows': 3,
            'placeholder': 'Notes ou observations sur ce dossier...'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        appartement = cleaned_data.get('appartement')
        locataire = cleaned_data.get('locataire')

        # Vérifier que l'appartement est bien libre
        if appartement and appartement.statut_occupation != 'libre':
            raise ValidationError(
                f"L'appartement {appartement.nom} n'est pas disponible (statut: {appartement.get_statut_occupation_display()})"
            )

        # Vérifier que le locataire n'a pas déjà un workflow en cours
        if locataire:
            workflows_en_cours = ContractWorkflow.objects.filter(
                contrat__locataire=locataire,
                etape_actuelle__in=['verification_dossier', 'attente_facture', 'facture_validee', 'redaction_contrat', 'visite_entree', 'remise_cles']
            )
            if workflows_en_cours.exists():
                raise ValidationError(
                    f"Le locataire {locataire.nom_complet} a déjà un workflow PMO en cours."
                )

        return cleaned_data
