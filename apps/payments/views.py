# apps/payments/views.py
from django.http import HttpResponse
from django.urls import reverse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models.invoice import Invoice
from .models.payment import Payment, PaymentReminder
from .utils import generate_payment_receipt_pdf, generate_payment_receipt_filename
from .forms import PaymentForm, QuickPaymentForm

logger = logging.getLogger(__name__)


@login_required
def payment_create_view(request):
    """
    Vue pour créer un nouveau paiement
    """
    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.statut = 'en_attente'  # Par défaut en attente
            payment.save()
            
            messages.success(
                request,
                f"Paiement {payment.numero_paiement} enregistré avec succès. "
                f"Il doit être validé par un administrateur."
            )
            return redirect('payments:detail', pk=payment.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs en rouge.")
    else:
        form = PaymentForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Enregistrer un nouveau paiement',
    }
    
    return render(request, 'payments/create.html', context)


@login_required
@require_http_methods(["POST"])
def quick_payment_create(request):
    """
    API pour créer rapidement un paiement depuis une facture
    """
    form = QuickPaymentForm(request.POST)
    
    if form.is_valid():
        try:
            facture = Invoice.objects.get(pk=form.cleaned_data['facture_id'])
            
            # Créer le paiement
            payment = Payment.objects.create(
                facture=facture,
                montant=form.cleaned_data['montant'],
                date_paiement=form.cleaned_data['date_paiement'],
                moyen_paiement=form.cleaned_data['moyen_paiement'],
                reference_transaction=form.cleaned_data.get('reference_transaction', ''),
                statut='en_attente'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Paiement {payment.numero_paiement} enregistré avec succès',
                'payment_id': payment.pk,
                'payment_url': reverse('payments:detail', kwargs={'pk': payment.pk})
            })
            
        except Invoice.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Facture non trouvée'
            }, status=404)
        except Exception as e:
            logger.error(f"Erreur création paiement rapide: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def payments_list_view(request):
    """
    Vue liste des paiements avec filtres et pagination
    """
    # Récupérer tous les paiements avec les relations
    payments = Payment.objects.select_related(
        'facture__contrat__appartement__residence',
        'facture__contrat__locataire__user',
        'valide_par'  # ✅
    ).order_by('-date_paiement')
    
    # Filtres
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    moyen_paiement = request.GET.get('moyen_paiement', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    if search:
        payments = payments.filter(
            Q(numero_paiement__icontains=search) |
            Q(facture__numero_facture__icontains=search) |
            Q(facture__contrat__locataire__user__first_name__icontains=search) |
            Q(facture__contrat__locataire__user__last_name__icontains=search) |
            Q(reference_transaction__icontains=search)
        )
    
    if statut:
        payments = payments.filter(statut=statut)
    
    if moyen_paiement:
        payments = payments.filter(moyen_paiement=moyen_paiement)
    
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            payments = payments.filter(date_paiement__gte=date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            payments = payments.filter(date_paiement__lte=date_fin_obj)
        except ValueError:
            pass
    
    # Permissions selon le type d'utilisateur
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            payments = payments.filter(facture__contrat__locataire__user=request.user)
        elif hasattr(request.user, 'proprietaire'):
            payments = payments.filter(facture__contrat__appartement__residence__proprietaire__user=request.user)
        else:
            payments = payments.none()
    
    # Statistiques
    total_payments = payments.count()
    total_amount = payments.filter(statut='valide').aggregate(Sum('montant'))['montant__sum'] or 0
    
    stats = {
        'total': total_payments,
        'valide': payments.filter(statut='valide').count(),
        'en_attente': payments.filter(statut='en_attente').count(),
        'refuse': payments.filter(statut='refuse').count(),
        'total_amount': total_amount,
    }
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'payments': page_obj,
        'search': search,
        'statut': statut,
        'moyen_paiement': moyen_paiement,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'statut_choices': Payment._meta.get_field('statut').choices,
        'moyen_paiement_choices': Payment._meta.get_field('moyen_paiement').choices,
        'stats': stats,
    }
    
    return render(request, 'payments/list.html', context)


@login_required
def payment_detail_view(request, pk):
    """
    Vue détail d'un paiement
    """
    payment = get_object_or_404(
        Payment.objects.select_related(
            'facture__contrat__appartement__residence',
            'facture__contrat__locataire__user',
            'valide_par'  # ✅
        ),
        pk=pk
    )
    
    # Vérification des permissions
    can_edit = False
    if request.user.is_staff:
        can_edit = True
    elif hasattr(request.user, 'locataire') and payment.facture.contrat.locataire.user == request.user:
        can_edit = False  # Les locataires ne peuvent que consulter
    elif hasattr(request.user, 'proprietaire') and payment.facture.contrat.appartement.residence.proprietaire.user == request.user:
        can_edit = False  # Les propriétaires ne peuvent que consulter
    else:
        raise Http404("Paiement non trouvé")
    
    context = {
        'payment': payment,
        'can_edit': can_edit,
    }
    
    return render(request, 'payments/detail.html', context)


@login_required
def payment_receipt_download(request, pk):
    """
    Télécharge la quittance de paiement en PDF
    """
    payment = get_object_or_404(
        Payment.objects.select_related(
            'facture__contrat__appartement__residence__proprietaire',
            'facture__contrat__locataire'
        ),
        pk=pk
    )

    # Vérifier que la facture a un contrat (nécessaire pour les quittances)
    if not payment.facture or not payment.facture.contrat:
        messages.error(request, "Cette facture n'est pas liée à un contrat. Impossible de générer une quittance.")
        return redirect('payments:detail', pk=pk)

    # Vérification des permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if payment.facture.contrat.locataire != request.user.locataire:
                raise Http404("Paiement non trouvé")
        elif hasattr(request.user, 'proprietaire'):
            if payment.facture.contrat.appartement.residence.proprietaire != request.user.proprietaire:
                raise Http404("Paiement non trouvé")
        else:
            raise Http404("Paiement non trouvé")

    # Vérifier que le paiement est validé
    if payment.statut != 'valide':
        messages.warning(request, "La quittance n'est disponible que pour les paiements validés.")
        return redirect('payments:detail', pk=pk)
    
    try:
        # Générer le PDF
        pdf = generate_payment_receipt_pdf(payment)
        filename = generate_payment_receipt_filename(payment)
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"Quittance générée pour le paiement {payment.numero_paiement}")
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la quittance: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la génération de la quittance.")
        return redirect('payments:detail', pk=pk)


@login_required
def payment_receipt_preview(request, pk):
    """
    Affiche un aperçu de la quittance dans le navigateur
    """
    payment = get_object_or_404(
        Payment.objects.select_related(
            'facture__contrat__appartement__residence__proprietaire',
            'facture__contrat__locataire'
        ),
        pk=pk
    )

    # Vérifier que la facture a un contrat (nécessaire pour les quittances)
    if not payment.facture or not payment.facture.contrat:
        messages.error(request, "Cette facture n'est pas liée à un contrat. Impossible de générer une quittance.")
        return redirect('payments:detail', pk=pk)

    # Vérification des permissions (même logique que download)
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if payment.facture.contrat.locataire != request.user.locataire:
                raise Http404("Paiement non trouvé")
        elif hasattr(request.user, 'proprietaire'):
            if payment.facture.contrat.appartement.residence.proprietaire != request.user.proprietaire:
                raise Http404("Paiement non trouvé")
        else:
            raise Http404("Paiement non trouvé")

    if payment.statut != 'valide':
        messages.warning(request, "La quittance n'est disponible que pour les paiements validés.")
        return redirect('payments:detail', pk=pk)
    
    try:
        # Générer le PDF
        pdf = generate_payment_receipt_pdf(payment)
        
        # Créer la réponse HTTP pour affichage inline
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline'
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'aperçu: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la génération de l'aperçu.")
        return redirect('payments:detail', pk=pk)


@login_required
def invoices_list_view(request):
    """
    Vue liste des factures avec filtres et pagination
    """
    # Récupérer toutes les factures avec les relations
    invoices = Invoice.objects.select_related(
        'contrat__appartement__residence',
        'contrat__locataire__user'
    ).prefetch_related('paiements').order_by('-date_emission')
    
    # Filtres
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    type_facture = request.GET.get('type_facture', '')
    
    if search:
        invoices = invoices.filter(
            Q(numero_facture__icontains=search) |
            Q(contrat__numero_contrat__icontains=search) |
            Q(contrat__locataire__user__first_name__icontains=search) |
            Q(contrat__locataire__user__last_name__icontains=search)
        )
    
    if statut:
        invoices = invoices.filter(statut=statut)
    
    if type_facture:
        invoices = invoices.filter(type_facture=type_facture)
    
    # Permissions selon le type d'utilisateur
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            invoices = invoices.filter(contrat__locataire__user=request.user)
        elif hasattr(request.user, 'proprietaire'):
            invoices = invoices.filter(contrat__appartement__residence__proprietaire__user=request.user)
        else:
            invoices = invoices.none()
    
    # Statistiques
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(Sum('montant_ttc'))['montant_ttc__sum'] or 0
    
    stats = {
        'total': total_invoices,
        'emise': invoices.filter(statut='emise').count(),
        'payee': invoices.filter(statut='payee').count(),
        'en_retard': invoices.filter(statut='en_retard').count(),
        'total_amount': total_amount,
    }
    
    # Pagination
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'invoices': page_obj,
        'search': search,
        'statut': statut,
        'type_facture': type_facture,
        'statut_choices': Invoice._meta.get_field('statut').choices,
        'type_facture_choices': Invoice._meta.get_field('type_facture').choices,
        'stats': stats,
    }
    
    return render(request, 'payments/invoices_list.html', context)


