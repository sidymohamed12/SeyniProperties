# apps/payments/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Payment, Invoice
from decimal import Decimal
from datetime import date, timedelta


# ==================== FORMULAIRES FACTURES ====================

class BaseInvoiceForm(forms.ModelForm):
    """Formulaire de base pour toutes les factures"""
    
    class Meta:
        model = Invoice
        fields = []
        widgets = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Styles communs pour tous les champs
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput, 
                                        forms.DateInput, forms.Select, forms.Textarea)):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all'
                })


class InvoiceLoyerForm(BaseInvoiceForm):
    """Formulaire pour créer une facture de loyer à partir d'un contrat existant"""
    
    contrat = forms.ModelChoiceField(
        queryset=None,
        label="Contrat de location",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
            'id': 'id_contrat'
        }),
        help_text="Sélectionnez le contrat pour lequel générer la facture"
    )
    
    class Meta:
        model = Invoice
        fields = [
            'contrat', 'periode_debut', 'periode_fin',
            'montant_ht', 'taux_tva', 'date_emission', 'date_echeance',
            'description', 'notes'
        ]
        widgets = {
            'periode_debut': forms.DateInput(attrs={'type': 'date'}),
            'periode_fin': forms.DateInput(attrs={'type': 'date'}),
            'date_emission': forms.DateInput(attrs={'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'type': 'date'}),
            'montant_ht': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'readonly': 'readonly'}),
            'taux_tva': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Description de la facture de loyer...'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importer ici pour éviter les imports circulaires
        from apps.contracts.models import RentalContract
        
        # Filtrer uniquement les contrats actifs
        self.fields['contrat'].queryset = RentalContract.objects.filter(
            statut='actif'
        ).select_related(
            'locataire__user',
            'appartement__residence'
        ).order_by('-date_debut')
        
        # Valeurs par défaut
        if not self.instance.pk:
            self.fields['date_emission'].initial = date.today()
            self.fields['date_echeance'].initial = date.today() + timedelta(days=5)
            self.fields['taux_tva'].initial = Decimal('0.00')  # Pas de TVA sur les loyers généralement
            
            # Période du mois en cours
            today = date.today()
            first_day = today.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            self.fields['periode_debut'].initial = first_day
            self.fields['periode_fin'].initial = last_day
    
    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        periode_debut = cleaned_data.get('periode_debut')
        periode_fin = cleaned_data.get('periode_fin')
        
        if periode_debut and periode_fin:
            if periode_fin < periode_debut:
                raise ValidationError("La période de fin doit être après la période de début")
        
        # Remplir automatiquement le montant depuis le contrat
        if contrat:
            cleaned_data['montant_ht'] = contrat.loyer_mensuel
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_facture = 'loyer'
        instance.is_manual = True
        
        # Les informations du locataire viennent du contrat
        # Pas besoin de destinataire_nom car on a le contrat
        
        if commit:
            instance.save()
        return instance


class InvoiceSyndicForm(BaseInvoiceForm):
    """Formulaire pour créer une facture syndic de copropriété"""
    
    class Meta:
        model = Invoice
        fields = [
            'destinataire_nom', 'destinataire_adresse', 'destinataire_email',
            'destinataire_telephone', 'reference_copropriete', 'trimestre',
            'montant_ht', 'taux_tva', 'date_emission', 'date_echeance',
            'description', 'notes'
        ]
        widgets = {
            'date_emission': forms.DateInput(attrs={'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'type': 'date'}),
            'montant_ht': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'taux_tva': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'destinataire_adresse': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cotisations trimestrielles de copropriété...'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['date_emission'].initial = date.today()
            self.fields['date_echeance'].initial = date.today() + timedelta(days=90)  # 3 mois pour syndic
            self.fields['taux_tva'].initial = Decimal('0.00')  # Pas de TVA pour syndic généralement
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_facture = 'syndic'
        instance.is_manual = True
        if commit:
            instance.save()
        return instance


class InvoiceDemandeAchatForm(BaseInvoiceForm):
    """Formulaire pour créer une facture de demande d'achat"""
    
    class Meta:
        model = Invoice
        fields = [
            'destinataire_nom', 'destinataire_email', 'destinataire_telephone',
            'numero_bon_commande', 'categorie_achat', 'montant_ht', 'taux_tva',
            'date_emission', 'date_echeance', 'description', 'notes'
        ]
        widgets = {
            'date_emission': forms.DateInput(attrs={'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'type': 'date'}),
            'montant_ht': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'taux_tva': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Détails de la demande d\'achat...'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['date_emission'].initial = date.today()
            self.fields['date_echeance'].initial = date.today() + timedelta(days=30)
            self.fields['taux_tva'].initial = Decimal('18.00')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_facture = 'demande_achat'
        instance.is_manual = True
        if commit:
            instance.save()
        return instance


class InvoicePrestataireForm(BaseInvoiceForm):
    """Formulaire pour créer une facture prestataire"""
    
    class Meta:
        model = Invoice
        fields = [
            'fournisseur_nom', 'fournisseur_reference', 'type_prestation',
            'destinataire_email', 'destinataire_telephone', 'montant_ht', 
            'taux_tva', 'date_emission', 'date_echeance', 'description', 'notes'
        ]
        widgets = {
            'date_emission': forms.DateInput(attrs={'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'type': 'date'}),
            'montant_ht': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'taux_tva': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Détails de la prestation...'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['date_emission'].initial = date.today()
            self.fields['date_echeance'].initial = date.today() + timedelta(days=30)
            self.fields['taux_tva'].initial = Decimal('18.00')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_facture = 'prestataire'
        instance.is_manual = True
        # Copier le nom du fournisseur vers destinataire_nom
        instance.destinataire_nom = instance.fournisseur_nom
        if commit:
            instance.save()
        return instance


# ==================== FORMULAIRE RENOMMAGE DOCUMENT ====================

class RenameDocumentForm(forms.Form):
    """Formulaire pour renommer un document/fichier"""
    
    nouveau_nom = forms.CharField(
        max_length=200,
        required=True,
        label="Nouveau nom du fichier",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Ex: Facture_Janvier_2025'
        })
    )
    
    def clean_nouveau_nom(self):
        nom = self.cleaned_data.get('nouveau_nom')
        # Nettoyer le nom (enlever caractères spéciaux)
        nom = nom.strip()
        # Remplacer espaces par underscores
        nom = nom.replace(' ', '_')
        # Enlever caractères non autorisés
        caracteres_autorises = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        nom = ''.join(c for c in nom if c in caracteres_autorises)
        return nom


# ==================== FORMULAIRE PAIEMENT (INCHANGÉ) ====================

class PaymentForm(forms.ModelForm):
    """Formulaire pour créer/modifier un paiement"""
    
    class Meta:
        model = Payment
        fields = [
            'facture',
            'montant',
            'date_paiement',
            'moyen_paiement',
            'reference_transaction',
            'commentaire',
        ]
        widgets = {
            'facture': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                'id': 'id_facture'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                'placeholder': '0',
                'step': '0.01',
                'min': '0.01'
            }),
            'date_paiement': forms.DateInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                'type': 'date'
            }),
            'moyen_paiement': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all'
            }),
            'reference_transaction': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                'placeholder': 'Ex: TRX123456 (optionnel)'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                'rows': 3,
                'placeholder': 'Commentaire optionnel...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les factures selon les permissions
        if user and not user.is_staff:
            if hasattr(user, 'locataire'):
                self.fields['facture'].queryset = Invoice.objects.filter(
                    contrat__locataire__user=user
                ).select_related('contrat__appartement__residence')
        
        # Valeur par défaut pour la date
        if not self.instance.pk:
            self.fields['date_paiement'].initial = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        montant = cleaned_data.get('montant')
        facture = cleaned_data.get('facture')
        
        if montant and facture:
            # Vérifier que le montant ne dépasse pas le solde restant
            if montant > facture.solde_restant:
                raise ValidationError(
                    f"Le montant ne peut pas dépasser le solde restant de {facture.solde_restant} FCFA"
                )
        
        return cleaned_data


class QuickPaymentForm(forms.ModelForm):
    """Formulaire rapide pour enregistrer un paiement"""
    
    class Meta:
        model = Payment
        fields = ['montant', 'date_paiement', 'moyen_paiement', 'reference_transaction']
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'date_paiement': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'moyen_paiement': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_transaction': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence (optionnel)'
            }),
        }


