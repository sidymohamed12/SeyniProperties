# apps/payments/urls.py

from django.urls import path
from . import views
from . import views_invoices
from . import views_demandes_achat

app_name = 'payments'

urlpatterns = [
    # ==================== PAIEMENTS ====================
    path('', views.payments_list_view, name='list'),
    path('paiements/', views.payments_list_view, name='payments_list'),
    path('paiements/nouveau/', views.payment_create_view, name='create'),
    path('paiements/<int:pk>/', views.payment_detail_view, name='detail'),
    path('paiements/<int:pk>/quittance/', views.payment_receipt_download, name='receipt_download'),
    path('paiements/<int:pk>/quittance/preview/', views.payment_receipt_preview, name='receipt_preview'),
    
    # ==================== FACTURES - LISTE & DÉTAILS ====================
    path('factures/', views.invoices_list_view, name='invoices_list'),
    path('factures/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('factures/<int:pk>/download-pdf/', views.invoice_download_pdf, name='invoice_download_pdf'),
    path('factures/<int:pk>/send-email/', views.invoice_send_email, name='invoice_send_email'),
    
    # ==================== FACTURES - CRÉATION MANUELLE ====================
    path('factures/creer/', views_invoices.invoice_create_menu, name='invoice_create_menu'),
    path('factures/creer/loyer/', views_invoices.invoice_create_loyer, name='invoice_create_loyer'),
    path('factures/creer/syndic/', views_invoices.invoice_create_syndic, name='invoice_create_syndic'),
    path('factures/creer/achat/', views_invoices.invoice_create_achat, name='invoice_create_achat'),
    path('factures/creer/prestataire/', views_invoices.invoice_create_prestataire, name='invoice_create_prestataire'),
    
    # ==================== FACTURES - GÉNÉRATION PDF PERSONNALISÉE ====================
    path('factures/<int:pk>/pdf-custom/', views_invoices.generate_invoice_pdf_custom, name='invoice_pdf_custom'),
    path('factures/<int:pk>/preview-pdf/', views_invoices.invoice_preview_pdf, name='invoice_preview_pdf'),
    
    # ==================== RENOMMAGE DOCUMENTS ====================
    path('factures/<int:pk>/rename-pdf/', views_invoices.rename_invoice_pdf, name='rename_invoice_pdf'),
    path('documents/rename/', views_invoices.rename_document_ajax, name='rename_document_ajax'),
    
    # ==================== MODULE 8 - GÉNÉRATION DOCUMENTS BAILLEUR ====================
    # État de loyer
    path('factures/<int:pk>/etat-loyer/preview/', views.etat_loyer_preview, name='etat_loyer_preview'),
    path('factures/<int:pk>/etat-loyer/download/', views.etat_loyer_download, name='etat_loyer_download'),
    # Quittance
    path('factures/<int:pk>/quittance/preview/', views.quittance_preview, name='quittance_preview'),
    path('factures/<int:pk>/quittance/download/', views.quittance_download, name='quittance_download'),
    # Rappel
    path('factures/<int:pk>/envoyer-rappel/', views.envoyer_rappel_paiement, name='envoyer_rappel'),
    # Legacy (à supprimer après migration)
    path('factures/<int:pk>/generer-etat-loyer/', views.etat_loyer_preview, name='generer_etat_loyer'),
    path('factures/<int:pk>/generer-quittance/', views.quittance_preview, name='generer_quittance'),

    # ==================== API ====================
    path('api/paiements/<int:pk>/valider/', views.validate_payment_api, name='validate_payment_api'),
    path('api/stats/', views.payment_stats_api, name='payment_stats_api'),
    path('api/facture/<int:pk>/info/', views.get_invoice_info_api, name='invoice_info_api'),

    # ==================== MODULE 4 - DEMANDES D'ACHAT ====================
    # Dashboard
    path('demandes-achat/dashboard/', views_demandes_achat.dashboard_demandes_achat, name='demandes_achat_dashboard'),

    # Création et liste
    path('demandes-achat/', views_demandes_achat.demande_achat_list, name='demande_achat_list'),
    path('demandes-achat/nouvelle/', views_demandes_achat.demande_achat_create, name='demande_achat_create'),
    path('demandes-achat/<int:pk>/', views_demandes_achat.demande_achat_detail, name='demande_achat_detail'),

    # Workflow
    path('demandes-achat/<int:pk>/soumettre/', views_demandes_achat.demande_achat_soumettre, name='demande_achat_soumettre'),
    path('demandes-achat/<int:pk>/valider-responsable/', views_demandes_achat.demande_achat_validation_responsable, name='demande_achat_validation_responsable'),
    path('demandes-achat/<int:pk>/traiter-comptable/', views_demandes_achat.demande_achat_traitement_comptable, name='demande_achat_traitement_comptable'),
    path('demandes-achat/<int:pk>/valider-dg/', views_demandes_achat.demande_achat_validation_dg, name='demande_achat_validation_dg'),
    path('demandes-achat/<int:pk>/reception/', views_demandes_achat.demande_achat_reception, name='demande_achat_reception'),
]