@login_required
def invoice_detail_view(request, pk):
    """
    Vue détail d'une facture
    """
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user'
        ).prefetch_related('paiements', 'lignes_achat'),
        pk=pk
    )

    # Vérification des permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if invoice.contrat and invoice.contrat.locataire.user != request.user:
                raise Http404("Facture non trouvée")
        elif hasattr(request.user, 'proprietaire'):
            if invoice.contrat and invoice.contrat.appartement.residence.proprietaire.user != request.user:
                raise Http404("Facture non trouvée")
        else:
            raise Http404("Facture non trouvée")

    context = {
        'invoice': invoice,
        'payments': invoice.paiements.all().order_by('-date_paiement'),
        'lignes_achat': invoice.lignes_achat.all() if invoice.type_facture == 'demande_achat' else None,
    }

    return render(request, 'payments/invoice_detail.html', context)


# ============ API ENDPOINTS ============

@login_required
@require_http_methods(["POST"])
def validate_payment_api(request, pk):
    """
    API pour valider un paiement
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    payment = get_object_or_404(Payment, pk=pk)
    
    if payment.statut != 'en_attente':
        return JsonResponse({
            'error': 'Seuls les paiements en attente peuvent être validés'
        }, status=400)
    
    try:
        payment.validate_payment(request.user)
        return JsonResponse({
            'success': True,
            'message': f'Paiement {payment.numero_paiement} validé avec succès',
            'statut': payment.get_statut_display()
        })
    except Exception as e:
        logger.error(f"Erreur validation paiement: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def payment_stats_api(request):
    """
    API pour récupérer les statistiques des paiements
    """
    # Filtres de date
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    payments = Payment.objects.all()
    
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            payments = payments.filter(date_paiement__gte=date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            payments = payments.filter(date_paiement__lte=date_fin_obj)
        except ValueError:
            pass
    
    # Permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            payments = payments.filter(facture__contrat__locataire__user=request.user)
        elif hasattr(request.user, 'proprietaire'):
            payments = payments.filter(facture__contrat__appartement__residence__proprietaire__user=request.user)
        else:
            payments = payments.none()
    
    # Calculs
    total_valide = payments.filter(statut='valide').aggregate(Sum('montant'))['montant__sum'] or 0
    total_en_attente = payments.filter(statut='en_attente').aggregate(Sum('montant'))['montant__sum'] or 0
    
    # Répartition par moyen de paiement
    by_method = {}
    for choice in Payment._meta.get_field('moyen_paiement').choices:
        method = choice[0]
        count = payments.filter(moyen_paiement=method, statut='valide').count()
        amount = payments.filter(moyen_paiement=method, statut='valide').aggregate(Sum('montant'))['montant__sum'] or 0
        by_method[method] = {
            'label': choice[1],
            'count': count,
            'amount': float(amount)
        }
    
    data = {
        'total_payments': payments.count(),
        'total_valide': float(total_valide),
        'total_en_attente': float(total_en_attente),
        'count_valide': payments.filter(statut='valide').count(),
        'count_en_attente': payments.filter(statut='en_attente').count(),
        'count_refuse': payments.filter(statut='refuse').count(),
        'by_method': by_method,
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def get_invoice_info_api(request, pk):
    """
    API pour récupérer les informations d'une facture
    """
    try:
        invoice = Invoice.objects.select_related(
            'contrat__locataire__user',
            'contrat__appartement__residence'
        ).get(pk=pk)
        
        # Vérifier les permissions
        if not request.user.is_staff:
            if hasattr(request.user, 'locataire'):
                if invoice.contrat.locataire.user != request.user:
                    return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
            else:
                return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
        
        data = {
            'success': True,
            'locataire': invoice.contrat.locataire.nom_complet,
            'bien': f"{invoice.contrat.appartement.nom} - {invoice.contrat.appartement.residence.nom}",
            'montant_total': f"{invoice.montant_ttc:,.0f} FCFA",
            'montant_total_raw': float(invoice.montant_ttc),
            'reste_a_payer': f"{invoice.solde_restant:,.0f} FCFA",
            'reste_a_payer_raw': float(invoice.solde_restant),
            'montant_paye': f"{invoice.montant_paye:,.0f} FCFA",
            'statut': invoice.get_statut_display(),
        }
        
        return JsonResponse(data)
        
    except Invoice.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Facture non trouvée'
        }, status=404)
    

@login_required
def invoice_download_pdf(request, pk):
    """Télécharger le PDF de la facture"""
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user'
        ),
        pk=pk
    )
    
    # Vérification des permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if invoice.contrat and invoice.contrat.locataire.user != request.user:
                raise Http404("Facture non trouvée")
        elif hasattr(request.user, 'proprietaire'):
            if invoice.contrat and invoice.contrat.appartement.residence.proprietaire.user != request.user:
                raise Http404("Facture non trouvée")
        else:
            raise Http404("Facture non trouvée")
    
    try:
        # Créer le PDF en mémoire
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Titre
        elements.append(Paragraph("FACTURE", title_style))
        elements.append(Spacer(1, 20))
        
        # Informations de la facture
        elements.append(Paragraph("INFORMATIONS DE LA FACTURE", heading_style))
        
        info_data = [
            ["Numéro:", invoice.numero_facture],
            ["Type:", invoice.get_type_facture_display()],
            ["Date d'émission:", invoice.date_emission.strftime("%d/%m/%Y") if invoice.date_emission else "Non émise"],
            ["Date d'échéance:", invoice.date_echeance.strftime("%d/%m/%Y")],
            ["Statut:", invoice.get_statut_display()],
        ]
        
        if invoice.periode_debut and invoice.periode_fin:
            info_data.append(["Période:", f"Du {invoice.periode_debut.strftime('%d/%m/%Y')} au {invoice.periode_fin.strftime('%d/%m/%Y')}"])
        
        info_table = Table(info_data, colWidths=[50*mm, 80*mm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))
        
        # Informations du client (contrat ou manuel)
        if invoice.contrat:
            # Avec contrat
            elements.append(Paragraph("LOCATAIRE", heading_style))
            
            # Récupérer le téléphone de manière sécurisée
            telephone = "Non renseigné"
            if hasattr(invoice.contrat.locataire, 'telephone') and invoice.contrat.locataire.telephone:
                telephone = invoice.contrat.locataire.telephone
            
            locataire_data = [
                ["Nom:", invoice.contrat.locataire.nom_complet],
                ["Email:", invoice.contrat.locataire.email or "Non renseigné"],
                ["Téléphone:", telephone],
            ]
            
            locataire_table = Table(locataire_data, colWidths=[50*mm, 80*mm])
            locataire_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(locataire_table)
            elements.append(Spacer(1, 15))
            
            # Informations du bien
            elements.append(Paragraph("BIEN CONCERNÉ", heading_style))
            
            bien_data = [
                ["Résidence:", invoice.contrat.appartement.residence.nom],
                ["Appartement:", invoice.contrat.appartement.nom],
                ["Adresse:", f"{invoice.contrat.appartement.residence.adresse}, {invoice.contrat.appartement.residence.ville}"],
            ]
            
            bien_table = Table(bien_data, colWidths=[50*mm, 80*mm])
            bien_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(bien_table)
            elements.append(Spacer(1, 15))
        else:
            # Facture manuelle
            elements.append(Paragraph("CLIENT", heading_style))
            
            client_data = [
                ["Nom:", invoice.destinataire_nom or "Non renseigné"],
                ["Email:", invoice.destinataire_email or "Non renseigné"],
                ["Téléphone:", invoice.destinataire_telephone or "Non renseigné"],
            ]
            
            if invoice.destinataire_adresse:
                client_data.append(["Adresse:", invoice.destinataire_adresse])
            
            client_table = Table(client_data, colWidths=[50*mm, 80*mm])
            client_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(client_table)
            elements.append(Spacer(1, 15))
        
        # Détails financiers
        elements.append(Paragraph("DÉTAILS FINANCIERS", heading_style))
        
        montant_ht = float(invoice.montant_ht)
        montant_ttc = float(invoice.montant_ttc)
        tva = montant_ttc - montant_ht
        
        finance_data = [
            ["Montant HT:", f"{montant_ht:,.0f} FCFA"],
            ["TVA ({:.1f}%):".format(float(invoice.taux_tva)), f"{tva:,.0f} FCFA"],
            ["Montant TTC:", f"{montant_ttc:,.0f} FCFA"],
        ]
        
        # Ajouter les paiements
        montant_paye = float(invoice.montant_paye)
        solde_restant = float(invoice.solde_restant)
        
        if montant_paye > 0:
            finance_data.extend([
                ["Montant payé:", f"{montant_paye:,.0f} FCFA"],
                ["Reste à payer:", f"{solde_restant:,.0f} FCFA"],
            ])
        
        finance_table = Table(finance_data, colWidths=[50*mm, 80*mm])
        finance_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#e5e7eb')),
        ]))
        elements.append(finance_table)
        
        # Description si présente
        if invoice.description:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("DESCRIPTION", heading_style))
            elements.append(Paragraph(invoice.description, styles['Normal']))
        
        # Générer le PDF
        doc.build(elements)
        
        # Retourner la réponse avec nom personnalisé si défini
        buffer.seek(0)
        
        # Utiliser le nom personnalisé si défini, sinon le numéro de facture
        if invoice.fichier_pdf_nom:
            filename = f"{invoice.fichier_pdf_nom}.pdf"
        else:
            filename = f"facture_{invoice.numero_facture}.pdf"
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF facture {invoice.numero_facture} généré avec succès")
        return response
        
    except Exception as e:
        logger.error(f"Erreur génération PDF facture: {str(e)}")
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('payments:invoice_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def invoice_send_email(request, pk):
    """Envoyer la facture par email"""
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user'
        ),
        pk=pk
    )
    
    # Vérification des permissions
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
    
    try:
        from django.core.mail import EmailMessage
        
        # Email du locataire
        email_to = invoice.contrat.locataire.email
        
        if not email_to:
            return JsonResponse({'success': False, 'error': 'Le locataire n\'a pas d\'email renseigné'})
        
        # Sujet et message
        subject = f"Facture {invoice.numero_facture} - Seyni Properties"
        message = f"""Bonjour {invoice.contrat.locataire.nom_complet},

