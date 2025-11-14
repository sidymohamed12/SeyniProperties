# apps/properties/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models.residence import Residence
from .models.appartement import Appartement
from .models.appartement import Appartement, AppartementMedia
from .models.etat_lieu import EtatDesLieux, EtatDesLieuxDetail
from .models.remise import RemiseDesCles
from .models.properties import Property

class AppartementInline(admin.TabularInline):
    """Inline pour afficher les appartements dans la résidence"""
    model = Appartement
    extra = 0
    fields = [
        'nom', 'etage', 'type_bien', 'superficie', 'nb_pieces', 
        'statut_occupation', 'loyer_base', 'charges'
    ]
    readonly_fields = ['reference']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('residence')


class AppartementMediaInline(admin.TabularInline):
    """Inline pour les médias des appartements"""
    model = AppartementMedia
    extra = 0
    fields = ['type_media', 'titre', 'fichier', 'is_principal', 'ordre', 'is_public']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('appartement')


@admin.register(Residence)
class ResidenceAdmin(admin.ModelAdmin):
    """Administration des résidences"""
    
    list_display = [
        'reference', 'nom', 'quartier', 'ville', 'bailleur_nom', 
        'nb_appartements_display', 'taux_occupation_display', 'statut'
    ]
    
    list_filter = [
        'statut', 'type_residence', 'ville', 'quartier',
        ('proprietaire', admin.RelatedOnlyFieldListFilter),
        'created_at'
    ]

    search_fields = [
        'reference', 'nom', 'adresse', 'quartier',
        'proprietaire__nom', 'proprietaire__prenom'
    ]
    
    readonly_fields = [
        'reference', 'created_at', 'updated_at', 
        'nb_appartements_reel', 'taux_occupation_display'
    ]
    
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'nom', 'type_residence', 'statut')
        }),
        ('Localisation', {
            'fields': ('adresse', 'quartier', 'ville', 'code_postal', 'latitude', 'longitude')
        }),
        ('Propriétaire', {
            'fields': ('proprietaire',)
        }),
        ('Caractéristiques', {
            'fields': ('nb_etages', 'nb_appartements_total', 'nb_appartements_reel', 'annee_construction')
        }),
        ('Informations Complémentaires', {
            'fields': ('description', 'equipements'),
            'classes': ('collapse',)
        }),
        ('Statistiques', {
            'fields': ('taux_occupation_display',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [AppartementInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'proprietaire'
        ).prefetch_related('appartements')

    def bailleur_nom(self, obj):
        """Affiche le nom du propriétaire"""
        return obj.proprietaire.nom_complet
    bailleur_nom.short_description = 'Propriétaire'
    bailleur_nom.admin_order_field = 'proprietaire__nom'
    
    def nb_appartements_display(self, obj):
        """Affiche le nombre d'appartements avec lien"""
        count = obj.appartements.count()
        url = reverse('admin:properties_appartement_changelist')
        return format_html(
            '<a href="{}?residence__id__exact={}">{} appartements</a>',
            url, obj.id, count
        )
    nb_appartements_display.short_description = 'Appartements'
    
    def nb_appartements_reel(self, obj):
        """Nombre réel d'appartements"""
        return obj.appartements.count()
    nb_appartements_reel.short_description = 'Nombre réel d\'appartements'
    
    def taux_occupation_display(self, obj):
        """Affiche le taux d'occupation"""
        taux = obj.taux_occupation

        # ✅ Formate le nombre AVANT format_html
        taux_str = f"{taux:.1f}"

        if taux >= 90:
            color = 'green'
        elif taux >= 70:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            taux_str  # ✅ Utilise la variable formatée
        )
    taux_occupation_display.short_description = 'Taux d\'occupation'


@admin.register(Appartement)
class AppartementAdmin(admin.ModelAdmin):
    """Administration des appartements"""
    
    list_display = [
        'reference', 'nom', 'residence_nom', 'etage', 'type_bien',
        'superficie', 'statut_occupation', 'loyer_total_display', 'locataire_actuel_display'
    ]
    
    list_filter = [
        'statut_occupation', 'type_bien', 'mode_location', 'is_meuble',
        ('residence', admin.RelatedOnlyFieldListFilter),
        ('residence__proprietaire', admin.RelatedOnlyFieldListFilter),
        'residence__ville', 'residence__quartier',
        'created_at'
    ]

    search_fields = [
        'reference', 'nom', 'residence__nom', 'residence__adresse',
        'residence__proprietaire__nom', 'residence__proprietaire__prenom'
    ]
    
    readonly_fields = [
        'reference', 'created_at', 'updated_at', 'bailleur_display',
        'adresse_complete_display', 'loyer_total_display', 'locataire_actuel_display'
    ]
    
    fieldsets = (
        ('Identification', {
            'fields': ('reference', 'nom', 'residence')
        }),
        ('Localisation', {
            'fields': ('etage', 'bailleur_display', 'adresse_complete_display')
        }),
        ('Caractéristiques', {
            'fields': (
                'type_bien', 'superficie', 'nb_pieces', 'nb_chambres', 'nb_sdb', 'nb_wc'
            )
        }),
        ('Équipements', {
            'fields': (
                'is_meuble', 'has_balcon', 'has_parking', 'has_climatisation', 'equipements_inclus'
            ),
            'classes': ('collapse',)
        }),
        ('Statut et Location', {
            'fields': ('statut_occupation', 'mode_location')
        }),
        ('Tarification', {
            'fields': ('loyer_base', 'charges', 'depot_garantie', 'frais_agence', 'loyer_total_display')
        }),
        ('Informations Complémentaires', {
            'fields': ('description', 'notes_internes'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_derniere_renovation', 'date_mise_en_location'),
            'classes': ('collapse',)
        }),
        ('Locataire Actuel', {
            'fields': ('locataire_actuel_display',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [AppartementMediaInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'residence__proprietaire'
        ).prefetch_related('contrats')
    
    def residence_nom(self, obj):
        """Affiche le nom de la résidence avec lien"""
        url = reverse('admin:properties_residence_change', args=[obj.residence.id])
        return format_html('<a href="{}">{}</a>', url, obj.residence.nom)
    residence_nom.short_description = 'Résidence'
    residence_nom.admin_order_field = 'residence__nom'
    
    def bailleur_display(self, obj):
        """Affiche le propriétaire"""
        return obj.residence.proprietaire.nom_complet
    bailleur_display.short_description = 'Propriétaire'
    
    def adresse_complete_display(self, obj):
        """Affiche l'adresse complète"""
        return obj.adresse_complete
    adresse_complete_display.short_description = 'Adresse complète'
    
    def loyer_total_display(self, obj):
        """Affiche le loyer total formaté"""
        return f"{obj.loyer_total:,.0f} FCFA"
    loyer_total_display.short_description = 'Loyer total'
    loyer_total_display.admin_order_field = 'loyer_base'
    
    def locataire_actuel_display(self, obj):
        """Affiche le locataire actuel s'il existe"""
        locataire = obj.locataire_actuel
        if locataire:
            return f"{locataire.nom_complet}"
        return "Libre"
    locataire_actuel_display.short_description = 'Locataire actuel'
    
    # Actions personnalisées
    actions = ['marquer_libre', 'marquer_occupe', 'marquer_maintenance']
    
    def marquer_libre(self, request, queryset):
        """Marque les appartements sélectionnés comme libres"""
        count = queryset.update(statut_occupation='libre')
        self.message_user(request, f'{count} appartements marqués comme libres.')
    marquer_libre.short_description = 'Marquer comme libre'
    
    def marquer_occupe(self, request, queryset):
        """Marque les appartements sélectionnés comme occupés"""
        count = queryset.update(statut_occupation='occupe')
        self.message_user(request, f'{count} appartements marqués comme occupés.')
    marquer_occupe.short_description = 'Marquer comme occupé'
    
    def marquer_maintenance(self, request, queryset):
        """Marque les appartements sélectionnés en maintenance"""
        count = queryset.update(statut_occupation='maintenance')
        self.message_user(request, f'{count} appartements marqués en maintenance.')
    marquer_maintenance.short_description = 'Marquer en maintenance'


@admin.register(AppartementMedia)
class AppartementMediaAdmin(admin.ModelAdmin):
    """Administration des médias d'appartements"""
    
    list_display = [
        'appartement', 'type_media', 'titre', 'is_principal', 
        'is_public', 'ordre', 'created_at'
    ]
    
    list_filter = [
        'type_media', 'is_principal', 'is_public',
        ('appartement__residence', admin.RelatedOnlyFieldListFilter),
        'created_at'
    ]
    
    search_fields = [
        'titre', 'description',
        'appartement__nom', 'appartement__residence__nom'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Média', {
            'fields': ('appartement', 'type_media', 'fichier')
        }),
        ('Informations', {
            'fields': ('titre', 'description')
        }),
        ('Options d\'affichage', {
            'fields': ('is_principal', 'is_public', 'ordre')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'appartement__residence'
        )


# ====== ADMIN POUR L'ANCIEN MODÈLE PROPERTY (Temporaire) ======

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """
    Administration de l'ancien modèle Property (Temporaire)
    DÉPRÉCIÉ - À supprimer après migration complète
    """
    
    list_display = [
        'reference', 'name', 'property_type', 'neighborhood', 
        'city', 'occupancy_status', 'total_rent_display', 'landlord_name'
    ]
    
    list_filter = [
        'occupancy_status', 'property_type', 'rental_mode', 'city', 'neighborhood',
        ('landlord', admin.RelatedOnlyFieldListFilter),
        'is_furnished', 'created_at'
    ]
    
    search_fields = [
        'reference', 'name', 'address', 'neighborhood',
        'landlord__user__first_name', 'landlord__user__last_name'
    ]
    
    readonly_fields = [
        'reference', 'created_at', 'updated_at', 'total_rent_display'
    ]
    
    fieldsets = (
        ('⚠️ MODÈLE DÉPRÉCIÉ', {
            'description': 'Ce modèle est déprécié. Utilisez le nouveau modèle Appartement.',
            'fields': ()
        }),
        ('Identification', {
            'fields': ('reference', 'name', 'property_type')
        }),
        ('Localisation', {
            'fields': ('address', 'neighborhood', 'city', 'postal_code')
        }),
        ('Propriétaire', {
            'fields': ('landlord',)
        }),
        ('Caractéristiques', {
            'fields': (
                'surface_area', 'rooms_count', 'bedrooms_count', 
                'bathrooms_count', 'is_furnished'
            )
        }),
        ('Statut et Location', {
            'fields': ('occupancy_status', 'rental_mode')
        }),
        ('Tarification', {
            'fields': ('base_rent', 'charges', 'security_deposit', 'total_rent_display')
        }),
        ('Informations Complémentaires', {
            'fields': ('description', 'amenities'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('landlord__user')
    
    def landlord_name(self, obj):
        """Affiche le nom du bailleur"""
        return obj.landlord.user.get_full_name()
    landlord_name.short_description = 'Bailleur'
    landlord_name.admin_order_field = 'landlord__user__last_name'
    
    def total_rent_display(self, obj):
        """Affiche le loyer total formaté"""
        return f"{obj.total_rent:,.0f} FCFA"
    total_rent_display.short_description = 'Loyer total'
    
    class Media:
        css = {
            'all': ('admin/css/deprecated_model.css',)
        }


# Configuration de l'admin
admin.site.site_header = "Seyni Properties - Administration"
admin.site.site_title = "Seyni Properties Admin"
admin.site.index_title = "Gestion Immobilière"

# Personnalisation des messages d'aide
admin.site.empty_value_display = '(Aucun)'




@admin.register(EtatDesLieux)
class EtatDesLieuxAdmin(admin.ModelAdmin):
    list_display = (
        'numero_etat', 'type_etat', 'appartement', 'locataire',
        'date_etat', 'is_complet', 'created_at'
    )
    list_filter = ('type_etat', 'signe_bailleur', 'signe_locataire', 'date_etat')
    search_fields = (
        'numero_etat', 'appartement__numero_appartement',
        'locataire__user__first_name', 'locataire__user__last_name'
    )
    readonly_fields = ('numero_etat', 'created_at', 'updated_at')
    date_hierarchy = 'date_etat'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_etat', 'type_etat', 'date_etat')
        }),
        ('Liens', {
            'fields': ('contrat', 'appartement', 'locataire', 'commercial_imany')
        }),
        ('Observations', {
            'fields': ('observation_globale',)
        }),
        ('Signatures', {
            'fields': ('signe_bailleur', 'signe_locataire', 'date_signature')
        }),
        ('Fichiers', {
            'fields': ('fichier_pdf',)
        }),
        ('Métadonnées', {
            'fields': ('cree_par', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EtatDesLieuxDetail)
class EtatDesLieuxDetailAdmin(admin.ModelAdmin):
    list_display = ('etat_lieux', 'piece', 'corps_etat', 'ordre')
    list_filter = ('piece',)
    search_fields = ('piece', 'corps_etat', 'observations')


@admin.register(RemiseDesCles)
class RemiseDesClesAdmin(admin.ModelAdmin):
    list_display = (
        'numero_attestation', 'type_remise', 'appartement', 'locataire',
        'date_remise', 'total_cles', 'is_complet', 'created_at'
    )
    list_filter = ('type_remise', 'signe_bailleur', 'signe_locataire', 'date_remise')
    search_fields = (
        'numero_attestation', 'appartement__numero_appartement',
        'locataire__user__first_name', 'locataire__user__last_name',
        'remis_par', 'recu_par'
    )
    readonly_fields = ('numero_attestation', 'total_cles', 'created_at', 'updated_at')
    date_hierarchy = 'date_remise'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero_attestation', 'type_remise', 'date_remise', 'heure_remise')
        }),
        ('Liens', {
            'fields': ('contrat', 'appartement', 'locataire', 'etat_lieux')
        }),
        ('Clés et équipements', {
            'fields': (
                'nombre_cles_appartement', 'nombre_cles_boite_lettres',
                'nombre_cles_garage', 'nombre_badges', 'nombre_telecommandes',
                'autres_equipements', 'total_cles'
            )
        }),
        ('Parties', {
            'fields': ('remis_par', 'recu_par')
        }),
        ('Observations', {
            'fields': ('observations',)
        }),
        ('Signatures', {
            'fields': ('signe_bailleur', 'signe_locataire', 'date_signature')
        }),
        ('Fichiers', {
            'fields': ('fichier_pdf',)
        }),
        ('Métadonnées', {
            'fields': ('cree_par', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )