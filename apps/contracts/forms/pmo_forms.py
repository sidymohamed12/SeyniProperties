# apps/contracts/forms/pmo_forms.py
"""
Formulaires pour le module PMO (Project Management Office)
Gestion du workflow de traitement des contrats
"""

from django import forms
from ..models import ContractWorkflow, DocumentContrat


class DocumentUploadForm(forms.ModelForm):
    """Formulaire pour uploader un document de contrat"""

    class Meta:
        model = DocumentContrat
        fields = ['type_document', 'fichier', 'obligatoire', 'commentaire']

        widgets = {
            'type_document': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
            }),
            'fichier': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'obligatoire': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-imani-primary border-gray-300 rounded focus:ring-imani-primary'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'rows': 3,
                'placeholder': 'Commentaire optionnel...'
            }),
        }

        labels = {
            'type_document': 'Type de document',
            'fichier': 'Fichier',
            'obligatoire': 'Document obligatoire',
            'commentaire': 'Commentaire',
        }


class VisitePlanificationForm(forms.ModelForm):
    """Formulaire pour planifier une visite d'entrée"""

    class Meta:
        model = ContractWorkflow
        fields = ['date_visite_entree', 'lieu_rdv_visite', 'observations_visite']

        widgets = {
            'date_visite_entree': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
            }),
            'lieu_rdv_visite': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'placeholder': 'Adresse du rendez-vous...'
            }),
            'observations_visite': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'rows': 4,
                'placeholder': 'Observations et points à vérifier lors de la visite...'
            }),
        }

        labels = {
            'date_visite_entree': 'Date et heure de la visite',
            'lieu_rdv_visite': 'Lieu de rendez-vous',
            'observations_visite': 'Observations',
        }


class EtatLieuxUploadForm(forms.ModelForm):
    """Formulaire pour uploader le rapport d'état des lieux"""

    class Meta:
        model = ContractWorkflow
        fields = ['rapport_etat_lieux', 'observations_visite']

        widgets = {
            'rapport_etat_lieux': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'accept': '.pdf'
            }),
            'observations_visite': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'rows': 4,
                'placeholder': 'Observations lors de la visite...'
            }),
        }

        labels = {
            'rapport_etat_lieux': 'Rapport d\'état des lieux (PDF)',
            'observations_visite': 'Observations de la visite',
        }


class RemiseClesForm(forms.ModelForm):
    """Formulaire pour la remise des clés"""

    class Meta:
        model = ContractWorkflow
        fields = ['date_remise_cles', 'nombre_cles', 'notes_pmo']

        widgets = {
            'date_remise_cles': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
            }),
            'nombre_cles': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'min': '1',
                'value': '1'
            }),
            'notes_pmo': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'rows': 3,
                'placeholder': 'Notes sur la remise des clés...'
            }),
        }

        labels = {
            'date_remise_cles': 'Date et heure de remise',
            'nombre_cles': 'Nombre de clés',
            'notes_pmo': 'Notes',
        }


class WorkflowFilterForm(forms.Form):
    """Formulaire de filtres pour le dashboard PMO"""

    ETAPE_CHOICES = [('', 'Toutes les étapes')] + ContractWorkflow.ETAPE_CHOICES
    STATUT_CHOICES = [('', 'Tous les statuts')] + ContractWorkflow.STATUT_DOSSIER_CHOICES

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Numéro contrat, locataire...',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
        }),
        label='Recherche'
    )

    etape = forms.ChoiceField(
        choices=ETAPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
        }),
        label='Étape'
    )

    statut_dossier = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
        }),
        label='Statut dossier'
    )

    responsable = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Tous les responsables",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary'
        }),
        label='Responsable PMO'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Charger les responsables PMO (utilisateurs qui ont des workflows assignés)
        from apps.accounts.models.custom_user import CustomUser
        self.fields['responsable'].queryset = CustomUser.objects.filter(
            workflows_pmo__isnull=False
        ).distinct().order_by('first_name', 'last_name')


class WorkflowNotesForm(forms.ModelForm):
    """Formulaire pour ajouter des notes au workflow"""

    class Meta:
        model = ContractWorkflow
        fields = ['notes_pmo']

        widgets = {
            'notes_pmo': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-imani-primary',
                'rows': 4,
                'placeholder': 'Ajouter des notes internes PMO...'
            }),
        }

        labels = {
            'notes_pmo': 'Notes internes',
        }
