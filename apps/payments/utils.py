# apps/payments/utils.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from django.conf import settings
from io import BytesIO
from decimal import Decimal
import os
import requests
import tempfile
from django.utils import timezone


def generate_payment_receipt_pdf(payment):
    """
    Génère une quittance de paiement en PDF

    Args:
        payment: Instance du modèle Payment

    Returns:
        BytesIO contenant le PDF généré
    """
    buffer = BytesIO()

    # URL publique du logo IMANY sur Google Drive
    LOGO_URL = "https://drive.usercontent.google.com/uc?id=13cv-A6HhhJTCtMIyqbaUhjpg1X_t9zpl&export=download"

    # Télécharger le logo depuis Google Drive
    logo_temp_path = None
    try:
        response = requests.get(LOGO_URL, timeout=10)
        if response.status_code == 200:
            # Créer un fichier temporaire pour le logo
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                logo_temp_path = tmp_file.name
    except Exception as e:
        print(f"Erreur téléchargement logo: {e}")
        logo_temp_path = None

    # Fonction pour ajouter en-tête et pied de page sur chaque page
    def add_header_footer(canvas_obj, doc):
        canvas_obj.saveState()

        # En-tête: Logo IMANY depuis Google Drive
        if logo_temp_path and os.path.exists(logo_temp_path):
            try:
                canvas_obj.drawImage(logo_temp_path, 20*mm, A4[1] - 20*mm, width=40*mm, height=15*mm, preserveAspectRatio=True)
            except Exception as e:
                print(f"Erreur affichage logo: {e}")
                # Fallback: texte IMANY
                canvas_obj.setFont('Helvetica-Bold', 12)
                canvas_obj.setFillColor(colors.HexColor('#23456B'))
                canvas_obj.drawString(20*mm, A4[1] - 15*mm, "IMANY")
        else:
            # Logo texte si pas d'image disponible
            canvas_obj.setFont('Helvetica-Bold', 12)
            canvas_obj.setFillColor(colors.HexColor('#23456B'))
            canvas_obj.drawString(20*mm, A4[1] - 15*mm, "IMANY")

        # Pied de page sur toutes les pages
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(colors.HexColor('#666666'))

        footer_line1 = "IMANY SN. NINEA /011195816/ RCCM/ SN DKR 2024 B 18099"
        footer_line2 = "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"

        # Centrer le pied de page
        footer_y = 15*mm
        canvas_obj.drawCentredString(A4[0]/2, footer_y + 3*mm, footer_line1)
        canvas_obj.drawCentredString(A4[0]/2, footer_y, footer_line2)

        canvas_obj.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=30*mm,  # Augmenté pour laisser place au logo
        bottomMargin=25*mm,  # Augmenté pour laisser place au footer
    )
    
    # Couleurs IMANY
    IMANY_BLUE = colors.HexColor('#23456B')
    IMANY_TERRACOTTA = colors.HexColor('#A25946')

    # Styles
    styles = getSampleStyleSheet()

    # Style titre - Couleur IMANY primaire
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=IMANY_BLUE,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Style sous-titre - Couleur IMANY secondaire
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=IMANY_TERRACOTTA,
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    # Style normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )

    # Style header info
    header_style = ParagraphStyle(
        'HeaderInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#475569'),
    )

    story = []

    # === TITRE === (le logo est dans l'en-tête de page)
    story.append(Paragraph("QUITTANCE DE PAIEMENT", title_style))
    story.append(Paragraph("Reçu pour paiement de loyer", subtitle_style))
    story.append(Spacer(1, 15))
    
    # === INFORMATIONS DU PAIEMENT ===
    facture = payment.facture
    contrat = facture.contrat
    locataire = contrat.locataire
    appartement = contrat.appartement
    residence = appartement.residence
    
    # Informations du locataire et du bien
    locataire_nom = locataire.nom_complet if locataire else "N/A"
    locataire_tel = locataire.telephone if hasattr(locataire, 'telephone') and locataire.telephone else "Non renseigné"
    locataire_email = locataire.email if locataire and locataire.email else "Non renseigné"

    info_data = [
        ["LOCATAIRE", "BIEN LOUÉ"],
        [
            f"{locataire_nom}\n"
            f"Téléphone: {locataire_tel}\n"
            f"Email: {locataire_email}",

            f"{appartement.nom}\n"
            f"{residence.nom}\n"
            f"{residence.adresse}, {residence.ville}"
        ]
    ]
    
    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 1), (-1, -1), 10),
        ('RIGHTPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # === DÉTAILS DU PAIEMENT ===
    story.append(Paragraph("<b>DÉTAILS DU PAIEMENT</b>", 
                          ParagraphStyle('SectionTitle', parent=normal_style, 
                                       fontSize=12, textColor=colors.HexColor('#23456b'))))
    story.append(Spacer(1, 8))
    
    # Préparer les détails du paiement
    payment_details = [
        ["Description", "Montant"],
        [f"Facture N° {facture.numero_facture}", ""],
    ]

    # Ajouter la période si disponible
    if facture.periode_debut and facture.periode_fin:
        payment_details.append([f"Période: du {facture.periode_debut.strftime('%d/%m/%Y')} au {facture.periode_fin.strftime('%d/%m/%Y')}", ""])

    payment_details.extend([
        ["", ""],
        ["Montant de la facture", f"{facture.montant_ttc:,.0f} FCFA"],
        ["Montant payé", f"{payment.montant:,.0f} FCFA"],
        ["", ""],
        ["Date de paiement", payment.date_paiement.strftime('%d/%m/%Y')],
        ["Moyen de paiement", payment.get_moyen_paiement_display()],
    ])
    
    if payment.reference_transaction:
        payment_details.append(["Référence transaction", payment.reference_transaction])
    
    payment_table = Table(payment_details, colWidths=[120*mm, 50*mm])
    payment_table.setStyle(TableStyle([
        # En-tête - Couleur IMANY primaire
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Corps du tableau
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Alignement montants
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        
        # Ligne montant payé en gras
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#dcfce7')),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (-1, 5), 11),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 25))
    
    # === MONTANT EN LETTRES ===
    montant_lettres = convert_amount_to_words(payment.montant)
    story.append(Paragraph(
        f"<b>Arrêté la présente quittance à la somme de :</b><br/>"
        f"<i>{montant_lettres} francs CFA</i>",
        ParagraphStyle('AmountWords', parent=normal_style, 
                      fontSize=11, textColor=colors.HexColor('#a25946'),
                      leftIndent=10, rightIndent=10,
                      borderWidth=1, borderColor=colors.HexColor('#d1fae5'),
                      borderPadding=10, backColor=colors.HexColor('#f0fdf4'))
    ))
    story.append(Spacer(1, 25))
    
    # === SIGNATURE ET CACHET ===
    signature_data = [
        ["", "Fait à Dakar, le " + timezone.now().strftime('%d/%m/%Y')],
        ["", ""],
        ["", "Pour IMANY"],
        ["", ""],
        ["", ""],
        ["", "Le Gestionnaire"],
    ]
    
    signature_table = Table(signature_data, colWidths=[85*mm, 85*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 20))

    # Note: Le pied de page IMANY est maintenant dans le footer automatique de chaque page
    story.append(Paragraph(
        "<i>Ce document constitue une quittance officielle de paiement. Conservez-le précieusement.</i>",
        ParagraphStyle('Footer', parent=header_style,
                      fontSize=8, textColor=colors.HexColor('#94a3b8'),
                      alignment=TA_CENTER)
    ))

    # Construction du PDF avec en-tête et pied de page sur chaque page
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    pdf = buffer.getvalue()
    buffer.close()

    # Nettoyer le fichier temporaire du logo
    if logo_temp_path and os.path.exists(logo_temp_path):
        try:
            os.unlink(logo_temp_path)
        except:
            pass  # Ignorer les erreurs de suppression

    return pdf


def convert_amount_to_words(amount):
    """
    Convertit un montant numérique en lettres (français)
    Simplifié pour les montants courants
    """
    amount = int(amount)
    
    # Unités
    units = [
        '', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
        'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 
        'dix-sept', 'dix-huit', 'dix-neuf'
    ]
    
    # Dizaines
    tens = [
        '', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante', 
        'soixante', 'quatre-vingt', 'quatre-vingt'
    ]
    
    if amount == 0:
        return "zéro"
    
    def convert_hundreds(n):
        """Convertit un nombre de 0 à 999"""
        if n == 0:
            return ""
        elif n < 20:
            return units[n]
        elif n < 100:
            if n >= 70 and n < 80:
                return f"{tens[6]}-{units[n-60]}"
            elif n >= 90:
                return f"{tens[8]}-{units[n-80]}"
            else:
                unit = n % 10
                ten = n // 10
                if unit == 0:
                    return tens[ten]
                elif unit == 1 and ten == 8:
                    return f"{tens[ten]}-un"
                else:
                    return f"{tens[ten]}-{units[unit]}"
        else:
            hundred = n // 100
            rest = n % 100
            result = ""
            if hundred == 1:
                result = "cent"
            else:
                result = f"{units[hundred]} cent"
            if rest > 0:
                if hundred > 1 and rest == 0:
                    result += "s"
                else:
                    result += f" {convert_hundreds(rest)}"
            return result
    
    # Gestion des milliers et millions
    if amount < 1000:
        return convert_hundreds(amount)
    elif amount < 1000000:
        thousands = amount // 1000
        rest = amount % 1000
        result = ""
        if thousands == 1:
            result = "mille"
        else:
            result = f"{convert_hundreds(thousands)} mille"
        if rest > 0:
            result += f" {convert_hundreds(rest)}"
        return result
    else:
        millions = amount // 1000000
        rest = amount % 1000000
        result = ""
        if millions == 1:
            result = "un million"
        else:
            result = f"{convert_hundreds(millions)} millions"
        
        if rest >= 1000:
            thousands = rest // 1000
            final_rest = rest % 1000
            if thousands > 0:
                result += f" {convert_hundreds(thousands)} mille"
            if final_rest > 0:
                result += f" {convert_hundreds(final_rest)}"
        elif rest > 0:
            result += f" {convert_hundreds(rest)}"
        
        return result


def generate_payment_receipt_filename(payment):
    """
    Génère un nom de fichier pour la quittance
    """
    facture = payment.facture
    locataire = facture.contrat.locataire
    safe_numero = payment.numero_paiement.replace('/', '_').replace(' ', '_')

    # Utiliser le nom du Tiers
    if locataire and locataire.nom:
        safe_name = locataire.nom.replace(' ', '_')
    else:
        safe_name = "locataire"

    return f"quittance_{safe_numero}_{safe_name}.pdf"


def generate_invoice_quittance_pdf(invoice):
    """
    Génère une quittance pour une facture en PDF (pour locataire)
    Utilise le même style que la quittance de paiement

    Args:
        invoice: Instance du modèle Invoice

    Returns:
        BytesIO contenant le PDF généré
    """
    buffer = BytesIO()

    # URL publique du logo IMANY sur Google Drive
    LOGO_URL = "https://drive.usercontent.google.com/uc?id=13cv-A6HhhJTCtMIyqbaUhjpg1X_t9zpl&export=download"

    # Télécharger le logo depuis Google Drive
    logo_temp_path = None
    try:
        response = requests.get(LOGO_URL, timeout=10)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                logo_temp_path = tmp_file.name
    except Exception as e:
        print(f"Erreur téléchargement logo: {e}")
        logo_temp_path = None

    # Fonction pour ajouter en-tête et pied de page sur chaque page
    def add_header_footer(canvas_obj, doc):
        canvas_obj.saveState()

        # En-tête: Logo IMANY depuis Google Drive
        if logo_temp_path and os.path.exists(logo_temp_path):
            try:
                canvas_obj.drawImage(logo_temp_path, 20*mm, A4[1] - 20*mm, width=40*mm, height=15*mm, preserveAspectRatio=True)
            except Exception as e:
                print(f"Erreur affichage logo: {e}")
                canvas_obj.setFont('Helvetica-Bold', 12)
                canvas_obj.setFillColor(colors.HexColor('#23456B'))
                canvas_obj.drawString(20*mm, A4[1] - 15*mm, "IMANY")
        else:
            canvas_obj.setFont('Helvetica-Bold', 12)
            canvas_obj.setFillColor(colors.HexColor('#23456B'))
            canvas_obj.drawString(20*mm, A4[1] - 15*mm, "IMANY")

        # Pied de page sur toutes les pages
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(colors.HexColor('#666666'))

        footer_line1 = "IMANY SN. NINEA /011195816/ RCCM/ SN DKR 2024 B 18099"
        footer_line2 = "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"

        footer_y = 15*mm
        canvas_obj.drawCentredString(A4[0]/2, footer_y + 3*mm, footer_line1)
        canvas_obj.drawCentredString(A4[0]/2, footer_y, footer_line2)

        canvas_obj.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=30*mm,  # Augmenté pour laisser place au logo
        bottomMargin=25*mm,  # Augmenté pour laisser place au footer
    )

    # Styles
    styles = getSampleStyleSheet()

    # Style titre - Couleur IMANY primaire
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#23456b'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Style sous-titre - Couleur IMANY secondaire
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#a25946'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    # Style normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )

    # Style header info
    header_style = ParagraphStyle(
        'HeaderInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#475569'),
    )

    story = []

    # === TITRE === (le logo est dans l'en-tête de page)
    story.append(Paragraph("QUITTANCE DE LOYER", title_style))
    story.append(Paragraph("Attestation de paiement", subtitle_style))
    story.append(Spacer(1, 15))

    # === INFORMATIONS ===
    contrat = invoice.contrat
    locataire = contrat.locataire if contrat else None
    appartement = contrat.appartement if contrat else None
    residence = appartement.residence if appartement else None

    # Informations du locataire et du bien
    locataire_nom = locataire.nom_complet if locataire else "N/A"
    locataire_tel = locataire.telephone if locataire and hasattr(locataire, 'telephone') and locataire.telephone else "Non renseigné"
    locataire_email = locataire.email if locataire and locataire.email else "Non renseigné"

    bien_info = "N/A"
    if appartement and residence:
        bien_info = f"{appartement.nom}\n{residence.nom}\n{residence.adresse}, {residence.ville}"

    info_data = [
        ["LOCATAIRE", "BIEN LOUÉ"],
        [
            f"{locataire_nom}\n"
            f"Téléphone: {locataire_tel}\n"
            f"Email: {locataire_email}",
            bien_info
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 1), (-1, -1), 10),
        ('RIGHTPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === DÉTAILS DE LA FACTURE ===
    story.append(Paragraph("<b>DÉTAILS DU PAIEMENT</b>",
                          ParagraphStyle('SectionTitle', parent=normal_style,
                                       fontSize=12, textColor=colors.HexColor('#23456b'))))
    story.append(Spacer(1, 8))

    # Préparer les détails
    payment_details = [
        ["Description", "Montant"],
        [f"Facture N° {invoice.numero_facture}", ""],
    ]

    # Ajouter la période si disponible
    if invoice.periode_debut and invoice.periode_fin:
        payment_details.append([f"Période: du {invoice.periode_debut.strftime('%d/%m/%Y')} au {invoice.periode_fin.strftime('%d/%m/%Y')}", ""])

    # Récupérer la date de paiement depuis les paiements liés
    last_payment = invoice.paiements.filter(statut='valide').order_by('-date_paiement').first()
    date_paiement_str = last_payment.date_paiement.strftime('%d/%m/%Y') if last_payment else "N/A"

    payment_details.extend([
        ["", ""],
        ["Montant du loyer", f"{invoice.montant_ttc:,.0f} FCFA"],
        ["", ""],
        ["Date de paiement", date_paiement_str],
        ["Statut", "PAYÉE"],
    ])

    payment_table = Table(payment_details, colWidths=[120*mm, 50*mm])
    payment_table.setStyle(TableStyle([
        # En-tête - Couleur IMANY primaire
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        # Corps du tableau
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

        # Alignement montants
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),

        # Ligne montant en gras
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#dcfce7')),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 11),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 25))

    # === MONTANT EN LETTRES ===
    montant_lettres = convert_amount_to_words(invoice.montant_ttc)
    story.append(Paragraph(
        f"<b>Arrêté la présente quittance à la somme de :</b><br/>"
        f"<i>{montant_lettres} francs CFA</i>",
        ParagraphStyle('AmountWords', parent=normal_style,
                      fontSize=11, textColor=colors.HexColor('#a25946'),
                      leftIndent=10, rightIndent=10,
                      borderWidth=1, borderColor=colors.HexColor('#d1fae5'),
                      borderPadding=10, backColor=colors.HexColor('#f0fdf4'))
    ))
    story.append(Spacer(1, 25))

    # === SIGNATURE ET CACHET ===
    signature_data = [
        ["", "Fait à Dakar, le " + timezone.now().strftime('%d/%m/%Y')],
        ["", ""],
        ["", "Pour IMANY"],
        ["", ""],
        ["", ""],
        ["", "Le Gestionnaire"],
    ]

    signature_table = Table(signature_data, colWidths=[85*mm, 85*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 20))

    # Note: Le pied de page IMANY est maintenant dans le footer automatique de chaque page
    story.append(Paragraph(
        "<i>Ce document constitue une quittance officielle de paiement. Conservez-le précieusement.</i>",
        ParagraphStyle('Footer', parent=header_style,
                      fontSize=8, textColor=colors.HexColor('#94a3b8'),
                      alignment=TA_CENTER)
    ))

    # Construction du PDF avec en-tête et pied de page sur chaque page
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    pdf = buffer.getvalue()
    buffer.close()

    # Nettoyer le fichier temporaire du logo
    if logo_temp_path and os.path.exists(logo_temp_path):
        try:
            os.unlink(logo_temp_path)
        except:
            pass  # Ignorer les erreurs de suppression

    return pdf


def generate_invoice_quittance_filename(invoice):
    """
    Génère un nom de fichier pour la quittance de facture
    """
    contrat = invoice.contrat
    locataire = contrat.locataire if contrat else None
    safe_numero = invoice.numero_facture.replace('/', '_').replace(' ', '_')

    # Utiliser le nom du Tiers
    if locataire and locataire.nom:
        safe_name = locataire.nom.replace(' ', '_')
    else:
        safe_name = "locataire"

    return f"quittance_{safe_numero}_{safe_name}.pdf"


def generate_etat_loyer_pdf(invoice):
    """
    Génère un état de loyer en PDF (pour proprietaire)
    Affiche le calcul: Loyer brut - TOM (3.6%) - Frais agence (5%) = Loyer net

    Args:
        invoice: Instance du modèle Invoice

    Returns:
        BytesIO contenant le PDF généré
    """
    buffer = BytesIO()

    # URL publique du logo IMANY sur Google Drive
    LOGO_URL = "https://drive.usercontent.google.com/uc?id=13cv-A6HhhJTCtMIyqbaUhjpg1X_t9zpl&export=download"

    # Télécharger le logo depuis Google Drive
    logo_temp_path = None
    try:
        response = requests.get(LOGO_URL, timeout=10)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                logo_temp_path = tmp_file.name
    except Exception as e:
        print(f"Erreur téléchargement logo: {e}")
        logo_temp_path = None

    # Fonction pour ajouter en-tête et pied de page sur chaque page
    def add_header_footer(canvas_obj, doc):
        canvas_obj.saveState()

        # En-tête: Logo IMANY depuis Google Drive
        if logo_temp_path and os.path.exists(logo_temp_path):
            try:
                canvas_obj.drawImage(logo_temp_path, 20*mm, A4[1] - 20*mm, width=40*mm, height=15*mm, preserveAspectRatio=True)
            except Exception as e:
                print(f"Erreur affichage logo: {e}")
                canvas_obj.setFont('Helvetica-Bold', 12)
                canvas_obj.setFillColor(colors.HexColor('#23456B'))
                canvas_obj.drawString(20*mm, A4[1] - 15*mm, "IMANY")
        else:
            canvas_obj.setFont('Helvetica-Bold', 12)
            canvas_obj.setFillColor(colors.HexColor('#23456B'))
            canvas_obj.drawString(20*mm, A4[1] - 15*mm, "IMANY")

        # Pied de page sur toutes les pages
        canvas_obj.setFont('Helvetica', 7)
        canvas_obj.setFillColor(colors.HexColor('#666666'))

        footer_line1 = "IMANY SN. NINEA /011195816/ RCCM/ SN DKR 2024 B 18099"
        footer_line2 = "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"

        footer_y = 15*mm
        canvas_obj.drawCentredString(A4[0]/2, footer_y + 3*mm, footer_line1)
        canvas_obj.drawCentredString(A4[0]/2, footer_y, footer_line2)

        canvas_obj.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=30*mm,  # Augmenté pour laisser place au logo
        bottomMargin=25*mm,  # Augmenté pour laisser place au footer
    )

    # Styles
    styles = getSampleStyleSheet()

    # Style titre - Couleur IMANY primaire
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#23456b'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Style sous-titre - Couleur IMANY secondaire
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#a25946'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    # Style normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )

    # Style header info
    header_style = ParagraphStyle(
        'HeaderInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#475569'),
    )

    story = []

    # === TITRE === (le logo est dans l'en-tête de page)
    story.append(Paragraph("ÉTAT DE LOYER", title_style))
    story.append(Paragraph("Relevé mensuel pour proprietaire", subtitle_style))
    story.append(Spacer(1, 15))

    # === INFORMATIONS ===
    contrat = invoice.contrat
    locataire = contrat.locataire if contrat else None
    appartement = contrat.appartement if contrat else None
    residence = appartement.residence if appartement else None
    proprietaire = residence.proprietaire if residence else None

    # Informations du proprietaire et du bien
    proprietaire_nom = proprietaire.nom_complet if proprietaire else "N/A"
    proprietaire_tel = proprietaire.telephone if proprietaire and hasattr(proprietaire, 'telephone') and proprietaire.telephone else "Non renseigné"
    proprietaire_email = proprietaire.email if proprietaire and proprietaire.email else "Non renseigné"

    locataire_nom = locataire.nom_complet if locataire else "N/A"

    bien_info = "N/A"
    if appartement and residence:
        bien_info = f"{appartement.nom}\n{residence.nom}\n{residence.adresse}, {residence.ville}"

    info_data = [
        ["PROPRIETAIRE", "BIEN LOUÉ"],
        [
            f"{proprietaire_nom}\n"
            f"Téléphone: {proprietaire_tel}\n"
            f"Email: {proprietaire_email}",
            bien_info
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 1), (-1, -1), 10),
        ('RIGHTPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === INFORMATIONS LOCATAIRE ===
    story.append(Paragraph("<b>LOCATAIRE</b>",
                          ParagraphStyle('SectionTitle', parent=normal_style,
                                       fontSize=12, textColor=colors.HexColor('#23456b'))))
    story.append(Spacer(1, 8))

    locataire_data = [
        ["Nom complet", locataire_nom],
    ]

    locataire_table = Table(locataire_data, colWidths=[60*mm, 110*mm])
    locataire_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(locataire_table)
    story.append(Spacer(1, 20))

    # === CALCUL DU LOYER NET ===
    story.append(Paragraph("<b>CALCUL DU LOYER NET</b>",
                          ParagraphStyle('SectionTitle', parent=normal_style,
                                       fontSize=12, textColor=colors.HexColor('#23456b'))))
    story.append(Spacer(1, 8))

    # Calculs
    loyer_brut = invoice.montant_ttc
    tom_taux = Decimal('0.036')  # 3.6%
    agence_taux = Decimal('0.05')  # 5%

    tom_montant = loyer_brut * tom_taux
    agence_montant = loyer_brut * agence_taux
    loyer_net = loyer_brut - tom_montant - agence_montant

    calcul_data = [
        ["Description", "Montant"],
        ["Loyer brut perçu", f"{loyer_brut:,.0f} FCFA"],
        ["", ""],
        ["TOM (3.6%)", f"- {tom_montant:,.0f} FCFA"],
        ["Frais d'agence (5%)", f"- {agence_montant:,.0f} FCFA"],
        ["", ""],
        ["LOYER NET À REVERSER", f"{loyer_net:,.0f} FCFA"],
    ]

    # Ajouter la période si disponible
    if invoice.periode_debut and invoice.periode_fin:
        calcul_data.insert(1, ["Période", f"du {invoice.periode_debut.strftime('%d/%m/%Y')} au {invoice.periode_fin.strftime('%d/%m/%Y')}"])

    calcul_table = Table(calcul_data, colWidths=[120*mm, 50*mm])
    calcul_table.setStyle(TableStyle([
        # En-tête - Couleur IMANY primaire
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        # Corps du tableau
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

        # Alignement montants
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),

        # Ligne loyer net en gras et vert
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dcfce7')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#a25946')),
    ]))
    story.append(calcul_table)
    story.append(Spacer(1, 25))

    # === MONTANT EN LETTRES ===
    montant_lettres = convert_amount_to_words(loyer_net)
    story.append(Paragraph(
        f"<b>Montant net à reverser au proprietaire :</b><br/>"
        f"<i>{montant_lettres} francs CFA</i>",
        ParagraphStyle('AmountWords', parent=normal_style,
                      fontSize=11, textColor=colors.HexColor('#a25946'),
                      leftIndent=10, rightIndent=10,
                      borderWidth=1, borderColor=colors.HexColor('#d1fae5'),
                      borderPadding=10, backColor=colors.HexColor('#f0fdf4'))
    ))
    story.append(Spacer(1, 25))

    # === SIGNATURE ET CACHET ===
    signature_data = [
        ["", "Fait à Dakar, le " + timezone.now().strftime('%d/%m/%Y')],
        ["", ""],
        ["", "Pour IMANY"],
        ["", ""],
        ["", ""],
        ["", "Le Gestionnaire"],
    ]

    signature_table = Table(signature_data, colWidths=[85*mm, 85*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 20))

    # Note: Le pied de page IMANY est maintenant dans le footer automatique de chaque page
    story.append(Paragraph(
        "<i>Ce document constitue un état de loyer officiel. Il détaille les montants perçus et les retenues effectuées.</i>",
        ParagraphStyle('Footer', parent=header_style,
                      fontSize=8, textColor=colors.HexColor('#94a3b8'),
                      alignment=TA_CENTER)
    ))

    # Construction du PDF avec en-tête et pied de page sur chaque page
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    pdf = buffer.getvalue()
    buffer.close()

    # Nettoyer le fichier temporaire du logo
    if logo_temp_path and os.path.exists(logo_temp_path):
        try:
            os.unlink(logo_temp_path)
        except:
            pass  # Ignorer les erreurs de suppression

    return pdf


def generate_etat_loyer_filename(invoice):
    """
    Génère un nom de fichier pour l'état de loyer
    """
    contrat = invoice.contrat
    residence = contrat.appartement.residence if contrat and contrat.appartement else None
    proprietaire = residence.proprietaire if residence else None
    safe_numero = invoice.numero_facture.replace('/', '_').replace(' ', '_')

    # Utiliser le nom du Tiers
    if proprietaire and proprietaire.nom:
        safe_name = proprietaire.nom.replace(' ', '_')
    else:
        safe_name = "proprietaire"

    return f"etat_loyer_{safe_numero}_{safe_name}.pdf"