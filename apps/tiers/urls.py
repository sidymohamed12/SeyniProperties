"""
URLs pour le module de gestion des tiers
"""
from django.urls import path
from . import views

app_name = 'tiers'

urlpatterns = [
    # Liste et recherche
    path('', views.tiers_liste, name='tiers_liste'),
    path('statistiques/', views.tiers_statistiques, name='tiers_statistiques'),
    path('search-api/', views.tiers_search_api, name='tiers_search_api'),

    # CRUD Tiers
    path('ajouter/', views.tiers_ajouter, name='tiers_ajouter'),
    path('<int:pk>/', views.tiers_detail, name='tiers_detail'),
    path('<int:pk>/modifier/', views.tiers_modifier, name='tiers_modifier'),
    path('<int:pk>/supprimer/', views.tiers_supprimer, name='tiers_supprimer'),

    # Gestion des comptes utilisateurs
    path('<int:pk>/creer-compte/', views.tiers_creer_compte, name='tiers_creer_compte'),
    path('<int:pk>/reinitialiser-mdp/', views.tiers_reinitialiser_mot_de_passe, name='tiers_reinitialiser_mot_de_passe'),

    # Liaison Tiers-Bien
    path('bien/ajouter/', views.tiers_bien_ajouter, name='tiers_bien_ajouter'),
    path('bien/ajouter/<int:tiers_pk>/', views.tiers_bien_ajouter, name='tiers_bien_ajouter'),
    path('bien/<int:pk>/modifier/', views.tiers_bien_modifier, name='tiers_bien_modifier'),
    path('bien/<int:pk>/supprimer/', views.tiers_bien_supprimer, name='tiers_bien_supprimer'),
]
