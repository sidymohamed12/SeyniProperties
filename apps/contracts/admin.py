# apps/contracts/admin.py - Version corrigée

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RentalContract, ContractWorkflow, DocumentContrat, HistoriqueWorkflow


@admin.register(RentalContract)
class RentalContractAdmin(admin.ModelAdmin):
    """Administration des contrats de location"""
    
    # ✅ CORRIGÉ: Utiliser les nouveaux noms de champs français
    list_display = [
        'numero_contrat',      # ✅ au lieu de 'contract_number'
        'appartement_display', # ✅ custom method
        'locataire_display',   # ✅ custom method
        'date_debut',          # ✅ au lieu de 'start_date'
        'date_fin',            # ✅ au lieu de 'end_date'
        'loyer_mensuel',       # ✅ au lieu de 'monthly_rent'
        'statut',              # ✅ au lieu de 'status'
        'is_active_display'    # ✅ custom method
    ]
    
    # ✅ CORRIGÉ: Utiliser les nouveaux noms de champs
    list_filter = [
        'statut',              # ✅ au lieu de 'status'
        'date_debut',          # ✅ au lieu de 'start_date'
        'date_fin',            # ✅ au lieu de 'end_date'
        'appartement__type_bien',         # ✅ au lieu de 'property__property_type'
        'appartement__residence__ville',  # ✅ au lieu de 'property__city'
        'appartement__residence__quartier',
        'type_contrat',
        'is_renouvelable',
        'created_at'
    ]
    
    # ✅ CORRIGÉ: Utiliser le nouveau nom de champ
    search_fields = [
        'numero_contrat',      # ✅ au lieu de 'contract_number'
        'appartement__nom',
        'appartement__residence__nom',
        'locataire__user__first_name',
        'locataire__user__last_name',
        'locataire__piece_identite'
    ]
    
    # ✅ CORRIGÉ: Utiliser le nouveau nom de champ
    date_hierarchy = 'date_debut'  # ✅ au lieu de 'start_date'
    
    # ✅ CORRIGÉ: Utiliser les nouveaux noms de champs
    readonly_fields = [
        'numero_contrat',      # ✅ au lieu de 'contract_number'
        'created_at',
        'updated_at',
        'montant_total_display',
        'jours_restants_display',
        'bailleur_display'
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'numero_contrat',
                'appartement',
                'locataire',
                'statut',
                'type_contrat'
            )
        }),
        ('Période du contrat', {
            'fields': (
                'date_debut',
                'date_fin',
                'duree_mois',
                'is_renouvelable',
                'preavis_mois'
            )
        }),
        ('Conditions financières', {
            'fields': (
                'loyer_mensuel',
                'charges_mensuelles',
                'depot_garantie',
                'frais_agence',
                'montant_total_display'
            )
        }),
        ('Signatures et documents', {
            'fields': (
                'date_signature',
                'signe_par_locataire',
                'signe_par_bailleur',
                'fichier_contrat'
            ),
            'classes': ('collapse',)
        }),
        ('Conditions particulières', {
            'fields': (
                'conditions_particulieres',
                'notes_internes'
            ),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': (
                'cree_par',
                'bailleur_display',
                'jours_restants_display',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'appartement__residence__bailleur__user',
            'locataire__user',
            'cree_par'
        )
    
    def appartement_display(self, obj):
        """Affiche l'appartement avec lien vers la résidence"""
        if obj.appartement:
            url = reverse('admin:properties_appartement_change', args=[obj.appartement.id])
            return format_html(
                '<a href="{}">{}</a><br><span style="color: #666; font-size: 0.9em;">{}</span>',
                url,
                obj.appartement.nom,
                obj.appartement.residence.nom
            )
        return '-'
    appartement_display.short_description = 'Appartement'
    appartement_display.admin_order_field = 'appartement__nom'
    
    def locataire_display(self, obj):
        """Affiche le locataire avec informations de contact"""
        if obj.locataire:
            url = reverse('admin:tiers_tiers_change', args=[obj.locataire.id])
            return format_html(
                '<a href="{}">{}</a><br><span style="color: #666; font-size: 0.9em;">{}</span>',
                url,
                obj.locataire.nom_complet,
                obj.locataire.email
            )
        return '-'
    locataire_display.short_description = 'Locataire'
    locataire_display.admin_order_field = 'locataire__nom'
    
    def is_active_display(self, obj):
        """Affiche le statut actif avec couleur"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Actif</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inactif</span>'
            )
    is_active_display.short_description = 'État actuel'
    is_active_display.boolean = True
    
    def montant_total_display(self, obj):
        """Affiche le montant total mensuel"""
        return f"{obj.montant_total_mensuel:,.0f} FCFA"
    montant_total_display.short_description = 'Total mensuel'
    
    def jours_restants_display(self, obj):
        """Affiche les jours restants avec couleur"""
        jours = obj.jours_restants
        if jours is None:
            return '-'
        elif jours <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Expiré</span>')
        elif jours <= 30:
            return format_html('<span style="color: orange; font-weight: bold;">{} jours</span>', jours)
        else:
            return f"{jours} jours"
    jours_restants_display.short_description = 'Jours restants'
    
    def bailleur_display(self, obj):
        """Affiche le propriétaire"""
        if obj.appartement and obj.appartement.residence and obj.appartement.residence.proprietaire:
            return obj.appartement.residence.proprietaire.nom_complet
        return '-'
    bailleur_display.short_description = 'Propriétaire'
    
    # Actions personnalisées
    actions = ['activer_contrats', 'suspendre_contrats', 'marquer_signes']
    
    def activer_contrats(self, request, queryset):
        """Active les contrats sélectionnés"""
        count = queryset.update(statut='actif')
        self.message_user(request, f'{count} contrats activés.')
    activer_contrats.short_description = 'Activer les contrats sélectionnés'
    
    def suspendre_contrats(self, request, queryset):
        """Suspend les contrats sélectionnés"""
        count = queryset.update(statut='suspendu')
        self.message_user(request, f'{count} contrats suspendus.')
    suspendre_contrats.short_description = 'Suspendre les contrats sélectionnés'
    
    def marquer_signes(self, request, queryset):
        """Marque les contrats comme signés"""
        from django.utils import timezone
        count = queryset.update(
            signe_par_locataire=True,
            signe_par_bailleur=True,
            date_signature=timezone.now().date()
        )
        self.message_user(request, f'{count} contrats marqués comme signés.')
    marquer_signes.short_description = 'Marquer comme signés'
    
    def save_model(self, request, obj, form, change):
        """Personnaliser la sauvegarde"""
        if not change:  # Nouveau contrat
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Champs en lecture seule selon le contexte"""
        readonly = list(self.readonly_fields)
        
        # Si le contrat est actif depuis plus de 30 jours, certains champs deviennent read-only
        if obj and obj.statut == 'actif':
            from django.utils import timezone
            from datetime import timedelta
            
            if obj.date_debut and obj.date_debut < timezone.now().date() - timedelta(days=30):
                readonly.extend(['appartement', 'locataire', 'date_debut'])
        
        return readonly
    
    class Media:
        css = {
            'all': ('admin/css/contracts_admin.css',)
        }
        js = ('admin/js/contracts_admin.js',)


# ============================================================================
# ADMIN PMO - Workflow et Documents
# ============================================================================

class DocumentContratInline(admin.TabularInline):
    """Inline pour les documents d'un workflow"""
    model = DocumentContrat
    extra = 1
    fields = ['type_document', 'fichier', 'statut', 'obligatoire', 'commentaire']
    readonly_fields = ['verifie_par', 'date_verification']


class HistoriqueWorkflowInline(admin.TabularInline):
    """Inline pour l'historique d'un workflow"""
    model = HistoriqueWorkflow
    extra = 0
    fields = ['etape_precedente', 'etape_suivante', 'effectue_par', 'date_transition', 'commentaire']
    readonly_fields = ['etape_precedente', 'etape_suivante', 'effectue_par', 'date_transition']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ContractWorkflow)
