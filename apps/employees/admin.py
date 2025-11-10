# apps/employees/admin.py - Configuration admin pour mobile
from django.contrib import admin
from .models import Task, Employee
from apps.maintenance.models import Intervention

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialite', 'statut', 'is_available', 'date_embauche']
    list_filter = ['specialite', 'statut', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('user',)
        }),
        ('Informations professionnelles', {
            'fields': ('specialite', 'date_embauche', 'statut', 'is_available')
        }),
        ('Contact', {
            'fields': ('telephone_professionnel',)
        }),
        ('Évaluation', {
            'fields': ('niveau_competence', 'note_moyenne')
        }),
        ('Notes', {
            'fields': ('notes',)
        })
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_tache', 'priorite', 'assigne_a', 'statut', 'date_prevue']
    list_filter = ['type_tache', 'priorite', 'statut', 'is_recurrente']
    search_fields = ['titre', 'description', 'assigne_a__first_name', 'assigne_a__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date_prevue'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('titre', 'description', 'type_tache', 'priorite')
        }),
        ('Assignation', {
            'fields': ('assigne_a', 'cree_par', 'bien')
        }),
        ('Planning', {
            'fields': ('date_prevue', 'duree_estimee', 'statut')
        }),
        ('Récurrence', {
            'fields': ('is_recurrente', 'recurrence_type', 'recurrence_fin'),
            'classes': ('collapse',)
        }),
        ('Résultats', {
            'fields': ('date_debut', 'date_fin', 'temps_passe', 'commentaire'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_complete', 'assign_to_me']
    
    def mark_as_complete(self, request, queryset):
        updated = queryset.filter(statut__in=['planifie', 'en_cours']).update(
            statut='complete',
            date_fin=timezone.now()
        )
        self.message_user(request, f'{updated} tâches marquées comme terminées.')
    mark_as_complete.short_description = "Marquer comme terminées"
    
    def assign_to_me(self, request, queryset):
        if request.user.user_type in ['agent_terrain', 'technicien']:
            updated = queryset.update(assigne_a=request.user)
            self.message_user(request, f'{updated} tâches assignées à vous.')
        else:
            self.message_user(request, "Vous ne pouvez pas vous assigner des tâches.", level='ERROR')
    assign_to_me.short_description = "M'assigner ces tâches"