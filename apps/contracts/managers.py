# apps/contracts/managers.py
"""
Custom QuerySet Managers pour le module contracts
Optimisation des requêtes et centralisation de la logique métier
"""

from django.db import models
from django.db.models import Q, Count, Sum, Avg, Prefetch
from django.utils import timezone
from datetime import timedelta


class RentalContractQuerySet(models.QuerySet):
    """QuerySet personnalisé pour les contrats de location"""

    def active(self):
        """Retourne uniquement les contrats actifs"""
        return self.filter(statut='actif')

    def expired(self):
        """Retourne les contrats expirés"""
        return self.filter(statut='expire')

    def draft(self):
        """Retourne les contrats en brouillon"""
        return self.filter(statut='brouillon')

    def terminated(self):
        """Retourne les contrats résiliés"""
        return self.filter(statut='resilie')

    def with_details(self):
        """Précharge toutes les relations nécessaires pour éviter les N+1 queries"""
        return self.select_related(
            'appartement__residence__proprietaire__user',
            'locataire__user',
            'cree_par'
        ).prefetch_related(
            'appartement__residence__appartements'
        )

    def expiring_soon(self, days=30):
        """
        Retourne les contrats actifs qui expirent dans X jours

        Args:
            days (int): Nombre de jours avant expiration (défaut: 30)
        """
        today = timezone.now().date()
        limit_date = today + timedelta(days=days)

        return self.filter(
            statut='actif',
            date_fin__gte=today,
            date_fin__lte=limit_date
        ).with_details().order_by('date_fin')

    def by_residence(self, residence_id):
        """Filtrer par résidence"""
        return self.filter(appartement__residence_id=residence_id)

    def by_proprietaire(self, proprietaire_id):
        """Filtrer par propriétaire (Tiers)"""
        return self.filter(appartement__residence__proprietaire_id=proprietaire_id)

    def by_locataire(self, locataire_id):
        """Filtrer par locataire (Tiers)"""
        return self.filter(locataire_id=locataire_id)

    def with_workflow(self):
        """Précharge le workflow PMO si existant"""
        from .models import ContractWorkflow
        return self.prefetch_related(
            Prefetch(
                'workflow',
                queryset=ContractWorkflow.objects.select_related('responsable_pmo', 'facture')
            )
        )

    def revenue_stats(self):
        """Calcule les statistiques de revenus"""
        return self.active().aggregate(
            total_loyers=Sum('loyer_mensuel'),
            moyenne_loyer=Avg('loyer_mensuel'),
            total_charges=Sum('charges_mensuelles'),
            total_contrats=Count('id')
        )

    def search(self, query):
        """
        Recherche dans les contrats

        Args:
            query (str): Terme de recherche
        """
        if not query:
            return self

        return self.filter(
            Q(numero_contrat__icontains=query) |
            Q(appartement__nom__icontains=query) |
            Q(appartement__residence__nom__icontains=query) |
            Q(locataire__nom__icontains=query) |
            Q(locataire__prenom__icontains=query) |
            Q(locataire__email__icontains=query)
        )

    def requiring_action(self):
        """
        Contrats nécessitant une action (expiration proche, signatures manquantes, etc.)
        """
        today = timezone.now().date()
        soon = today + timedelta(days=30)

        return self.filter(
            Q(statut='actif', date_fin__lte=soon) |  # Expire bientôt
            Q(statut='brouillon', created_at__lte=timezone.now() - timedelta(days=7)) |  # Brouillon ancien
            Q(statut='actif', signe_par_locataire=False) |  # Pas signé par locataire
            Q(statut='actif', signe_par_bailleur=False)  # Pas signé par bailleur
        ).distinct()


class RentalContractManager(models.Manager):
    """Manager pour RentalContract"""

    def get_queryset(self):
        return RentalContractQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def expired(self):
        return self.get_queryset().expired()

    def draft(self):
        return self.get_queryset().draft()

    def with_details(self):
        return self.get_queryset().with_details()

    def expiring_soon(self, days=30):
        return self.get_queryset().expiring_soon(days)

    def by_residence(self, residence_id):
        return self.get_queryset().by_residence(residence_id)

    def revenue_stats(self):
        return self.get_queryset().revenue_stats()

    def requiring_action(self):
        return self.get_queryset().requiring_action()


