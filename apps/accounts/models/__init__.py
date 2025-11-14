# apps/contracts/models/__init__.py
"""
Modèles du module contracts - Architecture modulaire

Ce fichier centralise les imports pour maintenir la rétrocompatibilité.
Les imports depuis l'ancien emplacement continuent de fonctionner:
    from apps.contracts.models import RentalContract, ContractWorkflow
"""

from .custom_user import CustomUser
from .employe import Employe

__all__ = [
    'CustomUser',
    'Employe',
]