# ============================================================================
# MODULE 4: FORMULAIRES DEMANDES D'ACHAT
# ============================================================================

from django.forms import inlineformset_factory
from .models import LigneDemandeAchat
from apps.maintenance.models.travail import Travail


class DemandeAchatForm(forms.ModelForm):
    """Formulaire pour créer une demande d'achat"""

    class Meta:
        model = Invoice
        fields = [
            'service_fonction',
            'motif_principal',
            'travail_lie',
            'date_echeance',
        ]
        widgets = {
            'service_fonction': forms.TextInput(attrs={
                'class': 'imani-input',
                'placeholder': 'Ex: Maintenance, Administration, etc.'
            }),
            'motif_principal': forms.Textarea(attrs={
                'class': 'imani-input',
                'rows': 3,
                'placeholder': 'Expliquez la raison de cette demande d\'achat...'
            }),
            'travail_lie': forms.Select(attrs={
                'class': 'imani-input'
            }),
            'date_echeance': forms.DateInput(attrs={
                'type': 'date',
                'class': 'imani-input'
            }),
        }
        labels = {
            'service_fonction': 'Service/Fonction',
            'motif_principal': 'Motif principal',
            'travail_lie': 'Travail lié (optionnel)',
            'date_echeance': 'Date d\'échéance souhaitée',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les travaux en attente de matériel ou non assignés
        from apps.maintenance.models.travail import Travail
        self.fields['travail_lie'].queryset = Travail.objects.filter(
            statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
        ).select_related('appartement__residence').order_by('-created_at')
        self.fields['travail_lie'].required = False


class LigneDemandeAchatForm(forms.ModelForm):
    """Formulaire pour une ligne d'article dans la demande"""

    class Meta:
        model = LigneDemandeAchat
        fields = [
            'designation',
            'quantite',
            'unite',
            'fournisseur',
            'prix_unitaire',
            'motif',
        ]
        widgets = {
            'designation': forms.TextInput(attrs={
                'class': 'imani-input',
                'placeholder': 'Ex: Robinet mitigeur chrome'
            }),
            'quantite': forms.NumberInput(attrs={
                'class': 'imani-input',
                'min': '0.01',
                'step': '0.01'
            }),
            'unite': forms.TextInput(attrs={
                'class': 'imani-input',
                'placeholder': 'Ex: unité, mètre, kg'
            }),
            'fournisseur': forms.TextInput(attrs={
                'class': 'imani-input',
                'placeholder': 'Ex: Quincaillerie SENGHOR'
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'imani-input',
                'min': '0',
                'step': '1'
            }),
            'motif': forms.Textarea(attrs={
                'class': 'imani-input',
                'rows': 2,
                'placeholder': 'Justification pour cet article...'
            }),
        }


# Formset pour gérer plusieurs lignes d'articles
LigneDemandeAchatFormSet = inlineformset_factory(
    Invoice,
    LigneDemandeAchat,
    form=LigneDemandeAchatForm,
    extra=3,  # 3 lignes vides par défaut
    can_delete=True,
    min_num=1,  # Au moins 1 ligne requise
    validate_min=True,
)


class ValidationResponsableForm(forms.Form):
    """Formulaire pour la validation par le responsable"""

    decision = forms.ChoiceField(
        choices=[
            ('valider', 'Valider la demande'),
            ('refuser', 'Refuser la demande'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300'
        }),
        label='Décision'
    )

    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': 4,
            'placeholder': 'Commentaire (optionnel)...'
        }),
        label='Commentaire'
    )


