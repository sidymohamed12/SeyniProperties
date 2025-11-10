from .dashboard_views import *
from .copropriete_views import *
from .cotisation_views import *
from .coproprietaire_views import *
from .budget_views import *

__all__ = [
    # Dashboard
    'syndic_dashboard',

    # Coproprietes
    'copropriete_list',
    'copropriete_detail',
    'copropriete_create',
    'copropriete_update',
    'copropriete_delete',

    # Coproprietaires
    'coproprietaire_list',
    'coproprietaire_create',
    'coproprietaire_update',
    'coproprietaire_delete',

    # Cotisations
    'cotisation_list',
    'cotisation_detail',
    'cotisation_create',
    'cotisation_update',
    'cotisation_delete',

    # Paiements
    'paiement_create',

    # Budgets
    'budget_list',
    'budget_detail',
    'budget_create',
    'budget_update',
    'budget_delete',
]