class ContractWorkflowAdmin(admin.ModelAdmin):
    """Administration des workflows PMO"""

    list_display = [
        'contrat_display',
        'etape_actuelle_display',
        'statut_dossier_display',
        'responsable_pmo',
        'progression_display',
        'facture_display',
        'created_at'
    ]

    list_filter = [
        'etape_actuelle',
        'statut_dossier',
        'responsable_pmo',
        'date_visite_entree',
        'created_at'
    ]

    search_fields = [
        'contrat__numero_contrat',
        'contrat__locataire__user__first_name',
        'contrat__locataire__user__last_name',
        'responsable_pmo__first_name',
        'responsable_pmo__last_name',
        'notes_pmo'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'progression_display',
        'peut_avancer_display'
    ]

    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Contrat et responsable', {
            'fields': (
                'contrat',
                'responsable_pmo',
                'statut_dossier'
            )
        }),
        ('Workflow', {
            'fields': (
                'etape_actuelle',
                'progression_display',
                'peut_avancer_display',
                'notes_pmo'
            )
        }),
        ('Facture', {
            'fields': (
                'facture',
                'facture_validee_le',
                'date_envoi_finance'
            ),
            'classes': ('collapse',)
        }),
        ('Rédaction', {
            'fields': (
                'date_debut_redaction',
            ),
            'classes': ('collapse',)
        }),
        ('Visite d\'entrée', {
            'fields': (
                'date_visite_entree',
                'lieu_rdv_visite',
                'observations_visite',
                'rapport_etat_lieux'
            ),
            'classes': ('collapse',)
        }),
        ('Remise des clés', {
            'fields': (
                'date_remise_cles',
                'nombre_cles',
                'cles_remises_par'
            ),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    inlines = [DocumentContratInline, HistoriqueWorkflowInline]

    actions = ['passer_etape_suivante', 'marquer_dossier_complet', 'envoyer_finance']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user',
            'responsable_pmo',
            'facture'
        )

    def contrat_display(self, obj):
        """Affiche le contrat avec lien"""
        url = reverse('admin:contracts_rentalcontract_change', args=[obj.contrat.id])
        return format_html(
            '<a href="{}">{}</a><br><span style="color: #666; font-size: 0.9em;">{}</span>',
            url,
            obj.contrat.numero_contrat,
            obj.contrat.locataire.nom_complet
        )
    contrat_display.short_description = 'Contrat'
    contrat_display.admin_order_field = 'contrat__numero_contrat'

    def etape_actuelle_display(self, obj):
        """Affiche l'étape actuelle avec couleur"""
        colors = {
            'verification_dossier': '#3b82f6',  # bleu
            'attente_facture': '#f59e0b',       # orange
            'facture_validee': '#10b981',       # vert
            'redaction_contrat': '#8b5cf6',     # violet
            'visite_entree': '#ec4899',         # rose
            'remise_cles': '#06b6d4',           # cyan
            'termine': '#22c55e',               # vert foncé
        }
        color = colors.get(obj.etape_actuelle, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.9em;">{}</span>',
            color,
            obj.get_etape_actuelle_display()
        )
    etape_actuelle_display.short_description = 'Étape actuelle'

    def statut_dossier_display(self, obj):
        """Affiche le statut du dossier avec couleur"""
        if obj.statut_dossier == 'complet':
            return format_html('<span style="color: green; font-weight: bold;">✓ Complet</span>')
        elif obj.statut_dossier == 'incomplet':
            return format_html('<span style="color: red; font-weight: bold;">✗ Incomplet</span>')
        else:
            return format_html('<span style="color: orange;">⏱ En cours</span>')
    statut_dossier_display.short_description = 'Dossier'

    def progression_display(self, obj):
        """Affiche la progression en pourcentage"""
        pourcent = obj.progression_pourcentage
        return format_html(
            '<div style="width: 100px; background-color: #e5e7eb; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; background-color: #10b981; height: 20px; text-align: center; color: white; font-size: 0.8em; line-height: 20px;">'
            '{}%'
            '</div>'
            '</div>',
            pourcent,
            pourcent
        )
    progression_display.short_description = 'Progression'

    def facture_display(self, obj):
        """Affiche la facture avec lien"""
        if obj.facture:
            url = reverse('admin:payments_invoice_change', args=[obj.facture.id])
            return format_html('<a href="{}">{}</a>', url, obj.facture.numero_facture)
        return '-'
    facture_display.short_description = 'Facture'

    def peut_avancer_display(self, obj):
        """Indique si le workflow peut avancer"""
        if obj.peut_avancer:
            return format_html('<span style="color: green;">✓ Peut avancer</span>')
        else:
            return format_html('<span style="color: red;">✗ Conditions non remplies</span>')
    peut_avancer_display.short_description = 'Peut avancer'

    # Actions personnalisées
    def passer_etape_suivante(self, request, queryset):
        """Fait avancer les workflows sélectionnés"""
        count = 0
        for workflow in queryset:
            if workflow.peut_avancer:
                if workflow.passer_etape_suivante():
                    count += 1
        self.message_user(request, f'{count} workflows avancés à l\'étape suivante.')
    passer_etape_suivante.short_description = 'Passer à l\'étape suivante'

    def marquer_dossier_complet(self, request, queryset):
        """Marque les dossiers comme complets"""
        count = queryset.update(statut_dossier='complet')
        self.message_user(request, f'{count} dossiers marqués comme complets.')
    marquer_dossier_complet.short_description = 'Marquer dossier complet'

    def envoyer_finance(self, request, queryset):
        """Envoie les workflows au service Finance"""
        from django.utils import timezone
        count = 0
        for workflow in queryset:
            if workflow.etape_actuelle == 'verification_dossier' and workflow.statut_dossier == 'complet':
                workflow.passer_etape_suivante()
                count += 1
        self.message_user(request, f'{count} workflows envoyés au service Finance.')
    envoyer_finance.short_description = 'Envoyer au service Finance'


@admin.register(DocumentContrat)
class DocumentContratAdmin(admin.ModelAdmin):
    """Administration des documents de contrat"""

    list_display = [
        'type_document',
        'workflow_display',
        'statut_display',
        'verifie_par',
        'date_verification',
        'obligatoire'
    ]

    list_filter = [
        'type_document',
        'statut',
        'obligatoire',
        'verifie_par',
        'date_verification'
    ]

    search_fields = [
        'workflow__contrat__numero_contrat',
        'type_document',
        'commentaire'
    ]

    readonly_fields = ['date_verification', 'created_at', 'updated_at']

    fieldsets = (
        ('Document', {
            'fields': (
                'workflow',
                'type_document',
                'fichier',
                'obligatoire'
            )
        }),
        ('Vérification', {
            'fields': (
                'statut',
                'verifie_par',
                'date_verification',
                'commentaire'
            )
        }),
        ('Informations système', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    actions = ['marquer_verifie', 'marquer_recu']

    def workflow_display(self, obj):
        """Affiche le workflow avec lien"""
        url = reverse('admin:contracts_contractworkflow_change', args=[obj.workflow.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.workflow.contrat.numero_contrat
        )
    workflow_display.short_description = 'Workflow'

    def statut_display(self, obj):
        """Affiche le statut avec couleur"""
        colors = {
            'attendu': '#f59e0b',
            'recu': '#3b82f6',
            'verifie': '#10b981',
            'refuse': '#ef4444'
        }
        color = colors.get(obj.statut, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.85em;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_display.short_description = 'Statut'

    def marquer_verifie(self, request, queryset):
        """Marque les documents comme vérifiés"""
        count = 0
        for doc in queryset:
            doc.marquer_comme_verifie(request.user)
            count += 1
        self.message_user(request, f'{count} documents marqués comme vérifiés.')
    marquer_verifie.short_description = 'Marquer comme vérifié'

    def marquer_recu(self, request, queryset):
        """Marque les documents comme reçus"""
        count = queryset.update(statut='recu')
        self.message_user(request, f'{count} documents marqués comme reçus.')
    marquer_recu.short_description = 'Marquer comme reçu'


@admin.register(HistoriqueWorkflow)
class HistoriqueWorkflowAdmin(admin.ModelAdmin):
    """Administration de l'historique des workflows"""

    list_display = [
        'workflow_display',
        'transition_display',
        'effectue_par',
        'date_transition'
    ]

    list_filter = [
        'etape_precedente',
        'etape_suivante',
        'effectue_par',
        'date_transition'
    ]

    search_fields = [
        'workflow__contrat__numero_contrat',
        'commentaire'
    ]

    readonly_fields = ['workflow', 'etape_precedente', 'etape_suivante', 'effectue_par', 'date_transition']

    date_hierarchy = 'date_transition'
    ordering = ['-date_transition']

    fieldsets = (
        ('Transition', {
            'fields': (
                'workflow',
                'etape_precedente',
                'etape_suivante',
                'date_transition',
                'effectue_par'
            )
        }),
        ('Détails', {
            'fields': (
                'commentaire',
            )
        })
    )

    def has_add_permission(self, request):
        """Empêche l'ajout manuel d'historique"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Empêche la suppression d'historique"""
        return False

    def workflow_display(self, obj):
        """Affiche le workflow avec lien"""
        url = reverse('admin:contracts_contractworkflow_change', args=[obj.workflow.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.workflow.contrat.numero_contrat
        )
    workflow_display.short_description = 'Workflow'

    def transition_display(self, obj):
        """Affiche la transition"""
        return format_html(
            '<span style="font-weight: bold;">{}</span> → <span style="font-weight: bold; color: #10b981;">{}</span>',
            obj.etape_precedente,
            obj.etape_suivante
        )
    transition_display.short_description = 'Transition'