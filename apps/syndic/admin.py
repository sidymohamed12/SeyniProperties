"""
Configuration de l'interface d'administration pour le module syndic.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Copropriete, Coproprietaire, CotisationSyndic,
    PaiementCotisation, BudgetPrevisionnel, LigneBudget
)


class CoproprietaireInline(admin.TabularInline):
    """Inline pour afficher les copropriétaires dans l'admin de Copropriete."""
    model = Coproprietaire
    extra = 0
    fields = ['tiers', 'nombre_tantiemes', 'quote_part', 'date_entree', 'is_active']
    readonly_fields = ['quote_part']
    autocomplete_fields = ['tiers']


class LigneBudgetInline(admin.TabularInline):
    """Inline pour afficher les lignes de budget."""
    model = LigneBudget
    extra = 1
    fields = ['categorie', 'description', 'montant_prevu', 'montant_realise']


@admin.register(Copropriete)
class CoproprieteAdmin(admin.ModelAdmin):
    """Administration des copropriétés."""
    list_display = [
        'residence', 'nombre_tantiemes_total', 'nombre_coproprietaires',
        'periode_cotisation', 'budget_annuel', 'is_active'
    ]
    list_filter = ['is_active', 'periode_cotisation', 'date_debut_gestion']
    search_fields = ['residence__nom', 'residence__adresse']
    readonly_fields = ['nombre_coproprietaires', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations générales', {
            'fields': ('residence', 'date_debut_gestion', 'is_active')
        }),
        ('Structure de la copropriété', {
            'fields': ('nombre_tantiemes_total', 'nombre_coproprietaires')
        }),
        ('Budget et cotisations', {
            'fields': ('budget_annuel', 'periode_cotisation')
        }),
        ('Informations bancaires', {
            'fields': ('compte_bancaire',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [CoproprietaireInline]

    def nombre_coproprietaires(self, obj):
        """Affiche le nombre de copropriétaires."""
        count = obj.nombre_coproprietaires
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )
    nombre_coproprietaires.short_description = "Nb copropriétaires"


@admin.register(Coproprietaire)
class CoproprietaireAdmin(admin.ModelAdmin):
    """Administration des copropriétaires."""
    list_display = [
        'tiers', 'copropriete', 'nombre_tantiemes', 'quote_part',
        'total_impaye_display', 'is_active'
    ]
    list_filter = ['is_active', 'date_entree', 'copropriete']
    search_fields = ['tiers__nom', 'tiers__prenom', 'copropriete__residence__nom']
    readonly_fields = ['quote_part', 'cotisation_par_periode', 'created_at', 'updated_at']
    autocomplete_fields = ['tiers', 'copropriete']
    filter_horizontal = ['lots']

    fieldsets = (
        ('Identité', {
            'fields': ('tiers', 'copropriete', 'is_active')
        }),
        ('Tantièmes et quote-part', {
            'fields': ('nombre_tantiemes', 'quote_part', 'cotisation_par_periode')
        }),
        ('Lots détenus', {
            'fields': ('lots',)
        }),
        ('Dates', {
            'fields': ('date_entree', 'date_sortie')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_impaye_display(self, obj):
        """Affiche le total impayé avec couleur."""
        total = obj.get_total_impaye()
        if total > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:,.0f} FCFA</span>',
                total
            )
        return format_html('<span style="color: green;">0 FCFA</span>')
    total_impaye_display.short_description = "Total impayé"


class PaiementCotisationInline(admin.TabularInline):
    """Inline pour afficher les paiements dans l'admin de CotisationSyndic."""
    model = PaiementCotisation
    extra = 0
    fields = ['date_paiement', 'montant', 'mode_paiement', 'reference_paiement']
    readonly_fields = ['date_paiement']


@admin.register(CotisationSyndic)
class CotisationSyndicAdmin(admin.ModelAdmin):
    """Administration des cotisations syndic."""
    list_display = [
        'reference', 'coproprietaire', 'periode', 'montant_theorique',
        'montant_percu', 'montant_restant', 'statut_display', 'date_echeance'
    ]
    list_filter = ['statut', 'annee', 'date_echeance', 'coproprietaire__copropriete']
    search_fields = [
        'reference', 'coproprietaire__tiers__nom',
        'coproprietaire__tiers__prenom', 'periode'
    ]
    readonly_fields = [
        'reference', 'montant_restant', 'pourcentage_paye',
        'est_en_retard', 'jours_retard', 'created_at', 'updated_at'
    ]
    autocomplete_fields = ['coproprietaire']
    date_hierarchy = 'date_echeance'

    fieldsets = (
        ('Référence', {
            'fields': ('reference',)
        }),
        ('Copropriétaire', {
            'fields': ('coproprietaire',)
        }),
        ('Période', {
            'fields': ('periode', 'annee', 'date_emission', 'date_echeance')
        }),
        ('Montants', {
            'fields': (
                'montant_theorique', 'montant_percu', 'montant_restant',
                'pourcentage_paye'
            )
        }),
        ('Statut et paiement', {
            'fields': ('statut', 'date_paiement_complet')
        }),
        ('Relances', {
            'fields': ('nombre_relances', 'date_derniere_relance', 'est_en_retard', 'jours_retard'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [PaiementCotisationInline]

    actions = ['marquer_comme_paye', 'envoyer_relance']

    def statut_display(self, obj):
        """Affiche le statut avec couleur."""
        colors = {
            'a_venir': 'gray',
            'en_cours': 'blue',
            'paye': 'green',
            'impaye': 'red',
            'annule': 'orange',
        }
        color = colors.get(obj.statut, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_display.short_description = "Statut"

    def marquer_comme_paye(self, request, queryset):
        """Action pour marquer des cotisations comme payées."""
        count = 0
        for cotisation in queryset:
            if cotisation.statut != 'paye':
                cotisation.montant_percu = cotisation.montant_theorique
                cotisation.save()
                count += 1
        self.message_user(request, f"{count} cotisation(s) marquée(s) comme payée(s).")
    marquer_comme_paye.short_description = "Marquer comme payé"

    def envoyer_relance(self, request, queryset):
        """Action pour envoyer des relances."""
        # TODO: Implémenter l'envoi de relances via notifications
        count = queryset.filter(statut__in=['en_cours', 'impaye']).count()
        self.message_user(
            request,
            f"Relances envoyées pour {count} cotisation(s). (Fonctionnalité à implémenter)"
        )
    envoyer_relance.short_description = "Envoyer une relance"


@admin.register(PaiementCotisation)
class PaiementCotisationAdmin(admin.ModelAdmin):
    """Administration des paiements de cotisations."""
    list_display = [
        'cotisation', 'montant', 'mode_paiement', 'date_paiement',
        'reference_paiement', 'recu_genere'
    ]
    list_filter = ['mode_paiement', 'date_paiement', 'recu_genere']
    search_fields = [
        'cotisation__reference', 'reference_paiement',
        'cotisation__coproprietaire__tiers__nom'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['cotisation']
    date_hierarchy = 'date_paiement'

    fieldsets = (
        ('Cotisation', {
            'fields': ('cotisation',)
        }),
        ('Paiement', {
            'fields': ('montant', 'mode_paiement', 'date_paiement', 'reference_paiement')
        }),
        ('Reçu', {
            'fields': ('recu_genere',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BudgetPrevisionnel)
class BudgetPrevisionnelAdmin(admin.ModelAdmin):
    """Administration des budgets prévisionnels."""
    list_display = [
        'copropriete', 'annee', 'montant_total', 'montant_depense',
        'taux_execution_display', 'statut'
    ]
    list_filter = ['statut', 'annee']
    search_fields = ['copropriete__residence__nom']
    readonly_fields = ['montant_depense', 'taux_execution', 'montant_restant', 'created_at', 'updated_at']
    autocomplete_fields = ['copropriete']

    fieldsets = (
        ('Copropriété', {
            'fields': ('copropriete', 'annee', 'statut')
        }),
        ('Budget', {
            'fields': ('montant_total', 'montant_depense', 'taux_execution', 'montant_restant')
        }),
        ('Assemblée générale', {
            'fields': ('date_ag', 'date_vote')
        }),
        ('Document', {
            'fields': ('document',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [LigneBudgetInline]

    def taux_execution_display(self, obj):
        """Affiche le taux d'exécution avec barre de progression."""
        taux = obj.taux_execution
        color = 'green' if taux < 80 else 'orange' if taux < 100 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-weight: bold;">'
            '{}%</div></div>',
            min(taux, 100), color, int(taux)
        )
    taux_execution_display.short_description = "Taux d'exécution"


@admin.register(LigneBudget)
class LigneBudgetAdmin(admin.ModelAdmin):
    """Administration des lignes de budget."""
    list_display = [
        'budget', 'categorie', 'description', 'montant_prevu',
        'montant_realise', 'ecart', 'taux_realisation_display'
    ]
    list_filter = ['categorie', 'budget__annee', 'budget__copropriete']
    search_fields = ['description', 'budget__copropriete__residence__nom']
    readonly_fields = ['ecart', 'taux_realisation', 'created_at', 'updated_at']
    autocomplete_fields = ['budget']

    fieldsets = (
        ('Budget', {
            'fields': ('budget', 'categorie')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Montants', {
            'fields': ('montant_prevu', 'montant_realise', 'ecart', 'taux_realisation')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def taux_realisation_display(self, obj):
        """Affiche le taux de réalisation."""
        taux = obj.taux_realisation
        color = 'green' if taux < 80 else 'orange' if taux < 100 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, int(taux)
        )
    taux_realisation_display.short_description = "Taux réalisation"
