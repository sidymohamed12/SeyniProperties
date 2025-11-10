# apps/contracts/serializers.py
"""
Serializers Django REST Framework pour le module contracts
"""

from rest_framework import serializers
from .models import RentalContract, ContractWorkflow, DocumentContrat, HistoriqueWorkflow


class RentalContractListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des contrats (données minimales)"""

    appartement_nom = serializers.CharField(source='appartement.nom', read_only=True)
    residence_nom = serializers.CharField(source='appartement.residence.nom', read_only=True)
    locataire_nom = serializers.CharField(source='locataire.nom_complet', read_only=True)
    proprietaire_nom = serializers.CharField(source='appartement.residence.proprietaire.nom_complet', read_only=True)
    montant_total = serializers.DecimalField(source='montant_total_mensuel', max_digits=10, decimal_places=2, read_only=True)
    jours_restants = serializers.IntegerField(read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = RentalContract
        fields = [
            'id', 'numero_contrat', 'date_debut', 'date_fin',
            'appartement_nom', 'residence_nom',
            'locataire_nom', 'proprietaire_nom',
            'loyer_mensuel', 'charges_mensuelles', 'montant_total',
            'statut', 'statut_display', 'jours_restants',
            'created_at'
        ]


class RentalContractDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'un contrat (toutes les données)"""

    appartement_details = serializers.SerializerMethodField()
    locataire_details = serializers.SerializerMethodField()
    proprietaire_details = serializers.SerializerMethodField()
    montant_total = serializers.DecimalField(source='montant_total_mensuel', max_digits=10, decimal_places=2, read_only=True)
    jours_restants = serializers.IntegerField(read_only=True)
    arrive_a_echeance = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    type_contrat_display = serializers.CharField(source='get_type_contrat_display', read_only=True)

    class Meta:
        model = RentalContract
        fields = '__all__'

    def get_appartement_details(self, obj):
        return {
            'id': obj.appartement.id,
            'nom': obj.appartement.nom,
            'type': obj.appartement.get_type_bien_display(),
            'residence': obj.appartement.residence.nom,
            'adresse': obj.appartement.residence.adresse,
            'ville': obj.appartement.residence.ville,
        }

    def get_locataire_details(self, obj):
        return {
            'id': obj.locataire.id,
            'nom_complet': obj.locataire.nom_complet,
            'email': obj.locataire.email,
            'telephone': obj.locataire.telephone,
        }

    def get_proprietaire_details(self, obj):
        proprietaire = obj.appartement.residence.proprietaire
        return {
            'id': proprietaire.id,
            'nom_complet': proprietaire.nom_complet,
            'email': proprietaire.email,
            'telephone': proprietaire.telephone,
        }


class RentalContractCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un contrat"""

    class Meta:
        model = RentalContract
        fields = [
            'appartement', 'locataire',
            'date_debut', 'date_fin', 'duree_mois',
            'loyer_mensuel', 'charges_mensuelles',
            'depot_garantie', 'frais_agence',
            'type_contrat', 'statut',
            'conditions_particulieres',
            'is_renouvelable', 'preavis_mois'
        ]

    def validate(self, data):
        """Validation personnalisée"""
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')

        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise serializers.ValidationError({
                    'date_fin': 'La date de fin doit être postérieure à la date de début'
                })

        return data


# ============================================================================
# CONTRACT WORKFLOW (PMO) SERIALIZERS
# ============================================================================

class ContractWorkflowListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des workflows"""

    contrat_numero = serializers.CharField(source='contrat.numero_contrat', read_only=True)
    locataire_nom = serializers.CharField(source='contrat.locataire.nom_complet', read_only=True)
    appartement = serializers.CharField(source='contrat.appartement.nom', read_only=True)
    residence = serializers.CharField(source='contrat.appartement.residence.nom', read_only=True)
    responsable_nom = serializers.CharField(source='responsable_pmo.get_full_name', read_only=True)
    progression = serializers.IntegerField(source='progression_pourcentage', read_only=True)
    etape_display = serializers.CharField(source='get_etape_actuelle_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_dossier_display', read_only=True)

    class Meta:
        model = ContractWorkflow
        fields = [
            'id', 'contrat_numero', 'locataire_nom',
            'appartement', 'residence',
            'etape_actuelle', 'etape_display',
            'statut_dossier', 'statut_display',
            'responsable_nom', 'progression',
            'created_at', 'updated_at'
        ]


class ContractWorkflowDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'un workflow"""

    contrat_details = serializers.SerializerMethodField()
    progression = serializers.IntegerField(source='progression_pourcentage', read_only=True)
    peut_avancer = serializers.BooleanField(read_only=True)
    documents_count = serializers.SerializerMethodField()
    historique_count = serializers.SerializerMethodField()
    etape_display = serializers.CharField(source='get_etape_actuelle_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_dossier_display', read_only=True)

    class Meta:
        model = ContractWorkflow
        fields = '__all__'

    def get_contrat_details(self, obj):
        return {
            'numero': obj.contrat.numero_contrat,
            'locataire': obj.contrat.locataire.nom_complet,
            'appartement': obj.contrat.appartement.nom,
            'residence': obj.contrat.appartement.residence.nom,
        }

    def get_documents_count(self, obj):
        return {
            'total': obj.documents.count(),
            'obligatoires': obj.documents.filter(obligatoire=True).count(),
            'verifies': obj.documents.filter(statut='verifie').count(),
            'en_attente': obj.documents.filter(statut='attendu').count(),
        }

    def get_historique_count(self, obj):
        return obj.historique.count()


# ============================================================================
# DOCUMENT CONTRACT SERIALIZERS
# ============================================================================

class DocumentContratSerializer(serializers.ModelSerializer):
    """Serializer pour les documents de contrat"""

    type_document_display = serializers.CharField(source='get_type_document_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    verifie_par_nom = serializers.CharField(source='verifie_par.get_full_name', read_only=True)
    workflow_numero = serializers.CharField(source='workflow.contrat.numero_contrat', read_only=True)

    class Meta:
        model = DocumentContrat
        fields = [
            'id', 'workflow', 'workflow_numero',
            'type_document', 'type_document_display',
            'fichier', 'statut', 'statut_display',
            'obligatoire', 'commentaire',
            'verifie_par', 'verifie_par_nom',
            'date_verification',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['verifie_par', 'date_verification']


# ============================================================================
# HISTORIQUE WORKFLOW SERIALIZERS
# ============================================================================

class HistoriqueWorkflowSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des workflows"""

    effectue_par_nom = serializers.CharField(source='effectue_par.get_full_name', read_only=True)
    workflow_numero = serializers.CharField(source='workflow.contrat.numero_contrat', read_only=True)

    class Meta:
        model = HistoriqueWorkflow
        fields = [
            'id', 'workflow', 'workflow_numero',
            'etape_precedente', 'etape_suivante',
            'effectue_par', 'effectue_par_nom',
            'date_transition', 'commentaire',
            'created_at'
        ]
        read_only_fields = ['date_transition']


# ============================================================================
# STATISTIQUES SERIALIZERS
# ============================================================================

class ContractStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des contrats"""

    total_contrats = serializers.IntegerField()
    contrats_actifs = serializers.IntegerField()
    contrats_expires = serializers.IntegerField()
    contrats_brouillons = serializers.IntegerField()
    contrats_resilies = serializers.IntegerField()
    revenus_mensuels_estimes = serializers.DecimalField(max_digits=12, decimal_places=2)
    taux_occupation = serializers.DecimalField(max_digits=5, decimal_places=2)


class WorkflowStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des workflows"""

    total = serializers.IntegerField()
    par_etape = serializers.DictField()
    par_statut = serializers.DictField()
    moyenne_progression = serializers.DecimalField(max_digits=5, decimal_places=2)