Veuillez trouver ci-joint votre facture n°{invoice.numero_facture}.

Détails:
- Montant: {invoice.montant_ttc:,.0f} FCFA
- Date d'échéance: {invoice.date_echeance.strftime('%d/%m/%Y')}
- Montant restant: {invoice.amount_remaining:,.0f} FCFA

Cordialement,
Seyni Properties
"""
        
        # Créer l'email
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email='noreply@seyniproperties.com',
            to=[email_to],
        )
        
        # Générer le PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        # ... (utiliser le même code de génération PDF que ci-dessus)
        
        # Attacher le PDF
        email.attach(f'facture_{invoice.numero_facture}.pdf', buffer.getvalue(), 'application/pdf')
        email.send()
        
        logger.info(f"Facture {invoice.numero_facture} envoyée par email à {email_to}")
        
        return JsonResponse({
            'success': True,
            'message': f'Facture envoyée avec succès à {email_to}'
        })
        
    except Exception as e:
        logger.error(f"Erreur envoi email facture: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de l\'envoi: {str(e)}'
        })


# ============================================================================
# MODULE 8 : GÉNÉRATION DOCUMENTS POUR PROPRIÉTAIRE
# ============================================================================

@login_required
def etat_loyer_preview(request, pk):
    """Affiche un aperçu de l'état de loyer dans le navigateur"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Vérifications
    if invoice.type_facture != 'loyer' or not invoice.contrat:
        messages.error(request, "Seules les factures de loyer avec contrat peuvent générer un état de loyer.")
        return redirect('payments:invoices_list')

    if invoice.statut != 'payee':
        messages.error(request, "La facture doit être payée pour générer l'état de loyer.")
        return redirect('payments:invoice_detail', pk=invoice.pk)

    try:
        from .utils import generate_etat_loyer_pdf

        # Générer le PDF
        pdf = generate_etat_loyer_pdf(invoice)

        # Retourner le PDF pour visualisation inline
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="etat_loyer_preview.pdf"'

        logger.info(f"Aperçu de l'état de loyer généré pour la facture {invoice.numero_facture}")
        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'aperçu de l'état de loyer: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la génération de l'aperçu de l'état de loyer.")
        return redirect('payments:invoice_detail', pk=pk)


