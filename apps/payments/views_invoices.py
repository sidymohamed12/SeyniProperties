# apps/payments/views_invoices.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
import logging
import os

from .models.invoice import Invoice
from .forms import (
    InvoiceLoyerForm, InvoiceSyndicForm, 
    InvoiceDemandeAchatForm, InvoicePrestataireForm,
    RenameDocumentForm
)

logger = logging.getLogger(__name__)


# ==================== CRÉATION FACTURES MANUELLES ====================

@login_required
def invoice_create_menu(request):
    """Menu de sélection du type de facture à créer"""
    
    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas les permissions pour créer des factures.")
        return redirect('dashboard:index')
    
    context = {
        'types_factures': [
            {
                'type': 'loyer',
                'titre': 'Facture de Loyer',
                'description': 'Créer une facture de loyer manuelle',
                'icon': 'fa-home',
                'color': 'blue',
                'url': 'payments:invoice_create_loyer'
            },
            {
                'type': 'syndic',
                'titre': 'Facture Syndic',
                'description': 'Cotisations trimestrielles de copropriété',
                'icon': 'fa-building',
                'color': 'purple',
                'url': 'payments:invoice_create_syndic'
            },
            {
                'type': 'demande_achat',
                'titre': 'Demande d\'Achat',
                'description': 'Facture pour achats et approvisionnements',
                'icon': 'fa-shopping-cart',
                'color': 'green',
                'url': 'payments:invoice_create_achat'
            },
            {
                'type': 'prestataire',
                'titre': 'Facture Prestataire',
                'description': 'Services externes (plombier, électricien, etc.)',
                'icon': 'fa-tools',
                'color': 'orange',
                'url': 'payments:invoice_create_prestataire'
            },
        ]
    }
    
    return render(request, 'payments/invoices/create_menu.html', context)