class TraitementComptableForm(forms.ModelForm):
    """Formulaire pour le traitement comptable et préparation du chèque"""

    class Meta:
        model = Invoice
        fields = [
            'numero_cheque',
            'banque_cheque',
            'date_emission_cheque',
            'beneficiaire_cheque',
            'commentaire_comptable',
        ]
        widgets = {
            'numero_cheque': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Ex: 0012345'
            }),
            'banque_cheque': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Ex: BICIS, CBAO, Ecobank'
            }),
            'date_emission_cheque': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'beneficiaire_cheque': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Ex: Quincaillerie SENGHOR'
            }),
            'commentaire_comptable': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Commentaire du comptable (optionnel)...'
            }),
        }
        labels = {
            'numero_cheque': 'Numéro de chèque',
            'banque_cheque': 'Banque émettrice',
            'date_emission_cheque': 'Date d\'émission du chèque',
            'beneficiaire_cheque': 'Bénéficiaire',
            'commentaire_comptable': 'Commentaire',
        }


class ValidationDGForm(forms.Form):
    """Formulaire pour la validation finale par la Direction Générale"""

    decision = forms.ChoiceField(
        choices=[
            ('valider', 'Valider et approuver le paiement'),
            ('refuser', 'Refuser la demande'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300'
        }),
        label='Décision'
    )

    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'rows': 4,
            'placeholder': 'Commentaire (optionnel)...'
        }),
        label='Commentaire de la Direction'
    )


class ReceptionMarchandiseForm(forms.ModelForm):
    """Formulaire pour enregistrer la réception de la marchandise"""

    class Meta:
        model = Invoice
        fields = [
            'date_reception',
            'remarques_reception',
        ]
        widgets = {
            'date_reception': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'remarques_reception': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Remarques sur la réception (état, conformité, etc.)...'
            }),
        }
        labels = {
            'date_reception': 'Date de réception',
            'remarques_reception': 'Remarques',
        }


class LigneReceptionForm(forms.ModelForm):
    """Formulaire pour enregistrer les quantités/prix réels reçus"""

    class Meta:
        model = LigneDemandeAchat
        fields = ['quantite_recue', 'prix_reel']
        widgets = {
            'quantite_recue': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'min': '0',
                'step': '0.01'
            }),
            'prix_reel': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'min': '0',
                'step': '1'
            }),
        }
        labels = {
            'quantite_recue': 'Quantité reçue',
            'prix_reel': 'Prix réel payé (FCFA)',
        }


# Formset pour la réception
LigneReceptionFormSet = inlineformset_factory(
    Invoice,
    LigneDemandeAchat,
    form=LigneReceptionForm,
    extra=0,  # Pas de lignes vides (on édite les existantes)
    can_delete=False,
)