# apps/properties/forms.py - MISE À JOUR pour Residence/Appartement

from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import InlineRadios
from .models import RemiseDesCles, Residence, Appartement, AppartementMedia, Property  # Garde Property pour compatibilité
from apps.tiers.models import Tiers
from django import forms
from .models import EtatDesLieux, EtatDesLieuxDetail


class ResidenceForm(forms.ModelForm):
    """Formulaire pour créer/modifier une résidence"""

    class Meta:
        model = Residence
        fields = [
            'nom', 'type_residence', 'type_gestion', 'adresse', 'quartier', 'ville', 'code_postal',
            'nb_etages', 'nb_appartements_total', 'annee_construction', 'proprietaire',
            'statut', 'description', 'equipements'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Résidence Les Palmiers'
            }),
            'type_residence': forms.Select(attrs={'class': 'form-control'}),
            'type_gestion': forms.Select(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète de la résidence'
            }),
            'quartier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Almadies, Plateau'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'Dakar'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal (optionnel)'
            }),
            'nb_etages': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'nb_appartements_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'annee_construction': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2030',
                'placeholder': 'Ex: 2020'
            }),
            'proprietaire': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description de la résidence...'
            }),
            'equipements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ex: Ascenseur, Parking, Gardien, Piscine...'
            }),
        }
        labels = {
            'nom': 'Nom de la résidence',
            'type_residence': 'Type de résidence',
            'type_gestion': 'Type de gestion',
            'adresse': 'Adresse complète',
            'quartier': 'Quartier',
            'ville': 'Ville',
            'code_postal': 'Code postal',
            'nb_etages': 'Nombre d\'étages',
            'nb_appartements_total': 'Nombre total d\'appartements',
            'annee_construction': 'Année de construction',
            'proprietaire': 'Propriétaire',
            'statut': 'Statut',
            'description': 'Description',
            'equipements': 'Équipements communs',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendre le champ proprietaire non requis par défaut
        # Il sera géré dynamiquement via JavaScript et validation côté serveur
        self.fields['proprietaire'].required = False

        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': True}
        
        # Layout du formulaire
        self.helper.layout = Layout(
            Fieldset(
                'Informations de base',
                'nom',
                Row(
                    Column('type_residence', css_class='form-group col-md-6'),
                    Column('type_gestion', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
                'proprietaire',
            ),
            Fieldset(
                'Localisation',
                'adresse',
                Row(
                    Column('quartier', css_class='form-group col-md-6'),
                    Column('ville', css_class='form-group col-md-4'),
                    Column('code_postal', css_class='form-group col-md-2'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Caractéristiques techniques',
                Row(
                    Column('nb_etages', css_class='form-group col-md-4'),
                    Column('nb_appartements_total', css_class='form-group col-md-4'),
                    Column('annee_construction', css_class='form-group col-md-4'),
                    css_class='form-row'
                ),
                Row(
                    Column('statut', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Informations complémentaires',
                'description',
                'equipements',
            ),
            Div(
                Submit('submit', 'Enregistrer la résidence', css_class='btn btn-primary'),
                css_class='text-right'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        nb_etages = cleaned_data.get('nb_etages')
        nb_appartements = cleaned_data.get('nb_appartements_total')
        type_gestion = cleaned_data.get('type_gestion')
        proprietaire = cleaned_data.get('proprietaire')

        # Validation du nombre d'appartements vs étages
        if nb_etages and nb_appartements:
            # Vérification logique : pas plus de 10 appartements par étage en moyenne
            if nb_appartements > nb_etages * 10:
                raise ValidationError(
                    f"Le nombre d'appartements ({nb_appartements}) semble trop élevé "
                    f"pour {nb_etages} étage(s). Maximum recommandé: {nb_etages * 10}"
                )

        # Validation du propriétaire selon le type de gestion
        if type_gestion in ['location', 'mixte'] and not proprietaire:
            raise ValidationError({
                'proprietaire': "Le propriétaire est obligatoire pour la gestion locative ou mixte."
            })

        # Pour les résidences de type syndic, le propriétaire n'est pas requis
        if type_gestion == 'syndic':
            cleaned_data['proprietaire'] = None  # Forcer à None pour éviter toute confusion

        return cleaned_data


class AppartementForm(forms.ModelForm):
    """Formulaire pour créer/modifier un appartement"""
    
    class Meta:
        model = Appartement
        fields = [
            'nom', 'residence', 'etage', 'type_bien', 'superficie', 'nb_pieces', 
            'nb_chambres', 'nb_sdb', 'nb_wc', 'is_meuble', 'has_balcon', 
            'has_parking', 'has_climatisation', 'equipements_inclus',
            'statut_occupation', 'mode_location', 'loyer_base', 'charges', 
            'depot_garantie', 'frais_agence', 'description', 'notes_internes'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Apt 2A, Studio 12, Bureau RDC'
            }),
            'residence': forms.Select(attrs={'class': 'form-control'}),
            'etage': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': '0',
                'help_text': '0 pour RDC, -1 pour sous-sol'
            }),
            'type_bien': forms.Select(attrs={'class': 'form-control'}),
            'superficie': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'nb_pieces': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'value': '1'
            }),
            'nb_chambres': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'value': '0'
            }),
            'nb_sdb': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'value': '1'
            }),
            'nb_wc': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'value': '1'
            }),
            'is_meuble': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_balcon': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_climatisation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'equipements_inclus': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Ex: Réfrigérateur, Lave-linge, TV, Cuisine équipée...'
            }),
            'statut_occupation': forms.Select(attrs={'class': 'form-control'}),
            'mode_location': forms.Select(attrs={'class': 'form-control'}),
            'loyer_base': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'placeholder': '0'
            }),
            'charges': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'value': '0'
            }),
            'depot_garantie': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'placeholder': '0'
            }),
            'frais_agence': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'value': '0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Description de l\'appartement...'
            }),
            'notes_internes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Notes visibles uniquement par l\'équipe...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuration Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': True}
        
        # Layout du formulaire
        self.helper.layout = Layout(
            Fieldset(
                'Identification',
                Row(
                    Column('nom', css_class='form-group col-md-6'),
                    Column('residence', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('etage', css_class='form-group col-md-4'),
                    Column('type_bien', css_class='form-group col-md-8'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Caractéristiques',
                Row(
                    Column('superficie', css_class='form-group col-md-3'),
                    Column('nb_pieces', css_class='form-group col-md-3'),
                    Column('nb_chambres', css_class='form-group col-md-3'),
                    Column('nb_sdb', css_class='form-group col-md-3'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Équipements',
                Row(
                    Column(
                        HTML('<div class="form-check">'),
                        'is_meuble',
                        HTML('<label class="form-check-label" for="id_is_meuble">Meublé</label></div>'),
                        css_class='form-group col-md-3'
                    ),
                    Column(
                        HTML('<div class="form-check">'),
                        'has_balcon',
                        HTML('<label class="form-check-label" for="id_has_balcon">Balcon/Terrasse</label></div>'),
                        css_class='form-group col-md-3'
                    ),
                    Column(
                        HTML('<div class="form-check">'),
                        'has_parking',
                        HTML('<label class="form-check-label" for="id_has_parking">Place de parking</label></div>'),
                        css_class='form-group col-md-3'
                    ),
                    Column(
                        HTML('<div class="form-check">'),
                        'has_climatisation',
                        HTML('<label class="form-check-label" for="id_has_climatisation">Climatisation</label></div>'),
                        css_class='form-group col-md-3'
                    ),
                    css_class='form-row'
                ),
                'equipements_inclus',
            ),
            Fieldset(
                'Statut et location',
                Row(
                    Column('statut_occupation', css_class='form-group col-md-6'),
                    Column('mode_location', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Tarification',
                Row(
                    Column('loyer_base', css_class='form-group col-md-6'),
                    Column('charges', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('depot_garantie', css_class='form-group col-md-6'),
                    Column('frais_agence', css_class='form-group col-md-6'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Informations complémentaires',
                'description',
                'notes_internes',
            ),
            Div(
                Submit('submit', 'Enregistrer l\'appartement', css_class='btn btn-primary'),
                css_class='text-right'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        
        # Validations logiques
        nb_pieces = cleaned_data.get('nb_pieces')
        nb_chambres = cleaned_data.get('nb_chambres')
        
        if nb_pieces and nb_chambres:
            if nb_chambres >= nb_pieces:
                raise ValidationError(
                    "Le nombre de chambres ne peut pas être supérieur ou égal au nombre total de pièces."
                )
        
        # Validation du loyer
        loyer_base = cleaned_data.get('loyer_base')
        if loyer_base and loyer_base <= 0:
            raise ValidationError("Le loyer de base doit être supérieur à 0.")
        
        return cleaned_data


class AppartementMediaForm(forms.ModelForm):
    """Formulaire pour upload de médias d'appartement"""
    
    class Meta:
        model = AppartementMedia
        fields = ['type_media', 'fichier', 'titre', 'description', 'is_principal', 'ordre', 'is_public']
        widgets = {
            'type_media': forms.Select(attrs={'class': 'form-control'}),
            'fichier': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*,.pdf,.doc,.docx'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du média'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description optionnelle...'
            }),
            'is_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AppartementFilterForm(forms.Form):
    """Formulaire de filtres pour la liste des appartements"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher par nom, référence...',
            'class': 'form-control'
        }),
        label='Recherche'
    )
    
    residence = forms.ModelChoiceField(
        queryset=Residence.objects.filter(statut='active'),
        required=False,
        empty_label="Toutes les résidences",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Résidence'
    )
    
    type_bien = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Appartement.TYPE_BIEN_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type'
    )
    
    statut_occupation = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Appartement.STATUT_OCCUPATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Statut'
    )
    
    ville = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ville...',
            'class': 'form-control'
        }),
        label='Ville'
    )


class QuickAppartementForm(forms.ModelForm):
    """Formulaire simplifié pour création rapide d'appartement"""
    
    class Meta:
        model = Appartement
        fields = [
            'nom', 'residence', 'type_bien', 'loyer_base', 'charges', 
            'nb_pieces', 'superficie'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'appartement'
            }),
            'residence': forms.Select(attrs={'class': 'form-control'}),
            'type_bien': forms.Select(attrs={'class': 'form-control'}),
            'loyer_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Loyer en FCFA'
            }),
            'charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'nb_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'superficie': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
        }


# === COMPATIBILITÉ AVEC L'ANCIEN SYSTÈME ===

class PropertyForm(forms.ModelForm):
    """
    ANCIEN FORMULAIRE - Maintenu pour compatibilité
    À SUPPRIMER après migration complète
    """
    
    class Meta:
        model = Property
        fields = [
            'name', 'property_type', 'address', 'neighborhood', 'city', 
            'base_rent', 'charges', 'surface_area', 'rooms_count', 
            'bedrooms_count', 'is_furnished', 'landlord'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du bien'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'base_rent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'charges': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'surface_area': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'rooms_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'bedrooms_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_furnished': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'landlord': forms.Select(attrs={'class': 'form-control'}),
        }




# apps/properties/forms.py
# (Ajouter ces formulaires à la fin du fichier existant)




class EtatDesLieuxForm(forms.ModelForm):
    """Formulaire pour créer/éditer un état des lieux"""
    
    class Meta:
        model = EtatDesLieux
        fields = [
            'type_etat', 'contrat', 'appartement', 'locataire',
            'date_etat', 'commercial_imany', 'observation_globale',
            'signe_bailleur', 'signe_locataire', 'date_signature'
        ]
        widgets = {
            'type_etat': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'contrat': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'appartement': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'locataire': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'date_etat': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'commercial_imany': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nom du commercial IMANY'
            }),
            'observation_globale': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-textarea rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Observations générales sur l\'état du bien...'
            }),
            'date_signature': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
        }


class EtatDesLieuxDetailForm(forms.ModelForm):
    """Formulaire pour ajouter un détail à l'état des lieux"""
    
    class Meta:
        model = EtatDesLieuxDetail
        fields = ['piece', 'corps_etat', 'observations', 'ordre']
        widgets = {
            'piece': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300',
                'placeholder': 'Ex: Salon, Chambre 1, Cuisine...'
            }),
            'corps_etat': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300',
                'placeholder': 'Ex: Murs, Sol, Plafond, Fenêtres...'
            }),
            'observations': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea rounded-lg border-gray-300',
                'placeholder': 'État, dégâts éventuels, remarques...'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300',
                'min': 0
            }),
        }


