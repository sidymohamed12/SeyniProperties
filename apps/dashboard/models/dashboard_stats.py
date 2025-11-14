from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.core.models import BaseModel

User = get_user_model()

class DashboardStats(BaseModel):
    """Modèle pour stocker les statistiques du dashboard (cache)"""
    
    date_snapshot = models.DateField(
        unique=True,
        verbose_name="Date du snapshot"
    )
    
    # Statistiques des biens
    total_biens = models.PositiveIntegerField(
        default=0,
        verbose_name="Total biens"
    )
    
    biens_occupes = models.PositiveIntegerField(
        default=0,
        verbose_name="Biens occupés"
    )
    
    biens_libres = models.PositiveIntegerField(
        default=0,
        verbose_name="Biens libres"
    )
    
    taux_occupation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Taux d'occupation (%)"
    )
    
    # Statistiques financières
    revenus_mensuels = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Revenus mensuels"
    )
    
    depenses_mensuelles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Dépenses mensuelles"
    )
    
    benefice_net = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Bénéfice net"
    )
    
    # Statistiques des paiements
    factures_en_attente = models.PositiveIntegerField(
        default=0,
        verbose_name="Factures en attente"
    )
    
    montant_en_attente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant en attente"
    )
    
    factures_en_retard = models.PositiveIntegerField(
        default=0,
        verbose_name="Factures en retard"
    )
    
    montant_en_retard = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant en retard"
    )
    
    # Statistiques des interventions
    interventions_ouvertes = models.PositiveIntegerField(
        default=0,
        verbose_name="Interventions ouvertes"
    )
    
    interventions_urgentes = models.PositiveIntegerField(
        default=0,
        verbose_name="Interventions urgentes"
    )
    
    interventions_en_retard = models.PositiveIntegerField(
        default=0,
        verbose_name="Interventions en retard"
    )
    
    # Statistiques des employés
    employes_actifs = models.PositiveIntegerField(
        default=0,
        verbose_name="Employés actifs"
    )
    
    taches_en_cours = models.PositiveIntegerField(
        default=0,
        verbose_name="Tâches en cours"
    )
    
    class Meta:
        verbose_name = "Statistiques dashboard"
        verbose_name_plural = "Statistiques dashboard"
        ordering = ['-date_snapshot']
    
    def __str__(self):
        return f"Stats du {self.date_snapshot}"
    
    @classmethod
    def generate_daily_stats(cls, date=None):
        """Génère les statistiques pour une date donnée"""
        from django.utils import timezone
        from django.db.models import Count, Sum, Q
        from apps.properties.models import Property
        from apps.payments.models import Invoice
        from apps.maintenance.models import Intervention
        from apps.employees.models import Task
        from apps.accounting.models.expenses import Expense
        from apps.payments.models import Payment
        
        if not date:
            date = timezone.now().date()
        
        # Statistiques des biens
        total_biens = Property.objects.count()
        biens_occupes = Property.objects.filter(
            statut_occupation='occupe'
        ).count()
        biens_libres = Property.objects.filter(
            statut_occupation='libre'
        ).count()
        taux_occupation = (
            (biens_occupes / total_biens * 100) 
            if total_biens > 0 else 0
        )
        
        # Statistiques financières (mois en cours)
        start_month = date.replace(day=1)
        if date.month == 12:
            end_month = date.replace(year=date.year + 1, month=1, day=1)
        else:
            end_month = date.replace(month=date.month + 1, day=1)
        
        revenus_mensuels = Payment.objects.filter(
            date_paiement__range=[start_month, date],
            statut='valide'
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
        
        depenses_mensuelles = Expense.objects.filter(
            date_expense__range=[start_month, date],
            statut='valide'
        ).aggregate(Sum('montant'))['montant__sum'] or Decimal('0.00')
        
        benefice_net = revenus_mensuels - depenses_mensuelles
        
        # Statistiques des paiements
        factures_stats = Invoice.objects.aggregate(
            en_attente=Count('id', filter=Q(statut='emise')),
            en_retard=Count('id', filter=Q(statut='en_retard')),
            montant_attente=Sum('montant_ttc', filter=Q(statut='emise')),
            montant_retard=Sum('montant_ttc', filter=Q(statut='en_retard'))
        )
        
        # Statistiques des interventions
        interventions_stats = Intervention.objects.aggregate(
            ouvertes=Count('id', filter=Q(statut__in=['signale', 'assigne', 'en_cours'])),
            urgentes=Count('id', filter=Q(priorite='urgente', statut__in=['signale', 'assigne', 'en_cours'])),
        )
        
        # Interventions en retard (logique complexe, simplifiée ici)
        interventions_en_retard = Intervention.objects.filter(
            statut__in=['signale', 'assigne', 'en_cours']
        ).count()  # À améliorer avec la logique is_overdue
        
        # Statistiques des employés
        employes_actifs = User.objects.filter(
            user_type__in=['technicien', 'agent_terrain'],
            is_active=True
        ).count()
        
        taches_en_cours = Task.objects.filter(
            statut__in=['planifie', 'en_cours']
        ).count()
        
        # Créer ou mettre à jour les stats
        stats, created = cls.objects.update_or_create(
            date_snapshot=date,
            defaults={
                'total_biens': total_biens,
                'biens_occupes': biens_occupes,
                'biens_libres': biens_libres,
                'taux_occupation': round(Decimal(str(taux_occupation)), 2),
                'revenus_mensuels': revenus_mensuels,
                'depenses_mensuelles': depenses_mensuelles,
                'benefice_net': benefice_net,
                'factures_en_attente': factures_stats['en_attente'] or 0,
                'montant_en_attente': factures_stats['montant_attente'] or Decimal('0.00'),
                'factures_en_retard': factures_stats['en_retard'] or 0,
                'montant_en_retard': factures_stats['montant_retard'] or Decimal('0.00'),
                'interventions_ouvertes': interventions_stats['ouvertes'] or 0,
                'interventions_urgentes': interventions_stats['urgentes'] or 0,
                'interventions_en_retard': interventions_en_retard,
                'employes_actifs': employes_actifs,
                'taches_en_cours': taches_en_cours,
            }
        )
        
        return stats


class DashboardWidget(BaseModel):
    """Modèle pour les widgets du dashboard"""
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du widget"
    )
    
    type_widget = models.CharField(
        max_length=20,
        choices=[
            ('stat_card', 'Carte statistique'),
            ('chart_line', 'Graphique linéaire'),
            ('chart_bar', 'Graphique en barres'),
            ('chart_pie', 'Graphique camembert'),
            ('table', 'Tableau'),
            ('list', 'Liste'),
        ],
        verbose_name="Type de widget"
    )
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets',
        verbose_name="Utilisateur",
        null=True,
        blank=True,
        help_text="Laisser vide pour un widget global"
    )
    
    # Position et taille
    position_x = models.PositiveIntegerField(
        default=0,
        verbose_name="Position X"
    )
    
    position_y = models.PositiveIntegerField(
        default=0,
        verbose_name="Position Y"
    )
    
    largeur = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Largeur (colonnes)"
    )
    
    hauteur = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Hauteur (lignes)"
    )
    
    # Configuration
    source_donnees = models.CharField(
        max_length=50,
        choices=[
            ('properties', 'Biens immobiliers'),
            ('payments', 'Paiements'),
            ('interventions', 'Interventions'),
            ('tasks', 'Tâches'),
            ('expenses', 'Dépenses'),
            ('kpis', 'KPIs'),
        ],
        verbose_name="Source de données"
    )
    
    filtres = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Filtres appliqués"
    )
    
    configuration = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Configuration du widget"
    )
    
    # Affichage
    is_visible = models.BooleanField(
        default=True,
        verbose_name="Visible"
    )
    
    couleur_theme = models.CharField(
        max_length=20,
        choices=[
            ('primary', 'Primaire'),
            ('secondary', 'Secondaire'),
            ('success', 'Succès'),
            ('warning', 'Avertissement'),
            ('danger', 'Danger'),
            ('info', 'Information'),
        ],
        default='primary',
        verbose_name="Couleur du thème"
    )
    
    # Cache
    donnees_cache = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données en cache"
    )
    
    date_cache = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date du cache"
    )
    
    duree_cache_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Durée du cache (minutes)"
    )
    
    class Meta:
        verbose_name = "Widget dashboard"
        verbose_name_plural = "Widgets dashboard"
        ordering = ['position_y', 'position_x']
        unique_together = [['utilisateur', 'nom']]
    
    def __str__(self):
        user_str = f" ({self.utilisateur.username})" if self.utilisateur else " (Global)"
        return f"{self.nom}{user_str}"
    
    @property
    def cache_expired(self):
        """Vérifie si le cache a expiré"""
        if not self.date_cache:
            return True
        
        from django.utils import timezone
        from datetime import timedelta
        
        expiry_time = self.date_cache + timedelta(minutes=self.duree_cache_minutes)
        return timezone.now() > expiry_time
    
    def get_data(self, force_refresh=False):
        """Récupère les données du widget (avec cache)"""
        if not force_refresh and not self.cache_expired and self.donnees_cache:
            return self.donnees_cache
        
        # Générer les nouvelles données
        data = self._generate_data()
        
        # Mettre à jour le cache
        from django.utils import timezone
        self.donnees_cache = data
        self.date_cache = timezone.now()
        self.save(update_fields=['donnees_cache', 'date_cache'])
        
        return data
    
    def _generate_data(self):
        """Génère les données selon la source configurée"""
        from django.db.models import Count, Sum, Avg
        
        if self.source_donnees == 'properties':
            from apps.properties.models import Property
            return self._get_properties_data()
        elif self.source_donnees == 'payments':
            from apps.payments.models import Payment, Invoice
            return self._get_payments_data()
        elif self.source_donnees == 'interventions':
            from apps.maintenance.models import Intervention
            return self._get_interventions_data()
        elif self.source_donnees == 'tasks':
            from apps.employees.models import Task
            return self._get_tasks_data()
        elif self.source_donnees == 'expenses':
            from apps.accounting.models.expenses import Expense
            return self._get_expenses_data()
        elif self.source_donnees == 'kpis':
            return self._get_kpis_data()
        
        return {}
    
    def _get_properties_data(self):
        """Génère les données pour les biens"""
        from apps.properties.models import Property
        from django.db.models import Count
        
        data = Property.objects.aggregate(
            total=Count('id'),
            libres=Count('id', filter=models.Q(statut_occupation='libre')),
            occupes=Count('id', filter=models.Q(statut_occupation='occupe')),
            maintenance=Count('id', filter=models.Q(statut_occupation='maintenance'))
        )
        
        # Répartition par type
        types_data = list(Property.objects.values('type_bien').annotate(
            count=Count('id')
        ).order_by('-count'))
        
        return {
            'totals': data,
            'by_type': types_data,
            'occupation_rate': (data['occupes'] / data['total'] * 100) if data['total'] > 0 else 0
        }
    
    def _get_payments_data(self):
        """Génère les données pour les paiements"""
        from apps.payments.models import Payment, Invoice
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        
        # Paiements du mois
        start_month = timezone.now().date().replace(day=1)
        
        monthly_payments = Payment.objects.filter(
            date_paiement__gte=start_month,
            statut='valide'
        ).aggregate(
            total=Sum('montant'),
            count=Count('id')
        )
        
        # Factures en attente
        pending_invoices = Invoice.objects.filter(
            statut__in=['emise', 'en_retard']
        ).aggregate(
            total=Sum('montant_ttc'),
            count=Count('id')
        )
        
        return {
            'monthly_payments': monthly_payments,
            'pending_invoices': pending_invoices
        }
    
    def _get_interventions_data(self):
        """Génère les données pour les interventions"""
        from apps.maintenance.models import Intervention
        from django.db.models import Count
        
        data = Intervention.objects.aggregate(
            total=Count('id'),
            ouvertes=Count('id', filter=models.Q(statut__in=['signale', 'assigne', 'en_cours'])),
            completees=Count('id', filter=models.Q(statut='complete')),
            urgentes=Count('id', filter=models.Q(priorite='urgente', statut__in=['signale', 'assigne', 'en_cours']))
        )
        
        # Répartition par type
        types_data = list(Intervention.objects.values('type_intervention').annotate(
            count=Count('id')
        ).order_by('-count')[:5])
        
        return {
            'totals': data,
            'by_type': types_data
        }
    
    def _get_tasks_data(self):
        """Génère les données pour les tâches"""
        from apps.employees.models import Task
        from django.db.models import Count
        
        data = Task.objects.aggregate(
            total=Count('id'),
            planifiees=Count('id', filter=models.Q(statut='planifie')),
            en_cours=Count('id', filter=models.Q(statut='en_cours')),
            completees=Count('id', filter=models.Q(statut='complete'))
        )
        
        return {'totals': data}
    
    def _get_expenses_data(self):
        """Génère les données pour les dépenses"""
        from apps.accounting.models.expenses import Expense
        from django.db.models import Sum, Count
        from django.utils import timezone
        
        # Dépenses du mois
        start_month = timezone.now().date().replace(day=1)
        
        monthly_expenses = Expense.objects.filter(
            date_expense__gte=start_month,
            statut='valide'
        ).aggregate(
            total=Sum('montant'),
            count=Count('id')
        )
        
        # Répartition par catégorie
        categories_data = list(Expense.objects.filter(
            date_expense__gte=start_month,
            statut='valide'
        ).values('categorie').annotate(
            total=Sum('montant')
        ).order_by('-total'))
        
        return {
            'monthly_expenses': monthly_expenses,
            'by_category': categories_data
        }
    
    def _get_kpis_data(self):
        """Génère les données pour les KPIs"""
        kpis = KPI.objects.filter(is_active=True).order_by('ordre_affichage')
        
        return {
            'kpis': [
                {
                    'nom': kpi.nom,
                    'valeur': float(kpi.valeur_actuelle),
                    'unite': kpi.get_unite_display(),
                    'tendance': kpi.tendance,
                    'evolution': float(kpi.evolution_pourcentage),
                    'couleur': kpi.couleur
                }
                for kpi in kpis
            ]
        }


class UserDashboardPreference(BaseModel):
    """Modèle pour les préférences utilisateur du dashboard"""
    
    utilisateur = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_preferences',
        verbose_name="Utilisateur"
    )
    
    layout = models.JSONField(
        default=dict,
        verbose_name="Configuration du layout"
    )
    
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Clair'),
            ('dark', 'Sombre'),
            ('auto', 'Automatique'),
        ],
        default='light',
        verbose_name="Thème"
    )
    
    widgets_actifs = models.JSONField(
        default=list,
        verbose_name="Widgets actifs"
    )
    
    refresh_interval = models.PositiveIntegerField(
        default=300,  # 5 minutes
        verbose_name="Intervalle de rafraîchissement (secondes)"
    )
    
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="Notifications activées"
    )
    
    class Meta:
        verbose_name = "Préférence dashboard"
        verbose_name_plural = "Préférences dashboard"
    
    def __str__(self):
        return f"Préférences de {self.utilisateur.username}"