@login_required
def generer_quittance(request, pk):
    """
    Génère la quittance de loyer pour le locataire (document PDF)
    """
    invoice = get_object_or_404(Invoice, pk=pk)

    # Vérifications
    if invoice.type_facture != 'loyer' or not invoice.contrat:
        messages.error(request, "Seules les factures de loyer avec contrat peuvent générer une quittance.")
        return redirect('payments:invoices_list')

    if invoice.statut != 'payee':
        messages.error(request, "La facture doit être payée pour générer la quittance.")
        return redirect('payments:invoice_detail', pk=invoice.pk)

    context = {
        'invoice': invoice,
        'contrat': invoice.contrat,
        'locataire': invoice.contrat.locataire,
        'appartement': invoice.contrat.appartement,
        'residence': invoice.contrat.appartement.residence,
        'date_generation': timezone.now(),
    }

    # Marquer comme généré
    invoice.quittance_generee = True
    invoice.date_generation_quittance = timezone.now()
    invoice.save(update_fields=['quittance_generee', 'date_generation_quittance'])

    # Render le template HTML
    return render(request, 'payments/quittance.html', context)


@login_required
@require_http_methods(["POST"])
def envoyer_rappel_paiement(request, pk):
    """
    Envoie un rappel de paiement pour une facture en retard
    """
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.statut not in ['emise', 'en_retard']:
        return JsonResponse({
            'success': False,
            'error': 'Cette facture ne nécessite pas de rappel'
        }, status=400)

    # Créer un rappel
    from .models.payment import PaymentReminder

    locataire = invoice.contrat.locataire if invoice.contrat else None
    if not locataire or not locataire.email:
        return JsonResponse({
            'success': False,
            'error': 'Aucun email disponible pour le locataire'
        }, status=400)

    message = f"""
    Bonjour {locataire.nom_complet},

    Nous vous informons que votre facture {invoice.numero_facture}
    d'un montant de {invoice.montant_ttc} FCFA est en attente de paiement.

    Date d'échéance : {invoice.date_echeance.strftime('%d/%m/%Y')}

    Merci de régulariser votre situation dans les plus brefs délais.

    Cordialement,
    L'équipe Seyni Properties
    """

    rappel = PaymentReminder.objects.create(
        facture=invoice,
        type_rappel='manuel',
        moyen_envoi='email',
        message=message,
        statut='envoye'
    )

    # Mettre à jour les compteurs
    invoice.date_derniere_relance = timezone.now()
    invoice.nombre_relances += 1
    invoice.statut = 'en_retard'
    invoice.save(update_fields=['date_derniere_relance', 'nombre_relances', 'statut'])

    return JsonResponse({
        'success': True,
        'message': f'Rappel envoyé à {locataire.email}',
        'nombre_relances': invoice.nombre_relances
    })


