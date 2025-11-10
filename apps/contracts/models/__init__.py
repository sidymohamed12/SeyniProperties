# apps/contracts/models/__init__.py
"""
Modèles du module contracts - Architecture modulaire

Ce fichier centralise les imports pour maintenir la rétrocompatibilité.
Les imports depuis l'ancien emplacement continuent de fonctionner:
    from apps.contracts.models import RentalContract, ContractWorkflow
"""

from .contract import RentalContract
from .workflow import ContractWorkflow
from .document import DocumentContrat
from .history import HistoriqueWorkflow

__all__ = [
    'RentalContract',
    'ContractWorkflow',
    'DocumentContrat',
    'HistoriqueWorkflow',
]
