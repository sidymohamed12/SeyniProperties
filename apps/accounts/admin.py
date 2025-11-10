from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Employe

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('user_type', 'phone', 'address', 'profile_picture')
        }),
        ('Dates importantes', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('date_created', 'date_updated')


# ════════════════════════════════════════════════════════════════════════════
# ADMINS BAILLEUR ET LOCATAIRE SUPPRIMÉS
# ════════════════════════════════════════════════════════════════════════════
# Ces admins ont été supprimés car les modèles Bailleur et Locataire
# ont été remplacés par le modèle Tiers (apps.tiers.models.Tiers).
#
# Pour gérer les propriétaires et locataires, utilisez l'admin Tiers:
# - Admin → Tiers → Ajouter un tiers
# - Filtrer par type_tiers: 'proprietaire' ou 'locataire'
# ════════════════════════════════════════════════════════════════════════════


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialite', 'date_embauche', 'statut', 'salaire')
    list_filter = ('specialite', 'statut', 'date_embauche')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'specialite'
    )
    date_hierarchy = 'date_embauche'

    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'specialite', 'date_embauche')
        }),
        ('Conditions d\'emploi', {
            'fields': ('salaire', 'statut')
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Filtrer les utilisateurs pour ne montrer que les employés
        if 'user' in form.base_fields:
            form.base_fields['user'].queryset = CustomUser.objects.filter(
                user_type__in=['manager', 'accountant', 'field_agent', 'technician']
            )
        return form


# Personnalisation de l'interface admin
admin.site.site_header = "Seyni Properties - Administration"
admin.site.site_title = "Seyni Properties"
admin.site.index_title = "Tableau de bord - Gestion Locative"