# ============================================================================
# CONTRACT WORKFLOW (PMO) MANAGERS
# ============================================================================

class ContractWorkflowQuerySet(models.QuerySet):
    """QuerySet personnalisé pour les workflows PMO"""

    def with_relations(self):
        """Précharge toutes les relations"""
        return self.select_related(
            'contrat__appartement__residence__proprietaire',
            'contrat__locataire',
            'responsable_pmo',
            'facture',
            'cles_remises_par'
        ).prefetch_related(
            'documents',
            'historique'
        )

    def at_stage(self, etape):
        """Filtrer par étape du workflow"""
        return self.filter(etape_actuelle=etape)

    def verification_dossier(self):
        """Workflows en vérification de dossier"""
        return self.at_stage('verification_dossier')

    def attente_facture(self):
        """Workflows en attente de facture"""
        return self.at_stage('attente_facture')

    def redaction_contrat(self):
        """Workflows en rédaction de contrat"""
        return self.at_stage('redaction_contrat')

    def visite_entree(self):
        """Workflows en visite d'entrée"""
        return self.at_stage('visite_entree')

    def termine(self):
        """Workflows terminés"""
        return self.at_stage('termine')

    def dossier_complet(self):
        """Workflows avec dossier complet"""
        return self.filter(statut_dossier='complet')

    def dossier_incomplet(self):
        """Workflows avec dossier incomplet"""
        return self.filter(statut_dossier='incomplet')

    def urgent(self, days=7):
        """
        Workflows urgents (en attente depuis plus de X jours)

        Args:
            days (int): Nombre de jours (défaut: 7)
        """
        limit_date = timezone.now() - timedelta(days=days)
        return self.filter(
            created_at__lte=limit_date,
            etape_actuelle__in=['verification_dossier', 'attente_facture', 'redaction_contrat']
        ).exclude(etape_actuelle='termine')

    def by_responsable(self, responsable_id):
        """Filtrer par responsable PMO"""
        return self.filter(responsable_pmo_id=responsable_id)

    def progress_stats(self):
        """Statistiques de progression"""
        return self.aggregate(
            total=Count('id'),
            moyenne_progression=Avg('progression_pourcentage'),
            termines=Count('id', filter=Q(etape_actuelle='termine'))
        )


class ContractWorkflowManager(models.Manager):
    """Manager pour ContractWorkflow"""

    def get_queryset(self):
        return ContractWorkflowQuerySet(self.model, using=self._db)

    def with_relations(self):
        return self.get_queryset().with_relations()

    def at_stage(self, etape):
        return self.get_queryset().at_stage(etape)

    def urgent(self, days=7):
        return self.get_queryset().urgent(days)

    def dossier_complet(self):
        return self.get_queryset().dossier_complet()

    def progress_stats(self):
        return self.get_queryset().progress_stats()


# ============================================================================
# DOCUMENT CONTRACT MANAGERS
# ============================================================================

class DocumentContratQuerySet(models.QuerySet):
    """QuerySet personnalisé pour les documents de contrat"""

    def obligatoires(self):
        """Documents obligatoires uniquement"""
        return self.filter(obligatoire=True)

    def optionnels(self):
        """Documents optionnels"""
        return self.filter(obligatoire=False)

    def en_attente(self):
        """Documents en attente"""
        return self.filter(statut='attendu')

    def recus(self):
        """Documents reçus"""
        return self.filter(statut='recu')

    def verifies(self):
        """Documents vérifiés"""
        return self.filter(statut='verifie')

    def refuses(self):
        """Documents refusés"""
        return self.filter(statut='refuse')

    def by_workflow(self, workflow_id):
        """Filtrer par workflow"""
        return self.filter(workflow_id=workflow_id)

    def manquants_obligatoires(self, workflow_id):
        """Documents obligatoires manquants pour un workflow"""
        return self.filter(
            workflow_id=workflow_id,
            obligatoire=True
        ).exclude(statut='verifie')


class DocumentContratManager(models.Manager):
    """Manager pour DocumentContrat"""

    def get_queryset(self):
        return DocumentContratQuerySet(self.model, using=self._db)

    def obligatoires(self):
        return self.get_queryset().obligatoires()

    def verifies(self):
        return self.get_queryset().verifies()

    def manquants_obligatoires(self, workflow_id):
        return self.get_queryset().manquants_obligatoires(workflow_id)