# ============================================================================
# NOUVELLES VUES POUR GÉNÉRATION PDF
# ============================================================================

@login_required
def etat_loyer_download(request, pk):
    """Télécharge l'état de loyer en PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Vérifications
    if invoice.type_facture != 'loyer' or not invoice.contrat:
        messages.error(request, "Seules les factures de loyer avec contrat peuvent générer un état de loyer.")
        return redirect('payments:invoices_list')

    if invoice.statut != 'payee':
        messages.error(request, "La facture doit être payée pour générer l'état de loyer.")
        return redirect('payments:invoice_detail', pk=invoice.pk)

    try:
        from .utils import generate_etat_loyer_pdf, generate_etat_loyer_filename

        # Générer le PDF
        pdf = generate_etat_loyer_pdf(invoice)
        filename = generate_etat_loyer_filename(invoice)

        # Marquer comme généré
        invoice.etat_loyer_genere = True
        invoice.date_generation_etat_loyer = timezone.now()
        invoice.save(update_fields=['etat_loyer_genere', 'date_generation_etat_loyer'])

        # Retourner le PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        logger.info(f"État de loyer généré pour la facture {invoice.numero_facture}")
        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'état de loyer: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la génération de l'état de loyer.")
        return redirect('payments:invoice_detail', pk=pk)


@login_required
def quittance_preview(request, pk):
    """Affiche un aperçu de la quittance dans le navigateur"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Vérifications
    if invoice.type_facture != 'loyer' or not invoice.contrat:
        messages.error(request, "Seules les factures de loyer avec contrat peuvent générer une quittance.")
        return redirect('payments:invoices_list')

    if invoice.statut != 'payee':
        messages.error(request, "La facture doit être payée pour générer la quittance.")
        return redirect('payments:invoice_detail', pk=invoice.pk)

    try:
        from .utils import generate_invoice_quittance_pdf

        # Générer le PDF
        pdf = generate_invoice_quittance_pdf(invoice)

        # Retourner pour affichage inline
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline'

        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'aperçu de la quittance: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la génération de l'aperçu.")
        return redirect('payments:invoice_detail', pk=pk)


@login_required
def quittance_download(request, pk):
    """Télécharge la quittance en PDF"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # Vérifications
    if invoice.type_facture != 'loyer' or not invoice.contrat:
        messages.error(request, "Seules les factures de loyer avec contrat peuvent générer une quittance.")
        return redirect('payments:invoices_list')

    if invoice.statut != 'payee':
        messages.error(request, "La facture doit être payée pour générer la quittance.")
        return redirect('payments:invoice_detail', pk=invoice.pk)

    try:
        from .utils import generate_invoice_quittance_pdf, generate_invoice_quittance_filename

        # Générer le PDF
        pdf = generate_invoice_quittance_pdf(invoice)
        filename = generate_invoice_quittance_filename(invoice)

        # Marquer comme généré
        invoice.quittance_generee = True
        invoice.date_generation_quittance = timezone.now()
        invoice.save(update_fields=['quittance_generee', 'date_generation_quittance'])

        # Retourner le PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        logger.info(f"Quittance générée pour la facture {invoice.numero_facture}")
        return response

    except Exception as e:
        logger.error(f"Erreur lors de la génération de la quittance: {str(e)}")
        messages.error(request, "Une erreur s'est produite lors de la génération de la quittance.")
        return redirect('payments:invoice_detail', pk=pk)