# Formset pour gérer plusieurs détails à la fois
from django.forms import inlineformset_factory

EtatDesLieuxDetailFormSet = inlineformset_factory(
    EtatDesLieux,
    EtatDesLieuxDetail,
    form=EtatDesLieuxDetailForm,
    extra=10,  # 10 lignes vides par défaut
    can_delete=True,
    fields=['piece', 'corps_etat', 'observations', 'ordre']
)



class RemiseDesClesForm(forms.ModelForm):
    """Formulaire pour créer/éditer une remise des clés"""
    
    class Meta:
        model = RemiseDesCles
        fields = [
            'type_remise', 'contrat', 'appartement', 'locataire',
            'etat_lieux', 'date_remise', 'heure_remise',
            'nombre_cles_appartement', 'nombre_cles_boite_lettres',
            'nombre_cles_garage', 'nombre_badges', 'nombre_telecommandes',
            'autres_equipements', 'observations',
            'remis_par', 'recu_par',
            'signe_bailleur', 'signe_locataire', 'date_signature'
        ]
        widgets = {
            'type_remise': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'contrat': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'appartement': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'locataire': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'etat_lieux': forms.Select(attrs={
                'class': 'form-select rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'date_remise': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'heure_remise': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
            'nombre_cles_appartement': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': 0
            }),
            'nombre_cles_boite_lettres': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': 0
            }),
            'nombre_cles_garage': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': 0
            }),
            'nombre_badges': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': 0
            }),
            'nombre_telecommandes': forms.NumberInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'min': 0
            }),
            'autres_equipements': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Ex: Clés de cave, interphone, etc.'
            }),
            'observations': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-textarea rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Observations sur l\'état des clés et équipements...'
            }),
            'remis_par': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nom de la personne qui remet les clés'
            }),
            'recu_par': forms.TextInput(attrs={
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nom de la personne qui reçoit les clés'
            }),
            'date_signature': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }),
        }