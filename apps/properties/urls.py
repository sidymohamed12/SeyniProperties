# apps/properties/urls.py - URLs complètes pour la gestion hiérarchique

from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    # === VUE PRINCIPALE ===
    # Redirige vers le dashboard des biens
    path('', views.properties_redirect_view, name='index'),

    # === PAGE D'ENREGISTREMENT UNIFIÉE ===
    path('enregistrement/', views.enregistrement_bien_view, name='enregistrement_bien'),

    # === GESTION DES RÉSIDENCES ===
    path('residences/', views.ResidenceListView.as_view(), name='residences_list'),
    path('residences/create/', views.ResidenceCreateView.as_view(), name='residence_create'),
    path('residences/<int:pk>/', views.ResidenceDetailView.as_view(), name='residence_detail'),
    path('residences/<int:pk>/edit/', views.ResidenceUpdateView.as_view(), name='residence_edit'),
    path('residences/<int:pk>/delete/', views.ResidenceDeleteView.as_view(), name='residence_delete'),
    
    # === GESTION DES APPARTEMENTS ===
    path('appartements/', views.AppartementListView.as_view(), name='appartements_list'),
    path('appartements/create/', views.AppartementCreateView.as_view(), name='appartement_create'),
    path('appartements/<int:pk>/', views.AppartementDetailView.as_view(), name='appartement_detail'),
    path('appartements/<int:pk>/edit/', views.AppartementUpdateView.as_view(), name='appartement_edit'),
    path('appartements/<int:pk>/delete/', views.AppartementDeleteView.as_view(), name='appartement_delete'),
    
    # === ACTIONS SUR APPARTEMENTS ===
    path('appartements/<int:pk>/set-available/', views.set_appartement_available, name='set_available'),
    path('appartements/<int:pk>/set-occupied/', views.set_appartement_occupied, name='set_occupied'),
    path('appartements/<int:pk>/set-maintenance/', views.set_appartement_maintenance, name='set_maintenance'),
    
    # === GESTION DES MÉDIAS ===
    path('appartements/<int:appartement_id>/medias/', views.AppartementMediaListView.as_view(), name='appartement_medias'),
    path('appartements/<int:appartement_id>/medias/upload/', views.upload_appartement_media, name='upload_media'),
    path('medias/<int:media_id>/delete/', views.delete_appartement_media, name='delete_media'),
    path('medias/<int:media_id>/set-main/', views.set_main_media, name='set_main_media'),
    
    # === APIs ET AJAX ===
    path('api/residences/by-landlord/<int:landlord_id>/', views.residences_by_landlord_api, name='residences_by_landlord'),
    path('api/appartements/by-residence/<int:residence_id>/', views.appartements_by_residence_api, name='appartements_by_residence'),
    path('api/appartement/<int:pk>/info/', views.appartement_info_api, name='appartement_info'),
    path('api/residence/<int:pk>/stats/', views.residence_stats_api, name='residence_stats'),
    
    # === EXPORTS ===
    path('export/residences/', views.export_residences_csv, name='export_residences'),
    path('export/appartements/', views.export_appartements_csv, name='export_appartements'),
    
    # === RAPPORTS ===
    path('reports/occupation/', views.rapport_occupation_view, name='rapport_occupation'),
    path('reports/residences/', views.rapport_residences_view, name='rapport_residences'),
    
    # === COMPATIBILITÉ AVEC L'ANCIEN SYSTÈME ===
    # Garde les anciennes URLs pour éviter les erreurs 404
    path('list/', views.AppartementListView.as_view(), name='list'),  # Redirige vers appartements
    path('add/', views.AppartementCreateView.as_view(), name='add'),   # Redirige vers create appartement
    path('<int:pk>/', views.appartement_detail_redirect, name='detail'),  # Redirige intelligemment
    path('<int:pk>/edit/', views.appartement_edit_redirect, name='edit'),  # Redirige intelligemment
    
    # === VUES SPÉCIALES ===
    # Vue combinée pour sélectionner résidence et appartement (pour les contrats par exemple)
    path('select/', views.property_selection_view, name='select'),
    # Vue de recherche avancée
    path('search/', views.property_search_view, name='search'),

     # === ÉTATS DES LIEUX ===
    path('etats-lieux/', views.etat_lieux_list_view, name='etat_lieux_list'),
    path('etats-lieux/create/', views.etat_lieux_create_view, name='etat_lieux_create'),
    path('etats-lieux/<int:pk>/', views.etat_lieux_detail_view, name='etat_lieux_detail'),
    path('etats-lieux/<int:pk>/edit/', views.etat_lieux_edit_view, name='etat_lieux_edit'),
    path('etats-lieux/<int:pk>/delete/', views.etat_lieux_delete_view, name='etat_lieux_delete'),
    path('etats-lieux/<int:pk>/download/', views.etat_lieux_download_pdf, name='etat_lieux_download'),
    path('etats-lieux/<int:pk>/preview/', views.etat_lieux_preview_pdf, name='etat_lieux_preview'),

    # === REMISES DE CLÉS ===
    path('remises-cles/', views.remise_cles_list_view, name='remise_cles_list'),
    path('remises-cles/create/', views.remise_cles_create_view, name='remise_cles_create'),
    path('remises-cles/<int:pk>/', views.remise_cles_detail_view, name='remise_cles_detail'),
    path('remises-cles/<int:pk>/edit/', views.remise_cles_edit_view, name='remise_cles_edit'),
    path('remises-cles/<int:pk>/delete/', views.remise_cles_delete_view, name='remise_cles_delete'),
    path('remises-cles/<int:pk>/download/', views.remise_cles_download_pdf, name='remise_cles_download'),
    path('remises-cles/<int:pk>/preview/', views.remise_cles_preview_pdf, name='remise_cles_preview'),
]