"""
URLs pour le module syndic.
"""
from django.urls import path
from . import views

app_name = 'syndic'

urlpatterns = [
    # Dashboard
    path('', views.syndic_dashboard, name='dashboard'),

    # Copropriétés
    path('coproprietes/', views.copropriete_list, name='copropriete_list'),
    path('coproprietes/creer/', views.copropriete_create, name='copropriete_create'),
    path('coproprietes/<int:pk>/', views.copropriete_detail, name='copropriete_detail'),
    path('coproprietes/<int:pk>/modifier/', views.copropriete_update, name='copropriete_update'),
    path('coproprietes/<int:pk>/supprimer/', views.copropriete_delete, name='copropriete_delete'),

    # Copropriétaires
    path('coproprietaires/', views.coproprietaire_list, name='coproprietaire_list'),
    path('coproprietaires/creer/', views.coproprietaire_create, name='coproprietaire_create'),
    path('coproprietaires/<int:pk>/modifier/', views.coproprietaire_update, name='coproprietaire_update'),
    path('coproprietaires/<int:pk>/supprimer/', views.coproprietaire_delete, name='coproprietaire_delete'),

    # Cotisations
    path('cotisations/', views.cotisation_list, name='cotisation_list'),
    path('cotisations/creer/', views.cotisation_create, name='cotisation_create'),
    path('cotisations/<int:pk>/', views.cotisation_detail, name='cotisation_detail'),
    path('cotisations/<int:pk>/modifier/', views.cotisation_update, name='cotisation_update'),
    path('cotisations/<int:pk>/supprimer/', views.cotisation_delete, name='cotisation_delete'),

    # Paiements
    path('cotisations/<int:cotisation_pk>/paiement/', views.paiement_create, name='paiement_create'),

    # Budgets
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/creer/', views.budget_create, name='budget_create'),
    path('budgets/<int:pk>/', views.budget_detail, name='budget_detail'),
    path('budgets/<int:pk>/modifier/', views.budget_update, name='budget_update'),
    path('budgets/<int:pk>/supprimer/', views.budget_delete, name='budget_delete'),
]
