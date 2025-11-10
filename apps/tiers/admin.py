"""
Administration Django pour la gestion des tiers
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Tiers, TiersBien


@admin.register(Tiers)
class TiersAdmin(admin.ModelAdmin):
    """
    Administration des tiers
    """
    list_display = [
        'reference',
        'nom_complet_display',
        'type_tiers',
        'telephone',
        'email',
        'ville',
        'statut_badge',
        'nb_biens_lies',
        'date_ajout',
    ]

    list_filter = [
        'type_tiers',
        'statut',
        'ville',
        'date_ajout',
    ]

    search_fields = [
        'reference',
        'nom',
        'prenom',
        'email',
        'telephone',
        'adresse',
    ]

    readonly_fields = [
        'reference',
        'date_ajout',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Identification', {
            'fields': (
                'reference',
                'nom',
                'prenom',
                'type_tiers',
            )
        }),
        ('Coordonnées', {
            'fields': (
                'telephone',
                'telephone_secondaire',
                'email',
                'adresse',
                'ville',
                'quartier',
                'code_postal',
            )
        }),
        ('Statut et Documents', {
            'fields': (
                'statut',
                'piece_identite',
                'autre_document',
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        ('Gestion', {
            'fields': (
                'date_ajout',
                'cree_par',
                'modifie_par',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def nom_complet_display(self, obj):
        """Afficher le nom complet"""
        return obj.nom_complet
    nom_complet_display.short_description = 'Nom complet'

    def statut_badge(self, obj):
        """Afficher le statut avec un badge coloré"""
        colors = {
            'actif': 'success',
            'inactif': 'danger',
            'en_attente': 'warning',
            'archive': 'secondary',
        }
        color = colors.get(obj.statut, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def nb_biens_lies(self, obj):
        """Afficher le nombre de biens liés"""
        count = obj.biens_lies_count
        if count > 0:
            return format_html(
                '<span class="badge badge-info">{}</span>',
                count
            )
        return '-'
    nb_biens_lies.short_description = 'Biens liés'


@admin.register(TiersBien)
class TiersBienAdmin(admin.ModelAdmin):
    """
    Administration des liaisons tiers-bien
    """
    list_display = [
        'tiers',
        'bien_lie_display',
        'type_contrat',
        'type_mandat',
        'date_debut',
        'date_fin',
        'statut_badge',
        'duree_display',
    ]

    list_filter = [
        'type_contrat',
        'type_mandat',
        'statut',
        'date_debut',
    ]

    search_fields = [
        'tiers__nom',
        'tiers__prenom',
        'tiers__reference',
        'appartement__reference',
        'residence__reference',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    autocomplete_fields = [
        'tiers',
        'appartement',
        'residence',
    ]

    fieldsets = (
        ('Liaison', {
            'fields': (
                'tiers',
                'appartement',
                'residence',
            )
        }),
        ('Contrat', {
            'fields': (
                'type_contrat',
                'type_mandat',
                'date_debut',
                'date_fin',
                'statut',
            )
        }),
        ('Commissions', {
            'fields': (
                'montant_commission',
                'pourcentage_commission',
            ),
            'classes': ('collapse',),
        }),
        ('Documents', {
            'fields': (
                'contrat_signe',
                'mandat_document',
            ),
            'classes': ('collapse',),
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        ('Gestion', {
            'fields': (
                'cree_par',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def bien_lie_display(self, obj):
        """Afficher le bien lié"""
        return str(obj.bien_lie) if obj.bien_lie else '-'
    bien_lie_display.short_description = 'Bien'

    def statut_badge(self, obj):
        """Afficher le statut avec un badge coloré"""
        colors = {
            'en_cours': 'success',
            'termine': 'secondary',
            'suspendu': 'warning',
            'annule': 'danger',
        }
        color = colors.get(obj.statut, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'

    def duree_display(self, obj):
        """Afficher la durée"""
        return f"{obj.duree_jours} jours"
    duree_display.short_description = 'Durée'
