# apps/payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Invoice, Payment, PaymentReminder, LigneDemandeAchat, HistoriqueValidation


class PaymentInline(admin.TabularInline):
    """Inline pour afficher les paiements dans les factures"""
    model = Payment
    extra = 0
    readonly_fields = ['numero_paiement', 'montant', 'date_paiement']
    fields = ['numero_paiement', 'montant', 'date_paiement', 'moyen_paiement', 'statut']
    can_delete = False


class LigneDemandeAchatInline(admin.TabularInline):
    """Inline pour les lignes de demande d'achat"""
    model = LigneDemandeAchat
    extra = 1
    fields = ('designation', 'quantite', 'unite', 'fournisseur', 'prix_unitaire', 'prix_total', 'motif')
    readonly_fields = ('prix_total',)


class HistoriqueValidationInline(admin.TabularInline):
    """Inline pour l'historique des validations"""
    model = HistoriqueValidation
    extra = 0
    fields = ('action', 'effectue_par', 'date_action', 'commentaire')
    readonly_fields = ('action', 'effectue_par', 'date_action')
    can_delete = False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Administration des factures"""
    list_display = [
        'numero_facture', 
        'type_facture', 
        'destinataire_nom', 
        'montant_ttc', 
        'date_emission',
        'date_echeance',
        'statut'
    ]
    list_filter = ['type_facture', 'statut', 'date_emission', 'is_manual']
    search_fields = ['numero_facture', 'destinataire_nom', 'description']
    readonly_fields = ['numero_facture', 'created_at', 'updated_at']
    date_hierarchy = 'date_emission'
    
    fieldsets = (
        ('Informations Générales', {
            'fields': (
                'numero_facture',
                'type_facture',
                'contrat',
                'is_manual',
                'statut',
                'etape_workflow'
            )
        }),
        ('Destinataire', {
            'fields': (
                'destinataire_nom',
                'destinataire_adresse',
                'destinataire_email',
                'destinataire_telephone'
            )
        }),
        ('Dates et Périodes', {
            'fields': (
                'date_emission',
                'date_echeance',
                'periode_debut',
                'periode_fin'
            )
        }),
        ('Montants', {
            'fields': (
                'montant_ht',
                'taux_tva',
                'montant_ttc'
            )
        }),
        ('Détails Spécifiques', {
            'fields': (
                'description',
                'notes',
                'reference_copropriete',
                'trimestre',
                'fournisseur_nom',
                'fournisseur_reference',
                'type_prestation',
                'numero_bon_commande',
                'categorie_achat'
            ),
            'classes': ('collapse',)
        }),
        ('Workflow Demande d\'Achat', {
            'fields': (
                'demandeur',
                'date_demande',
                'service_fonction',
                'motif_principal',
                'travail_lie',
                'valide_par_responsable',
                'date_validation_responsable',
                'commentaire_responsable',
                'traite_par_comptable',
                'date_traitement_comptable',
                'commentaire_comptable',
                'numero_cheque',
                'banque_cheque',
                'date_emission_cheque',
                'beneficiaire_cheque',
                'valide_par_dg',
                'date_validation_dg',
                'commentaire_dg',
                'date_reception',
                'receptionne_par',
                'remarques_reception'
            ),
            'classes': ('collapse',)
        }),
        ('Fichiers', {
            'fields': (
                'fichier_pdf',
                'fichier_pdf_nom'
            )
        }),
        ('Métadonnées', {
            'fields': (
                'creee_par',
                'created_at',
                'updated_at'
            )
        })
    )

    def get_inlines(self, request, obj=None):
        """Retourne les inlines selon le type de facture"""
        inlines = [PaymentInline]
        if obj and obj.type_facture == 'demande_achat':
            inlines.extend([LigneDemandeAchatInline, HistoriqueValidationInline])
        return inlines


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Administration des paiements"""
    list_display = [
        'numero_paiement',
        'facture',
        'montant',
        'date_paiement',
        'moyen_paiement',
        'statut',
        'valide_par'
    ]
    list_filter = ['statut', 'moyen_paiement', 'date_paiement', 'valide_par']
    search_fields = ['numero_paiement', 'facture__numero_facture', 'reference_transaction']
    readonly_fields = ['numero_paiement', 'valide_par', 'date_validation', 'created_at', 'updated_at']
    date_hierarchy = 'date_paiement'
    
    fieldsets = (
        ('Informations Paiement', {
            'fields': (
                'numero_paiement',
                'facture',
                'montant',
                'date_paiement',
                'moyen_paiement',
                'reference_transaction'
            )
        }),
        ('Statut', {
            'fields': (
                'statut',
                'valide_par',
                'date_validation'
            )
        }),
        ('Commentaire', {
            'fields': ('commentaire',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    """Administration des rappels de paiement"""
    list_display = [
        'facture',
        'date_envoi',
        'type_rappel',
        'moyen_envoi',
        'statut'
    ]
    list_filter = ['type_rappel', 'moyen_envoi', 'statut']
    search_fields = ['facture__numero_facture', 'message']
    readonly_fields = ['date_envoi']
    date_hierarchy = 'date_envoi'
    
    fieldsets = (
        ('Facture', {
            'fields': ('facture',)
        }),
        ('Rappel', {
            'fields': (
                'type_rappel',
                'moyen_envoi',
                'message',
                'statut'
            )
        }),
        ('Envoi', {
            'fields': (
                'date_envoi',
                'envoye_par'
            )
        })
    )


# ============================================================================
# ADMIN POUR NOUVEAUX MODÈLES MODULE 4
# ============================================================================

@admin.register(LigneDemandeAchat)
class LigneDemandeAchatAdmin(admin.ModelAdmin):
    """Administration des lignes de demande d'achat"""

    list_display = (
        'demande', 'designation', 'quantite', 'unite',
        'fournisseur', 'prix_unitaire_display', 'prix_total_display',
        'ecart_display'
    )

    list_filter = ('unite', 'created_at')

    search_fields = (
        'demande__numero_facture', 'designation', 'fournisseur', 'motif'
    )

    readonly_fields = ('prix_total', 'ecart_quantite', 'ecart_prix', 'created_at', 'updated_at')

    fieldsets = (
        ('Demande', {
            'fields': ('demande',)
        }),
        ('Article', {
            'fields': (
                'designation', 'quantite', 'unite',
                'fournisseur', 'motif'
            )
        }),
        ('Prix Estimé', {
            'fields': ('prix_unitaire', 'prix_total')
        }),
        ('Réception Réelle', {
            'fields': (
                'quantite_recue', 'prix_reel',
                'ecart_quantite', 'ecart_prix'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def prix_unitaire_display(self, obj):
        """Affichage du prix unitaire"""
        return format_html('<strong>{:,.0f} FCFA</strong>', obj.prix_unitaire)
    prix_unitaire_display.short_description = 'Prix Unitaire'

    def prix_total_display(self, obj):
        """Affichage du prix total"""
        return format_html('<strong>{:,.0f} FCFA</strong>', obj.prix_total)
    prix_total_display.short_description = 'Prix Total'

    def ecart_display(self, obj):
        """Affichage des écarts"""
        if obj.prix_reel and obj.ecart_prix:
            color = '#ef4444' if obj.ecart_prix > 0 else '#10b981'
            return format_html(
                '<span style="color: {};">{:+,.0f} FCFA</span>',
                color, obj.ecart_prix
            )
        return '-'
    ecart_display.short_description = 'Écart Prix'

    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related('demande')


@admin.register(HistoriqueValidation)
class HistoriqueValidationAdmin(admin.ModelAdmin):
    """Administration de l'historique des validations"""

    list_display = (
        'demande', 'action_display', 'effectue_par',
        'date_action', 'commentaire_court'
    )

    list_filter = ('action', 'date_action')

    search_fields = (
        'demande__numero_facture', 'commentaire',
        'effectue_par__first_name', 'effectue_par__last_name'
    )

    readonly_fields = ('date_action', 'created_at', 'updated_at')

    date_hierarchy = 'date_action'

    fieldsets = (
        ('Demande', {
            'fields': ('demande', 'action')
        }),
        ('Acteur', {
            'fields': ('effectue_par', 'date_action')
        }),
        ('Détails', {
            'fields': (
                'commentaire', 'ancienne_valeur', 'nouvelle_valeur'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def action_display(self, obj):
        """Affichage coloré de l'action"""
        color_map = {
            'creation': '#6b7280',
            'validation_responsable': '#10b981',
            'refus_responsable': '#ef4444',
            'traitement_comptable': '#3b82f6',
            'validation_dg': '#10b981',
            'refus_dg': '#ef4444',
            'paiement': '#10b981',
            'annulation': '#ef4444',
        }
        color = color_map.get(obj.action, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_action_display()
        )
    action_display.short_description = 'Action'
    action_display.admin_order_field = 'action'

    def commentaire_court(self, obj):
        """Affichage court du commentaire"""
        if obj.commentaire:
            return obj.commentaire[:50] + '...' if len(obj.commentaire) > 50 else obj.commentaire
        return '-'
    commentaire_court.short_description = 'Commentaire'

    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related(
            'demande', 'effectue_par'
        )