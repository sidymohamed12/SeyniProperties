# apps/contracts/models/__init__.py
"""
Modèles du module contracts - Architecture modulaire

Ce fichier centralise les imports pour maintenir la rétrocompatibilité.
Les imports depuis l'ancien emplacement continuent de fonctionner:
    from apps.contracts.models import RentalContract, ContractWorkflow
"""

from .accounting_period import AccountingPeriod, TaxDeclaration
from .expenses import Expense
from .landor_statement import LandlordStatement, LandlordStatementDetail

__all__ = [
    'AccountingPeriod',
    'TaxDeclaration',
    'Expense',
    'LandlordStatement',
    'LandlordStatementDetail',
]
