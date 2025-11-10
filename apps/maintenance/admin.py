from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    # Nouveaux modèles unifiés
    Travail, TravailMedia, TravailChecklist,
    # Anciens modèles (dépréciés)
    Intervention, InterventionMedia, MaintenanceSchedule,
    InterventionChecklistItem, InterventionTemplate, InterventionTemplateChecklistItem,
    Tache
)


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = (
        'numero_intervention', 'property_display', 'type_intervention', 
        'priorite', 'statut', 'date_signalement'
    )
    list_filter = ('type_intervention', 'priorite', 'statut', 'date_signalement')
    search_fields = (
        'numero_intervention', 'bien__name', 'titre'  # CORRIGÉ: bien__name
    )
    readonly_fields = ('numero_intervention', 'created_at', 'updated_at', 'date_signalement')
    date_hierarchy = 'date_signalement'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('numero_intervention', 'bien', 'locataire', 'technicien')
        }),
        ('Détails intervention', {
            'fields': ('type_intervention', 'priorite', 'titre', 'description')
        }),
        ('Dates', {
            'fields': ('date_signalement', 'date_assignation', 'date_debut', 'date_fin')
        }),
        ('Coûts', {
            'fields': ('cout_estime', 'cout_reel'),
            'classes': ('collapse',)
        }),
        ('Statut et commentaires', {
            'fields': ('statut', 'commentaire_technicien', 'satisfaction_locataire')
        }),
        ('Métadonnées', {
            'fields': ('signale_par', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['assign_to_technician', 'mark_as_completed', 'mark_as_cancelled']
    
    def property_display(self, obj):
        """Affichage personnalisé de la propriété"""
        if obj.bien:
            return format_html(
                '<a href="{}" title="Voir la propriété">{}</a><br>'
                '<small style="color: #666;">{}</small>',
                reverse('admin:properties_property_change', args=[obj.bien.pk]),
                obj.bien.reference,
                obj.bien.name
            )
        return "-"
    property_display.short_description = 'Propriété'
    property_display.admin_order_field = 'bien__reference'
    
    def assign_to_technician(self, request, queryset):
        """Action pour assigner à un technicien"""
        self.message_user(
            request, 
            f"Assignation de {queryset.count()} intervention(s) - "
            "Fonctionnalité à implémenter complètement."
        )
    assign_to_technician.short_description = "Assigner à un technicien"
    
    def mark_as_completed(self, request, queryset):
        """Action pour marquer comme terminé"""
        updated = queryset.filter(statut__in=['signale', 'assigne', 'en_cours']).update(
            statut='complete'
        )
        self.message_user(request, f"{updated} intervention(s) marquée(s) comme terminée(s).")
    mark_as_completed.short_description = "Marquer comme terminées"
    
    def mark_as_cancelled(self, request, queryset):
        """Action pour annuler"""
        updated = queryset.filter(statut__in=['signale', 'assigne']).update(
            statut='annule'
        )
        self.message_user(request, f"{updated} intervention(s) annulée(s).")
    mark_as_cancelled.short_description = "Annuler les interventions"
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related(
            'bien', 'locataire', 'locataire__user', 'technicien'
        )


@admin.register(InterventionMedia)
class InterventionMediaAdmin(admin.ModelAdmin):
    list_display = (
        'intervention', 'type_media', 'description', 'created_at'  # CORRIGÉ: created_at
    )
    list_filter = ('type_media', 'created_at')  # CORRIGÉ: created_at
    search_fields = ('intervention__numero_intervention', 'description')
    readonly_fields = ('created_at', 'updated_at')  # CORRIGÉ: utiliser BaseModel fields
    
    fieldsets = (
        ('Intervention', {
            'fields': ('intervention', 'type_media', 'uploaded_by')
        }),
        ('Fichier', {
            'fields': ('fichier', 'description')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related('intervention', 'uploaded_by')


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'bien', 'type_maintenance', 'frequence', 
        'prochaine_maintenance', 'is_active'
    )
    list_filter = ('type_maintenance', 'frequence', 'is_active', 'prochaine_maintenance')
    search_fields = ('titre', 'bien__name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'prochaine_maintenance'
    
    actions = ['generate_interventions', 'activate_schedules', 'deactivate_schedules']
    
    def generate_interventions(self, request, queryset):
        """Action pour générer les interventions"""
        count = 0
        for schedule in queryset.filter(is_active=True):
            intervention = schedule.generate_next_intervention()
            if intervention:
                count += 1
        
        self.message_user(request, f"{count} intervention(s) générée(s).")
    generate_interventions.short_description = "Générer les interventions"
    
    def activate_schedules(self, request, queryset):
        """Action pour activer les programmations"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} programmation(s) activée(s).")
    activate_schedules.short_description = "Activer les programmations"
    
    def deactivate_schedules(self, request, queryset):
        """Action pour désactiver les programmations"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} programmation(s) désactivée(s).")
    deactivate_schedules.short_description = "Désactiver les programmations"


@admin.register(InterventionTemplate)
class InterventionTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'type_intervention', 'duree_estimee', 
        'cout_estime', 'is_active'
    )
    list_filter = ('type_intervention', 'is_active')
    search_fields = ('nom', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def activate_templates(self, request, queryset):
        """Action pour activer les templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} template(s) activé(s).")
    activate_templates.short_description = "Activer les templates"
    
    def deactivate_templates(self, request, queryset):
        """Action pour désactiver les templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} template(s) désactivé(s).")
    deactivate_templates.short_description = "Désactiver les templates"


# Enregistrement simple pour les autres modèles
admin.site.register(InterventionChecklistItem)
admin.site.register(InterventionTemplateChecklistItem)
admin.site.register(Tache)


# ============================================================================
# ADMIN POUR NOUVEAUX MODÈLES UNIFIÉS
# ============================================================================

class TravailMediaInline(admin.TabularInline):
    """Inline pour les médias d'un travail"""
    model = TravailMedia
    extra = 1
    fields = ('type_media', 'fichier', 'description', 'ajoute_par')
    readonly_fields = ('created_at',)


class TravailChecklistInline(admin.TabularInline):
    """Inline pour la checklist d'un travail"""
    model = TravailChecklist
    extra = 1
    fields = ('ordre', 'description', 'is_completed', 'notes')
    readonly_fields = ('completed_by', 'date_completion')


@admin.register(Travail)
class TravailAdmin(admin.ModelAdmin):
    """Administration du modèle Travail unifié"""

    list_display = (
        'numero_travail', 'titre', 'nature', 'type_travail',
        'priorite', 'statut', 'lieu_display', 'assigne_a_display',
        'date_prevue_display'
    )

    list_filter = (
        'nature', 'type_travail', 'priorite', 'statut',
        'is_recurrent', 'created_at'
    )

    search_fields = (
        'numero_travail', 'titre', 'description',
        'appartement__nom', 'residence__nom',
        'assigne_a__first_name', 'assigne_a__last_name'
    )

    readonly_fields = (
        'numero_travail', 'created_at', 'updated_at',
        'lieu_travail', 'duree_reelle', 'est_en_retard', 'necessite_materiel'
    )

    date_hierarchy = 'date_prevue'

    fieldsets = (
        ('Identification', {
            'fields': ('numero_travail', 'titre', 'description')
        }),
        ('Classification', {
            'fields': ('nature', 'type_travail', 'priorite', 'statut')
        }),
        ('Localisation', {
            'fields': ('appartement', 'residence', 'lieu_travail')
        }),
        ('Attribution', {
            'fields': ('signale_par', 'assigne_a', 'cree_par')
        }),
        ('Planification', {
            'fields': (
                'date_signalement', 'date_prevue', 'date_assignation',
                'date_debut', 'date_fin', 'duree_estimee', 'duree_reelle'
            )
        }),
        ('Récurrence', {
            'fields': ('is_recurrent', 'recurrence', 'recurrence_fin'),
            'classes': ('collapse',)
        }),
        ('Coûts et Matériel', {
            'fields': ('cout_estime', 'cout_reel', 'demande_achat', 'necessite_materiel'),
            'classes': ('collapse',)
        }),
        ('Suivi', {
            'fields': ('commentaire', 'notes_internes', 'satisfaction', 'temps_reel', 'est_en_retard')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [TravailMediaInline, TravailChecklistInline]

    actions = ['marquer_complete', 'marquer_annule', 'assigner_employe']

    def lieu_display(self, obj):
        """Affichage du lieu"""
        return obj.lieu_travail
    lieu_display.short_description = 'Lieu'

    def assigne_a_display(self, obj):
        """Affichage de la personne assignée"""
        if obj.assigne_a:
            return format_html(
                '<span style="color: #{};">{}</span>',
                '2563eb' if obj.statut == 'en_cours' else '6b7280',
                obj.assigne_a.get_full_name()
            )
        return format_html('<span style="color: #ef4444;">Non assigné</span>')
    assigne_a_display.short_description = 'Assigné à'

    def date_prevue_display(self, obj):
        """Affichage de la date prévue avec indicateur de retard"""
        if obj.date_prevue:
            color = '#ef4444' if obj.est_en_retard else '#10b981'
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                obj.date_prevue.strftime('%d/%m/%Y %H:%M')
            )
        return '-'
    date_prevue_display.short_description = 'Date prévue'
    date_prevue_display.admin_order_field = 'date_prevue'

    def marquer_complete(self, request, queryset):
        """Action pour marquer comme terminé"""
        count = 0
        for travail in queryset:
            if travail.statut not in ['complete', 'valide', 'annule']:
                travail.marquer_complete()
                count += 1

        self.message_user(request, f"{count} travail/travaux marqué(s) comme terminé(s).")
    marquer_complete.short_description = "Marquer comme terminé"

    def marquer_annule(self, request, queryset):
        """Action pour annuler"""
        updated = queryset.exclude(
            statut__in=['complete', 'valide', 'annule']
        ).update(statut='annule')

        self.message_user(request, f"{updated} travail/travaux annulé(s).")
    marquer_annule.short_description = "Annuler les travaux"

    def assigner_employe(self, request, queryset):
        """Action pour assigner à un employé"""
        self.message_user(
            request,
            f"Assignation de {queryset.count()} travail/travaux - "
            "Sélectionnez un employé dans le formulaire."
        )
    assigner_employe.short_description = "Assigner à un employé"

    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related(
            'appartement', 'residence', 'signale_par',
            'assigne_a', 'cree_par', 'demande_achat'
        ).prefetch_related('medias', 'checklist')


@admin.register(TravailMedia)
class TravailMediaAdmin(admin.ModelAdmin):
    """Administration des médias de travaux"""

    list_display = (
        'travail', 'type_media', 'description_courte', 'ajoute_par', 'created_at'
    )

    list_filter = ('type_media', 'created_at')

    search_fields = (
        'travail__numero_travail', 'travail__titre', 'description'
    )

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Travail', {
            'fields': ('travail', 'type_media', 'ajoute_par')
        }),
        ('Fichier', {
            'fields': ('fichier', 'description')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def description_courte(self, obj):
        """Affichage court de la description"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_courte.short_description = 'Description'

    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related(
            'travail', 'ajoute_par'
        )


@admin.register(TravailChecklist)
class TravailChecklistAdmin(admin.ModelAdmin):
    """Administration des checklists de travaux"""

    list_display = (
        'travail', 'description', 'ordre', 'is_completed',
        'completed_by', 'date_completion'
    )

    list_filter = ('is_completed', 'date_completion')

    search_fields = (
        'travail__numero_travail', 'travail__titre', 'description'
    )

    readonly_fields = ('created_at', 'updated_at', 'date_completion')

    ordering = ['travail', 'ordre']

    actions = ['marquer_complete_action']

    def marquer_complete_action(self, request, queryset):
        """Action pour marquer comme terminé"""
        count = 0
        for item in queryset.filter(is_completed=False):
            item.mark_completed(user=request.user)
            count += 1

        self.message_user(request, f"{count} élément(s) marqué(s) comme terminé(s).")
    marquer_complete_action.short_description = "Marquer comme terminé"

    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related(
            'travail', 'completed_by'
        )