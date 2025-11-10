# apps/contracts/permissions.py
"""
Permissions et contrôle d'accès pour le module contracts
"""

from rest_framework import permissions


class IsContractOwner(permissions.BasePermission):
    """
    Permission permettant uniquement au créateur du contrat ou staff de le modifier
    """

    def has_object_permission(self, request, view, obj):
        # Les méthodes de lecture sont autorisées pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True

        # Les permissions d'écriture sont accordées au créateur ou staff
        return obj.cree_par == request.user or request.user.is_staff


class IsLocataireOrProprietaireOrStaff(permissions.BasePermission):
    """
    Permission permettant au locataire, propriétaire ou staff de consulter le contrat
    """

    def has_object_permission(self, request, view, obj):
        # Staff a toujours accès
        if request.user.is_staff:
            return True

        # Le locataire peut consulter son propre contrat
        if hasattr(request.user, 'tiers'):
            if obj.locataire == request.user.tiers:
                return True

        # Le propriétaire peut consulter les contrats de ses biens
        if hasattr(request.user, 'tiers'):
            if obj.appartement.residence.proprietaire == request.user.tiers:
                return True

        return False


class CanManageContract(permissions.BasePermission):
    """
    Permission pour gérer les contrats (créer, modifier, supprimer)
    Réservé au staff (manager, accountant)
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff


class CanManageWorkflow(permissions.BasePermission):
    """
    Permission pour gérer les workflows PMO
    Réservé aux responsables PMO et managers
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Staff peut toujours gérer
        if request.user.is_staff:
            return True

        # Vérifier si l'utilisateur est responsable PMO
        return hasattr(request.user, 'workflows_pmo') and request.user.workflows_pmo.exists()

    def has_object_permission(self, request, view, obj):
        # Staff a toujours accès
        if request.user.is_staff:
            return True

        # Le responsable PMO assigné peut gérer
        return obj.responsable_pmo == request.user


class CanViewContract(permissions.BasePermission):
    """
    Permission pour consulter un contrat
    """

    def has_object_permission(self, request, view, obj):
        # Staff peut tout voir
        if request.user.is_staff:
            return True

        # Le locataire peut voir son contrat
        if hasattr(request.user, 'tiers') and obj.locataire == request.user.tiers:
            return True

        # Le propriétaire peut voir les contrats de ses biens
        if hasattr(request.user, 'tiers') and obj.appartement.residence.proprietaire == request.user.tiers:
            return True

        # Le créateur peut voir son contrat
        if obj.cree_par == request.user:
            return True

        return False


class CanModifyContract(permissions.BasePermission):
    """
    Permission pour modifier un contrat
    Seul le staff peut modifier
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff


class CanDeleteContract(permissions.BasePermission):
    """
    Permission pour supprimer un contrat
    Seuls les managers peuvent supprimer
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'manager'

    def has_object_permission(self, request, view, obj):
        # Seul un manager peut supprimer
        if request.user.user_type != 'manager':
            return False

        # On ne peut supprimer que les brouillons ou contrats expirés/résiliés
        return obj.statut in ['brouillon', 'expire', 'resilie']


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def can_user_access_contract(user, contract):
    """
    Vérifie si un utilisateur peut accéder à un contrat

    Args:
        user: L'utilisateur
        contract: Le contrat

    Returns:
        bool: True si l'utilisateur peut accéder au contrat
    """
    # Staff a toujours accès
    if user.is_staff:
        return True

    # Le locataire peut accéder à son contrat
    if hasattr(user, 'tiers') and contract.locataire == user.tiers:
        return True

    # Le propriétaire peut accéder aux contrats de ses biens
    if hasattr(user, 'tiers') and contract.appartement.residence.proprietaire == user.tiers:
        return True

    # Le créateur peut accéder au contrat
    if contract.cree_par == user:
        return True

    return False


def can_user_modify_contract(user, contract):
    """
    Vérifie si un utilisateur peut modifier un contrat

    Args:
        user: L'utilisateur
        contract: Le contrat

    Returns:
        bool: True si l'utilisateur peut modifier le contrat
    """
    # Seul le staff peut modifier
    return user.is_staff


def can_user_delete_contract(user, contract):
    """
    Vérifie si un utilisateur peut supprimer un contrat

    Args:
        user: L'utilisateur
        contract: Le contrat

    Returns:
        bool: True si l'utilisateur peut supprimer le contrat
    """
    # Seul un manager peut supprimer
    if user.user_type != 'manager':
        return False

    # On ne peut supprimer que les brouillons ou contrats terminés
    return contract.statut in ['brouillon', 'expire', 'resilie']


def can_user_manage_workflow(user, workflow):
    """
    Vérifie si un utilisateur peut gérer un workflow PMO

    Args:
        user: L'utilisateur
        workflow: Le workflow

    Returns:
        bool: True si l'utilisateur peut gérer le workflow
    """
    # Staff peut toujours gérer
    if user.is_staff:
        return True

    # Le responsable PMO assigné peut gérer
    if workflow.responsable_pmo == user:
        return True

    return False


def get_user_contracts(user):
    """
    Retourne les contrats accessibles par un utilisateur

    Args:
        user: L'utilisateur

    Returns:
        QuerySet: Les contrats accessibles
    """
    from .models import RentalContract

    # Staff peut voir tous les contrats
    if user.is_staff:
        return RentalContract.objects.all()

    # Locataire voit ses contrats
    if hasattr(user, 'tiers') and user.tiers.type_tiers == 'locataire':
        return RentalContract.objects.filter(locataire=user.tiers)

    # Propriétaire voit les contrats de ses biens
    if hasattr(user, 'tiers') and user.tiers.type_tiers == 'proprietaire':
        return RentalContract.objects.filter(
            appartement__residence__proprietaire=user.tiers
        )

    # Aucun contrat par défaut
    return RentalContract.objects.none()