@login_required
def invoice_create_loyer(request):
    """Créer une facture de loyer manuelle"""
    
    if not request.user.is_staff:
        messages.error(request, "Permission refusée.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = InvoiceLoyerForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.creee_par = request.user
            invoice.statut = 'emise'
            invoice.save()
            
            messages.success(
                request,
                f"✅ Facture de loyer {invoice.numero_facture} créée avec succès !"
            )
            return redirect('payments:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
    else:
        form = InvoiceLoyerForm()
    
    context = {
        'form': form,
        'type_facture': 'loyer',
        'titre': 'Créer une Facture de Loyer',
        'icon': 'fa-home',
        'color': 'blue'
    }
    
    return render(request, 'payments/invoices/create_form.html', context)


@login_required
def invoice_create_syndic(request):
    """Créer une facture syndic de copropriété"""
    
    if not request.user.is_staff:
        messages.error(request, "Permission refusée.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = InvoiceSyndicForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.creee_par = request.user
            invoice.statut = 'emise'
            invoice.save()
            
            messages.success(
                request,
                f"✅ Facture syndic {invoice.numero_facture} créée avec succès !"
            )
            return redirect('payments:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
    else:
        form = InvoiceSyndicForm()
    
    context = {
        'form': form,
        'type_facture': 'syndic',
        'titre': 'Créer une Facture Syndic',
        'icon': 'fa-building',
        'color': 'purple'
    }
    
    return render(request, 'payments/invoices/create_form.html', context)


@login_required
def invoice_create_achat(request):
    """Créer une facture de demande d'achat"""
    
    if not request.user.is_staff:
        messages.error(request, "Permission refusée.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = InvoiceDemandeAchatForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.creee_par = request.user
            invoice.statut = 'emise'
            invoice.save()
            
            messages.success(
                request,
                f"✅ Facture d'achat {invoice.numero_facture} créée avec succès !"
            )
            return redirect('payments:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
    else:
        form = InvoiceDemandeAchatForm()
    
    context = {
        'form': form,
        'type_facture': 'demande_achat',
        'titre': 'Créer une Demande d\'Achat',
        'icon': 'fa-shopping-cart',
        'color': 'green'
    }
    
    return render(request, 'payments/invoices/create_form.html', context)


@login_required
def invoice_create_prestataire(request):
    """Créer une facture prestataire"""
    
    if not request.user.is_staff:
        messages.error(request, "Permission refusée.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = InvoicePrestataireForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.creee_par = request.user
            invoice.statut = 'emise'
            invoice.save()
            
            messages.success(
                request,
                f"✅ Facture prestataire {invoice.numero_facture} créée avec succès !"
            )
            return redirect('payments:invoice_detail', pk=invoice.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs.")
    else:
        form = InvoicePrestataireForm()
    
    context = {
        'form': form,
        'type_facture': 'prestataire',
        'titre': 'Créer une Facture Prestataire',
        'icon': 'fa-tools',
        'color': 'orange'
    }
    
    return render(request, 'payments/invoices/create_form.html', context)


# ==================== RENOMMAGE DE DOCUMENTS ====================

@login_required
@require_http_methods(["GET", "POST"])
def rename_invoice_pdf(request, pk):
    """Renommer le fichier PDF d'une facture"""
    
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Vérification des permissions
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)
    
    if request.method == 'POST':
        form = RenameDocumentForm(request.POST)
        if form.is_valid():
            nouveau_nom = form.cleaned_data['nouveau_nom']
            
            # Mettre à jour le nom personnalisé
            invoice.fichier_pdf_nom = nouveau_nom
            invoice.save()
            
            messages.success(
                request,
                f"✅ Le nom du fichier a été changé en '{nouveau_nom}'"
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f"Le nom du fichier a été changé en '{nouveau_nom}'",
                    'nouveau_nom': nouveau_nom
                })
            else:
                return redirect('payments:invoice_detail', pk=pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = RenameDocumentForm(initial={
            'nouveau_nom': invoice.fichier_pdf_nom or f"Facture_{invoice.numero_facture}"
        })
    
    context = {
        'form': form,
        'invoice': invoice
    }
    
    return render(request, 'payments/invoices/rename_pdf.html', context)


@login_required
@require_http_methods(["POST"])
def rename_document_ajax(request):
    """Renommer un document via AJAX (générique)"""
    
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        
        document_type = data.get('document_type')  # 'invoice', 'contract', 'expense', etc.
        document_id = data.get('document_id')
        nouveau_nom = data.get('nouveau_nom', '').strip()
        
        if not all([document_type, document_id, nouveau_nom]):
            return JsonResponse({
                'success': False,
                'error': 'Données manquantes'
            }, status=400)
        
        # Nettoyer le nom
        nouveau_nom = nouveau_nom.replace(' ', '_')
        caracteres_autorises = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        nouveau_nom = ''.join(c for c in nouveau_nom if c in caracteres_autorises)
        
        # Selon le type de document
        if document_type == 'invoice':
            invoice = get_object_or_404(Invoice, pk=document_id)
            invoice.fichier_pdf_nom = nouveau_nom
            invoice.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Nom du fichier changé en '{nouveau_nom}'",
                'nouveau_nom': nouveau_nom
            })
        
        else:
            return JsonResponse({
                'success': False,
                'error': 'Type de document non supporté'
            }, status=400)
    
    except Exception as e:
        logger.error(f"Erreur renommage document: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== GÉNÉRATION PDF SELON TYPE ====================

@login_required
def generate_invoice_pdf_custom(request, pk):
    """Génère le PDF de la facture selon son type (téléchargement)"""

    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user',
            'creee_par'
        ),
        pk=pk
    )

    # Vérification des permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if invoice.contrat and invoice.contrat.locataire.user != request.user:
                messages.error(request, "Permission refusée.")
                return redirect('dashboard:index')
        else:
            messages.error(request, "Permission refusée.")
            return redirect('dashboard:index')

    try:
        # Importer la fonction de génération appropriée selon le type
        if invoice.type_facture == 'loyer':
            from .pdf_generators import generate_invoice_loyer_pdf
            pdf_data = generate_invoice_loyer_pdf(invoice)
        elif invoice.type_facture == 'syndic':
            from .pdf_generators import generate_invoice_syndic_pdf
            pdf_data = generate_invoice_syndic_pdf(invoice)
        elif invoice.type_facture == 'demande_achat':
            from .pdf_generators import generate_invoice_achat_pdf
            pdf_data = generate_invoice_achat_pdf(invoice)
        elif invoice.type_facture == 'prestataire':
            from .pdf_generators import generate_invoice_prestataire_pdf
            pdf_data = generate_invoice_prestataire_pdf(invoice)
        else:
            # Utiliser le générateur par défaut
            from .pdf_generators import generate_invoice_default_pdf
            pdf_data = generate_invoice_default_pdf(invoice)

        # Nom du fichier - utiliser le nom personnalisé si défini
        if invoice.fichier_pdf_nom:
            filename = f"{invoice.fichier_pdf_nom}.pdf"
        else:
            filename = f"facture_{invoice.numero_facture}.pdf"

        # Retourner la réponse en téléchargement
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        logger.info(f"PDF facture {invoice.numero_facture} généré avec succès (nom: {filename})")
        return response

    except Exception as e:
        logger.error(f"Erreur génération PDF facture: {str(e)}")
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('payments:invoice_detail', pk=pk)


@login_required
def invoice_preview_pdf(request, pk):
    """Affiche l'aperçu du PDF de la facture dans le navigateur"""

    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user',
            'creee_par'
        ),
        pk=pk
    )

    # Vérification des permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if invoice.contrat and invoice.contrat.locataire.user != request.user:
                messages.error(request, "Permission refusée.")
                return redirect('dashboard:index')
        else:
            messages.error(request, "Permission refusée.")
            return redirect('dashboard:index')

    try:
        # Importer la fonction de génération appropriée selon le type
        if invoice.type_facture == 'loyer':
            from .pdf_generators import generate_invoice_loyer_pdf
            pdf_data = generate_invoice_loyer_pdf(invoice)
        elif invoice.type_facture == 'syndic':
            from .pdf_generators import generate_invoice_syndic_pdf
            pdf_data = generate_invoice_syndic_pdf(invoice)
        elif invoice.type_facture == 'demande_achat':
            from .pdf_generators import generate_invoice_achat_pdf
            pdf_data = generate_invoice_achat_pdf(invoice)
        elif invoice.type_facture == 'prestataire':
            from .pdf_generators import generate_invoice_prestataire_pdf
            pdf_data = generate_invoice_prestataire_pdf(invoice)
        else:
            # Utiliser le générateur par défaut
            from .pdf_generators import generate_invoice_default_pdf
            pdf_data = generate_invoice_default_pdf(invoice)

        # Nom du fichier - utiliser le nom personnalisé si défini
        if invoice.fichier_pdf_nom:
            filename = f"{invoice.fichier_pdf_nom}.pdf"
        else:
            filename = f"facture_{invoice.numero_facture}.pdf"

        # Retourner la réponse en aperçu (inline)
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'

        logger.info(f"Aperçu PDF facture {invoice.numero_facture} affiché (nom: {filename})")
        return response

    except Exception as e:
        logger.error(f"Erreur aperçu PDF facture: {str(e)}")
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('payments:invoice_detail', pk=pk)