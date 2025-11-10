# apps/contracts/forms/__init__.py
"""
Formulaires du module contracts - Architecture modulaire

Ce fichier centralise les imports pour maintenir la rétrocompatibilité.
Les imports depuis l'ancien emplacement continuent de fonctionner:
    from apps.contracts.forms import RentalContractForm, DocumentUploadForm
"""

# Contract forms
from .contract_forms import (
    RentalContractForm,
    ContractFilterForm,
    ContractQuickCreateForm,
    AppartementSelectionForm,
    ContractRenewalForm,
    RentalContractFormLegacy,
)

# PMO forms
from .pmo_forms import (
    DocumentUploadForm,
    VisitePlanificationForm,
    EtatLieuxUploadForm,
    RemiseClesForm,
    WorkflowFilterForm,
    WorkflowNotesForm,
)

# PMO Workflow creation
from .pmo_workflow_create_form import WorkflowCreateForm

__all__ = [
    # Contract forms
    'RentalContractForm',
    'ContractFilterForm',
    'ContractQuickCreateForm',
    'AppartementSelectionForm',
    'ContractRenewalForm',
    'RentalContractFormLegacy',

    # PMO forms
    'DocumentUploadForm',
    'VisitePlanificationForm',
    'EtatLieuxUploadForm',
    'RemiseClesForm',
    'WorkflowFilterForm',
    'WorkflowNotesForm',
    'WorkflowCreateForm',
]
