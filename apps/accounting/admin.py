from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    Expense, 
    LandlordStatement, 
    LandlordStatementDetail,
    AccountingPeriod,
    TaxDeclaration
)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'numero_expense', 'titre', 'categorie', 'montant', 
        'date_expense', 'statut', 'fournisseur'
    )
    list_filter = (
        'categorie', 'statut', 'moyen_paiement', 
        'date_expense', 'is_deductible'
    )
    search_fields = (
        'numero_expense', 'titre', 'description', 
        'fournisseur', 'numero_facture_fournisseur'
    )
    readonly_fields = ('numero_expense', 'created_at', 'updated_at')
    date_hierarchy = 'date_expense'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('numero_expense', 'titre', 'description', 'categorie')
        }),
        ('Montant et date', {
            'fields': ('montant', 'date_expense', 'moyen_paiement')
        }),
        ('Fournisseur', {
            'fields': ('fournisseur', 'numero_facture_fournisseur'),
            'classes': ('collapse',)
        }),
        ('Bien concerné', {
            'fields': ('bien',),
            'classes': ('collapse',)
        }),
        ('Fichiers', {
            'fields': ('facture_fichier', 'recu_paiement'),
            'classes': ('collapse',)
        }),
        ('Validation', {
            'fields': ('statut', 'saisie_par', 'valide_par', 'date_validation')
        }),
        ('Comptabilité', {
            'fields': ('is_deductible', 'notes'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['validate_expenses', 'mark_as_paid']
    
    def validate_expenses(self, request, queryset):
        """Action pour valider plusieurs dépenses"""
        updated = 0
        for expense in queryset.filter(statut='brouillon'):
            expense.validate_expense(request.user)
            updated += 1
        
        self.message_user(request, f"{updated} dépense(s) validée(s).")
    validate_expenses.short_description = "Valider les dépenses sélectionnées"
    
    def mark_as_paid(self, request, queryset):
        """Action pour marquer comme payé"""
        updated = queryset.update(statut='paye')
        self.message_user(request, f"{updated} dépense(s) marquée(s) comme payée(s).")
    mark_as_paid.short_description = "Marquer comme payé"


class LandlordStatementDetailInline(admin.TabularInline):
    model = LandlordStatementDetail
    extra = 0
    readonly_fields = ('net_bailleur', 'commission_montant', 'total_encaisse')
    
    def total_encaisse(self, obj):
        if obj.pk:
            return obj.total_encaisse
        return '-'
    total_encaisse.short_description = 'Total encaissé'


@admin.register(LandlordStatement)
class LandlordStatementAdmin(admin.ModelAdmin):
    list_display = (
        'numero_releve', 'proprietaire', 'periode_debut', 'periode_fin',
        'total_encaisse', 'commission_agence', 'montant_a_verser', 'statut'
    )
    list_filter = ('statut', 'periode_debut', 'periode_fin', 'moyen_envoi')
    search_fields = ('numero_releve', 'proprietaire__nom', 'proprietaire__prenom')
    readonly_fields = ('numero_releve', 'created_at', 'updated_at')
    date_hierarchy = 'periode_debut'
    inlines = [LandlordStatementDetailInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('numero_releve', 'proprietaire')
        }),
        ('Période', {
            'fields': ('periode_debut', 'periode_fin')
        }),
        ('Calculs', {
            'fields': (
                'total_encaisse', 'commission_agence', 'total_depenses',
                'montant_a_verser', 'nb_biens_concernes'
            )
        }),
        ('Statut et envoi', {
            'fields': ('statut', 'date_envoi', 'moyen_envoi', 'fichier_pdf')
        }),
        ('Métadonnées', {
            'fields': ('genere_par', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['calculate_totals', 'generate_pdf', 'mark_as_sent']
    
    def calculate_totals(self, request, queryset):
        """Action pour recalculer les totaux"""
        updated = 0
        for statement in queryset:
            statement.calculate_totals()
            statement.generate_details()
            updated += 1
        
        self.message_user(request, f"Totaux recalculés pour {updated} relevé(s).")
    calculate_totals.short_description = "Recalculer les totaux"
    
    def mark_as_sent(self, request, queryset):
        """Action pour marquer comme envoyé"""
        updated = queryset.update(statut='envoye', date_envoi=timezone.now())
        self.message_user(request, f"{updated} relevé(s) marqué(s) comme envoyé(s).")
    mark_as_sent.short_description = "Marquer comme envoyé"


@admin.register(LandlordStatementDetail)
class LandlordStatementDetailAdmin(admin.ModelAdmin):
    list_display = (
        'releve', 'bien', 'contrat', 'montant_loyer', 
        'montant_charges', 'commission_montant', 'net_bailleur'
    )
    # CORRIGÉ: Enlevé le filtre problématique temporairement
    list_filter = ('releve__periode_debut',)
    search_fields = ('releve__numero_releve',)
    readonly_fields = ('created_at', 'updated_at', 'total_encaisse')
    
    def total_encaisse(self, obj):
        return obj.total_encaisse
    total_encaisse.short_description = 'Total encaissé'


@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'date_debut', 'date_fin', 'total_revenus',
        'total_depenses', 'resultat_net', 'is_closed'
    )
    list_filter = ('is_closed', 'date_debut', 'date_fin')
    search_fields = ('nom',)
    readonly_fields = ('created_at', 'updated_at', 'date_cloture')
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        ('Période', {
            'fields': ('nom', 'date_debut', 'date_fin')
        }),
        ('Totaux', {
            'fields': ('total_revenus', 'total_depenses', 'resultat_net')
        }),
        ('Clôture', {
            'fields': ('is_closed', 'date_cloture', 'cloture_par')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['calculate_period_totals', 'close_periods']
    
    def calculate_period_totals(self, request, queryset):
        """Action pour recalculer les totaux des périodes"""
        updated = 0
        for period in queryset:
            period.calculate_totals()
            updated += 1
        
        self.message_user(request, f"Totaux recalculés pour {updated} période(s).")
    calculate_period_totals.short_description = "Recalculer les totaux"
    
    def close_periods(self, request, queryset):
        """Action pour clôturer les périodes"""
        updated = 0
        for period in queryset.filter(is_closed=False):
            if period.close_period(request.user):
                updated += 1
        
        self.message_user(request, f"{updated} période(s) clôturée(s).")
    close_periods.short_description = "Clôturer les périodes"


@admin.register(TaxDeclaration)
class TaxDeclarationAdmin(admin.ModelAdmin):
    list_display = (
        'periode', 'type_declaration', 'montant_du', 
        'date_echeance', 'statut', 'is_overdue_display'
    )
    list_filter = ('type_declaration', 'statut', 'date_echeance')
    search_fields = ('periode__nom', 'reference_paiement')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date_echeance'
    
    fieldsets = (
        ('Déclaration', {
            'fields': ('periode', 'type_declaration', 'montant_du', 'date_echeance')
        }),
        ('Paiement', {
            'fields': ('statut', 'date_paiement', 'reference_paiement')
        }),
        ('Fichiers', {
            'fields': ('fichier_declaration',),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue_display(self, obj):
        """Affiche si la déclaration est en retard"""
        if obj.is_overdue:
            return format_html('<span style="color: red;">En retard</span>')
        return format_html('<span style="color: green;">À jour</span>')
    is_overdue_display.short_description = 'Statut échéance'
    is_overdue_display.admin_order_field = 'date_echeance'
    
    actions = ['mark_as_paid', 'mark_as_declared']
    
    def mark_as_paid(self, request, queryset):
        """Action pour marquer comme payé"""
        updated = queryset.update(
            statut='paye', 
            date_paiement=timezone.now().date()
        )
        self.message_user(request, f"{updated} déclaration(s) marquée(s) comme payée(s).")
    mark_as_paid.short_description = "Marquer comme payé"
    
    def mark_as_declared(self, request, queryset):
        """Action pour marquer comme déclaré"""
        updated = queryset.update(statut='declare')
        self.message_user(request, f"{updated} déclaration(s) marquée(s) comme déclarée(s).")
    mark_as_declared.short_description = "Marquer comme déclaré"