# apps/payments/pdf_generators.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from decimal import Decimal


def get_common_styles():
    """Retourne les styles communs pour tous les PDFs avec les couleurs Imani"""
    styles = getSampleStyleSheet()

    # Couleurs Imani
    IMANI_PRIMARY = '#6366f1'  # Indigo/Violet principal
    IMANI_SECONDARY = '#8b5cf6'  # Violet secondaire
    IMANI_DARK = '#5b21b6'  # Violet foncé
    IMANI_GRAY = '#64748b'  # Gris neutre

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor(IMANI_PRIMARY),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor(IMANI_GRAY),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor(IMANI_PRIMARY),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'heading': heading_style,
        'normal': styles['Normal'],
        'colors': {
            'primary': colors.HexColor(IMANI_PRIMARY),
            'secondary': colors.HexColor(IMANI_SECONDARY),
            'dark': colors.HexColor(IMANI_DARK),
            'gray': colors.HexColor(IMANI_GRAY)
        }
    }


def add_header(elements, styles_dict):
    """Ajoute l'en-tête IMANY avec les couleurs Imani"""
    # Style pour le nom de l'entreprise
    company_style = ParagraphStyle(
        'CompanyName',
        parent=styles_dict['normal'],
        fontSize=20,
        textColor=styles_dict['colors']['primary'],
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=6
    )

    # Style pour les coordonnées
    contact_style = ParagraphStyle(
        'ContactInfo',
        parent=styles_dict['normal'],
        fontSize=9,
        textColor=styles_dict['colors']['gray'],
        alignment=TA_CENTER
    )

    header_data = [
        [Paragraph("<b>IMANY</b> by Seyni Properties", company_style)],
        [Paragraph("Liberté 4, Allées Khalifa Ababacar Sy 11000, Dakar - Sénégal", contact_style)],
        [Paragraph("Tél: +221 77 590 84 84 | Email: contact@imany.sn | Web: www.seynisproperties.sn", contact_style)]
    ]

    header_table = Table(header_data, colWidths=[180*mm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 15))


def generate_invoice_loyer_pdf(invoice):
    """Génère un PDF pour une facture de loyer - Style identique aux quittances"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # Styles avec couleurs IMANY
    styles = getSampleStyleSheet()

    # Couleurs IMANY
    IMANY_BLUE = colors.HexColor('#23456B')  # Bleu foncé principal
    IMANY_TERRACOTTA = colors.HexColor('#A25946')  # Marron/Terra cotta
    IMANY_GRAY = colors.HexColor('#64748b')

    # Style titre principal
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=IMANY_BLUE,
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        letterSpacing=2
    )

    # Style sous-titre
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=20,
        textColor=IMANY_TERRACOTTA,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Style section titre
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=IMANY_BLUE,
        fontName='Helvetica-Bold',
        spaceAfter=12,
        spaceBefore=8
    )

    # Style texte normal
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=14,
        leading=20
    )

    story = []

    # === EN-TÊTE ===
    story.append(Paragraph("FACTURE DE LOYER", title_style))
    story.append(Paragraph("Demande de Paiement", subtitle_style))

    # Ligne de séparation
    from reportlab.platypus import HRFlowable
    story.append(HRFlowable(width="100%", thickness=4, color=IMANY_BLUE, spaceAfter=30))

    # === NUMÉRO DE FACTURE ===
    numero_style = ParagraphStyle(
        'NumeroStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Gestion du numéro de facture avec période optionnelle
    if invoice.periode_debut:
        numero_text = f"N° {invoice.numero_facture} - {invoice.periode_debut.strftime('%B %Y').upper()}"
    else:
        numero_text = f"N° {invoice.numero_facture}"

    numero_data = [[Paragraph(numero_text, numero_style)]]
    numero_table = Table(numero_data, colWidths=[170*mm])
    numero_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), IMANY_BLUE),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(numero_table)
    story.append(Spacer(1, 20))

    # === INFORMATIONS ===
    client_info = invoice.get_client_info()

    info_header_style = ParagraphStyle(
        'InfoHeaderStyle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=IMANY_BLUE,
        fontName='Helvetica-Bold'
    )

    info_content_style = ParagraphStyle(
        'InfoContentStyle',
        parent=styles['Normal'],
        fontSize=14,
        leading=22
    )

    info_data = [
        [Paragraph("Propriétaire", info_header_style), Paragraph("Locataire", info_header_style)],
        [
            Paragraph(
                f"<b>{invoice.contrat.appartement.residence.proprietaire.nom_complet if invoice.contrat else 'N/A'}</b><br/>"
                f"{invoice.contrat.appartement.residence.proprietaire.email if invoice.contrat else ''}",
                info_content_style
            ),
            Paragraph(
                f"<b>{client_info['nom']}</b><br/>"
                f"{client_info['email']}<br/>"
                f"{client_info['telephone']}",
                info_content_style
            )
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('LEFTPADDING', (0, 0), (-1, 0), 15),
        ('RIGHTPADDING', (0, 0), (-1, 0), 15),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('LEFTPADDING', (0, 1), (-1, -1), 15),
        ('RIGHTPADDING', (0, 1), (-1, -1), 15),
        ('TOPPADDING', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === BIEN LOUÉ ===
    bien_header_style = ParagraphStyle(
        'BienHeaderStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )

    bien_content_style = ParagraphStyle(
        'BienContentStyle',
        parent=styles['Normal'],
        fontSize=15,
        textColor=colors.white,
        leading=24
    )

    bien_data = [
        [Paragraph("BIEN LOUÉ", bien_header_style)],
        [Paragraph(
            f"<b>Appartement :</b> {invoice.contrat.appartement.nom if invoice.contrat else 'N/A'}<br/>"
            f"<b>Résidence :</b> {invoice.contrat.appartement.residence.nom if invoice.contrat else 'N/A'}<br/>"
            f"<b>Adresse :</b> {client_info['adresse']}<br/>"
            f"<b>Contrat N° :</b> {invoice.contrat.numero_contrat if invoice.contrat else 'N/A'}",
            bien_content_style
        )]
    ]

    bien_table = Table(bien_data, colWidths=[170*mm])
    bien_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#667eea')),
        ('PADDING', (0, 0), (-1, -1), 25),  # Augmenté de 15 à 20
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(bien_table)
    story.append(Spacer(1, 20))

    # === DÉTAILS DU PAIEMENT ===
    detail_header_style = ParagraphStyle(
        'DetailHeaderStyle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )

    detail_content_style = ParagraphStyle(
        'DetailContentStyle',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold'
    )

    # Calculer les montants
    loyer = invoice.contrat.loyer_mensuel if invoice.contrat else invoice.montant_ht
    charges = invoice.contrat.charges_mensuelles if invoice.contrat else 0
    total = invoice.montant_ttc

    # Détecter si c'est une facture initiale PMO (contient "Dépôt de garantie" dans la description)
    is_facture_initiale = invoice.description and "Dépôt de garantie" in invoice.description

    details_data = [
        [Paragraph("DÉSIGNATION", detail_header_style), Paragraph("MONTANT", detail_header_style)],
    ]

    if is_facture_initiale and invoice.contrat:
        # Facture initiale PMO avec 3 mois de conditions
        depot_garantie = invoice.contrat.depot_garantie
        details_data.extend([
            [Paragraph("Dépôt de garantie (caution)", detail_content_style), Paragraph(f"{depot_garantie:,.0f} FCFA", detail_content_style)],
            [Paragraph("Loyer du 1er mois", detail_content_style), Paragraph(f"{loyer:,.0f} FCFA", detail_content_style)],
            [Paragraph("Charges du 1er mois", detail_content_style), Paragraph(f"{charges:,.0f} FCFA", detail_content_style)],
        ])
    else:
        # Facture de loyer mensuel normale
        details_data.extend([
            [Paragraph("Loyer mensuel", detail_content_style), Paragraph(f"{loyer:,.0f} FCFA", detail_content_style)],
            [Paragraph("Charges mensuelles", detail_content_style), Paragraph(f"{charges:,.0f} FCFA", detail_content_style)],
        ])

    details_table = Table(details_data, colWidths=[120*mm, 50*mm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), IMANY_BLUE),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('PADDING', (0, 0), (-1, 0), 15),  # Augmenté de 12 à 15
        ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('PADDING', (0, 1), (-1, -1), 15),  # Augmenté de 12 à 15
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ]))
    story.append(details_table)

    # Total avec fond gris
    total_data = [
        [Paragraph("<b>TOTAL</b>", detail_content_style), Paragraph(f"<b>{total:,.0f} FCFA</b>", detail_content_style)]
    ]
    total_table = Table(total_data, colWidths=[120*mm, 50*mm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 15),  # Augmenté de 12 à 15
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 30))

    # === MONTANT PRINCIPAL EN GRAND ===
    montant_principal_style = ParagraphStyle(
        'MontantPrincipalStyle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#65432B'),  # Marron foncé au lieu de vert
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )

    montant_chiffre_style = ParagraphStyle(
        'MontantChiffreStyle',
        parent=styles['Normal'],
        fontSize=48,
        textColor=IMANY_TERRACOTTA,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )

    montant_lettres_style = ParagraphStyle(
        'MontantLettresStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#65432B'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )

    montant_data = [
        [Paragraph("Montant Total à Payer", montant_principal_style)],
        [Paragraph(f"{total:,.0f} FCFA", montant_chiffre_style)],
        [Paragraph(f"Arrêté la présente facture à la somme de :<br/><b>{total:,.0f} Francs CFA</b>", montant_lettres_style)]
    ]

    montant_table = Table(montant_data, colWidths=[170*mm])
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF5F1')),  # Beige clair
        ('BOX', (0, 0), (-1, -1), 3, IMANY_TERRACOTTA),
        ('PADDING', (0, 0), (-1, -1), 25),  # Augmenté de 20 à 25
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(montant_table)
    story.append(Spacer(1, 25))

    # === INFORMATIONS DE PAIEMENT ===
    info_box_header_style = ParagraphStyle(
        'InfoBoxHeaderStyle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=IMANY_BLUE,
        fontName='Helvetica-Bold'
    )

    info_box_content_style = ParagraphStyle(
        'InfoBoxContentStyle',
        parent=styles['Normal'],
        fontSize=14
    )

    # Période et échéance - Gestion des factures initiales sans période
    info_lines = []
    if invoice.periode_debut and invoice.periode_fin:
        info_lines.append(f"<b>Période :</b> du {invoice.periode_debut.strftime('%d/%m/%Y')} au {invoice.periode_fin.strftime('%d/%m/%Y')}")

    info_lines.append(f"<b>Date d'échéance :</b> {invoice.date_echeance.strftime('%d/%m/%Y')}")
    info_lines.append(f"<b>Contrat N° :</b> {invoice.contrat.numero_contrat if invoice.contrat else 'N/A'}")

    info_paiement_data = [
        [Paragraph("Informations de Paiement", info_box_header_style)],
        [Paragraph("<br/>".join(info_lines), info_box_content_style)]
    ]

    info_paiement_table = Table(info_paiement_data, colWidths=[170*mm])
    info_paiement_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('LEFTPADDING', (0, 0), (-1, 0), 15),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('PADDING', (0, 0), (-1, -1), 15),  # Augmenté de 12 à 15
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(info_paiement_table)
    story.append(Spacer(1, 40))

    # === PIED DE PAGE ===
    from django.utils import timezone
    date_today = timezone.now().strftime('%d/%m/%Y')

    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("<b>IMANY by Seyni Properties</b> - Gestion Locative Professionnelle", footer_style))
    story.append(Paragraph("Liberté 4, Allées Khalifa Ababacar Sy, 11000, Dakar - Sénégal", footer_style))
    story.append(Paragraph("Tél: +221 77 590 84 84 | Email: contact@imany.sn | Web: www.seyniproperties.sn", footer_style))
    story.append(Paragraph(f"Document généré automatiquement le {date_today}",
                          ParagraphStyle('FooterDate', parent=footer_style, fontSize=9, textColor=colors.HexColor('#cccccc'))))

    # Construction du PDF
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_invoice_syndic_pdf(invoice):
    """Genere un PDF pour une facture syndic - Style IMANY"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # Styles avec couleurs IMANY
    styles = getSampleStyleSheet()
    IMANY_BLUE = colors.HexColor('#23456B')
    IMANY_TERRACOTTA = colors.HexColor('#A25946')
    IMANY_PURPLE = colors.HexColor('#9333ea')

    from reportlab.platypus import HRFlowable
    from django.utils import timezone

    story = []

    # === EN-TÊTE ===
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=32,
                                 textColor=IMANY_BLUE, alignment=TA_CENTER,
                                 fontName='Helvetica-Bold', letterSpacing=2, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=20,
                                   textColor=IMANY_PURPLE, alignment=TA_CENTER,
                                   fontName='Helvetica-Bold', spaceAfter=30)

    story.append(Paragraph("FACTURE SYNDIC", title_style))
    story.append(Paragraph("Copropriété", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=4, color=IMANY_BLUE, spaceAfter=30))

    # === NUMÉRO DE FACTURE ===
    numero_style = ParagraphStyle('Numero', parent=styles['Normal'], fontSize=18,
                                  textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    numero_data = [[Paragraph(f"N° {invoice.numero_facture} - {invoice.date_emission.strftime('%B %Y').upper()}", numero_style)]]
    numero_table = Table(numero_data, colWidths=[170*mm])
    numero_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), IMANY_BLUE),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(numero_table)
    story.append(Spacer(1, 20))

    # === INFORMATIONS ===
    info_header_style = ParagraphStyle('InfoHeader', parent=styles['Normal'], fontSize=13,
                                      textColor=IMANY_BLUE, fontName='Helvetica-Bold')
    info_content_style = ParagraphStyle('InfoContent', parent=styles['Normal'], fontSize=14, leading=22)

    info_data = [
        [Paragraph("Copropriétaire", info_header_style), Paragraph("Détails", info_header_style)],
        [
            Paragraph(f"<b>{invoice.destinataire_nom}</b><br/>"
                     f"{invoice.destinataire_adresse or ''}<br/>"
                     f"{invoice.destinataire_email}<br/>{invoice.destinataire_telephone}", info_content_style),
            Paragraph(f"<b>Référence:</b> {invoice.reference_copropriete or 'N/A'}<br/>"
                     f"<b>Date émission:</b> {invoice.date_emission.strftime('%d/%m/%Y')}<br/>"
                     f"<b>Date échéance:</b> {invoice.date_echeance.strftime('%d/%m/%Y')}", info_content_style)
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === DÉTAILS ===
    detail_header_style = ParagraphStyle('DetailHeader', parent=styles['Normal'], fontSize=13,
                                        textColor=colors.white, fontName='Helvetica-Bold')

    details_data = [
        [Paragraph("DÉSIGNATION", detail_header_style), Paragraph("MONTANT", detail_header_style)],
        [Paragraph(invoice.description or "Cotisation trimestrielle", info_content_style),
         Paragraph(f"{invoice.montant_ttc:,.0f} FCFA", ParagraphStyle('Bold', parent=info_content_style, fontName='Helvetica-Bold'))]
    ]

    details_table = Table(details_data, colWidths=[120*mm, 50*mm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), IMANY_PURPLE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(details_table)

    # === MONTANT TOTAL ===
    montant_principal_style = ParagraphStyle('MontantP', parent=styles['Normal'], fontSize=18,
                                            textColor=colors.HexColor('#65432B'), fontName='Helvetica-Bold', alignment=TA_CENTER)
    montant_chiffre_style = ParagraphStyle('MontantC', parent=styles['Normal'], fontSize=48,
                                          textColor=IMANY_TERRACOTTA, fontName='Helvetica-Bold', alignment=TA_CENTER)

    montant_data = [
        [Paragraph("Montant Total à Régler", montant_principal_style)],
        [Paragraph(f"{invoice.montant_ttc:,.0f} FCFA", montant_chiffre_style)],
    ]

    montant_table = Table(montant_data, colWidths=[170*mm])
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF5F1')),
        ('BOX', (0, 0), (-1, -1), 3, IMANY_TERRACOTTA),
        ('PADDING', (0, 0), (-1, -1), 25),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(montant_table)
    story.append(Spacer(1, 30))

    # === FOOTER ===
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=11,
                                  textColor=colors.HexColor('#999999'), alignment=TA_CENTER)

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("<b>IMANY by Seyni Properties</b> - Gestion Locative Professionnelle", footer_style))
    story.append(Paragraph("Liberté 4, Allées Khalifa Ababacar Sy, 11000, Dakar - Sénégal", footer_style))
    story.append(Paragraph("Tél: +221 77 590 84 84 | Email: contact@imany.sn | Web: www.seyniproperties.sn", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_invoice_achat_pdf(invoice):
    """Genere un PDF pour une facture de demande d'achat - Style IMANY"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # Styles avec couleurs IMANY
    styles = getSampleStyleSheet()
    IMANY_BLUE = colors.HexColor('#23456B')
    IMANY_TERRACOTTA = colors.HexColor('#A25946')
    IMANY_ORANGE = colors.HexColor('#f97316')

    from reportlab.platypus import HRFlowable
    from django.utils import timezone

    story = []

    # === EN-TÊTE ===
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=32,
                                 textColor=IMANY_BLUE, alignment=TA_CENTER,
                                 fontName='Helvetica-Bold', letterSpacing=2, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=20,
                                   textColor=IMANY_TERRACOTTA, alignment=TA_CENTER,
                                   fontName='Helvetica-Bold', spaceAfter=30)

    story.append(Paragraph("DEMANDE D'ACHAT", title_style))
    story.append(Paragraph("Bon de Commande", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=4, color=IMANY_BLUE, spaceAfter=30))

    # === NUMÉRO DE FACTURE ===
    numero_style = ParagraphStyle('Numero', parent=styles['Normal'], fontSize=18,
                                  textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    numero_data = [[Paragraph(f"N° {invoice.numero_facture} - {invoice.date_emission.strftime('%B %Y').upper()}", numero_style)]]
    numero_table = Table(numero_data, colWidths=[170*mm])
    numero_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), IMANY_BLUE),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(numero_table)
    story.append(Spacer(1, 20))

    # === INFORMATIONS ===
    info_header_style = ParagraphStyle('InfoHeader', parent=styles['Normal'], fontSize=13,
                                      textColor=IMANY_BLUE, fontName='Helvetica-Bold')
    info_content_style = ParagraphStyle('InfoContent', parent=styles['Normal'], fontSize=14, leading=22)

    info_data = [
        [Paragraph("🏪 Fournisseur", info_header_style), Paragraph("📦 Détails Commande", info_header_style)],
        [
            Paragraph(f"<b>{invoice.destinataire_nom}</b><br/>"
                     f"{invoice.destinataire_email}<br/>{invoice.destinataire_telephone}", info_content_style),
            Paragraph(f"<b>Bon de commande:</b> {invoice.numero_bon_commande or 'N/A'}<br/>"
                     f"<b>Date émission:</b> {invoice.date_emission.strftime('%d/%m/%Y')}<br/>"
                     f"<b>Date échéance:</b> {invoice.date_echeance.strftime('%d/%m/%Y')}", info_content_style)
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === DÉTAILS ===
    detail_header_style = ParagraphStyle('DetailHeader', parent=styles['Normal'], fontSize=13,
                                        textColor=colors.white, fontName='Helvetica-Bold')

    details_data = [
        [Paragraph("DÉSIGNATION", detail_header_style), Paragraph("MONTANT", detail_header_style)],
        [Paragraph(invoice.description or "Achat de matériel/fournitures", info_content_style),
         Paragraph(f"{invoice.montant_ht:,.0f} FCFA", ParagraphStyle('Bold', parent=info_content_style, fontName='Helvetica-Bold'))]
    ]

    details_table = Table(details_data, colWidths=[120*mm, 50*mm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), IMANY_TERRACOTTA),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))

    # === TOTAUX ===
    tva_montant = invoice.montant_ttc - invoice.montant_ht
    totaux_data = [
        [Paragraph("Montant HT", info_content_style), Paragraph(f"{invoice.montant_ht:,.0f} FCFA", info_content_style)],
        [Paragraph(f"TVA ({invoice.taux_tva}%)", info_content_style), Paragraph(f"{tva_montant:,.0f} FCFA", info_content_style)],
    ]
    totaux_table = Table(totaux_data, colWidths=[120*mm, 50*mm])
    totaux_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(totaux_table)

    # === MONTANT TOTAL ===
    montant_principal_style = ParagraphStyle('MontantP', parent=styles['Normal'], fontSize=18,
                                            textColor=colors.HexColor('#65432B'), fontName='Helvetica-Bold', alignment=TA_CENTER)
    montant_chiffre_style = ParagraphStyle('MontantC', parent=styles['Normal'], fontSize=48,
                                          textColor=IMANY_TERRACOTTA, fontName='Helvetica-Bold', alignment=TA_CENTER)

    montant_data = [
        [Paragraph("Montant Total TTC", montant_principal_style)],
        [Paragraph(f"{invoice.montant_ttc:,.0f} FCFA", montant_chiffre_style)],
    ]

    montant_table = Table(montant_data, colWidths=[170*mm])
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF5F1')),
        ('BOX', (0, 0), (-1, -1), 3, IMANY_TERRACOTTA),
        ('PADDING', (0, 0), (-1, -1), 25),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(montant_table)
    story.append(Spacer(1, 30))

    # === FOOTER ===
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=11,
                                  textColor=colors.HexColor('#999999'), alignment=TA_CENTER)

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("<b>IMANY by Seyni Properties</b> - Gestion Locative Professionnelle", footer_style))
    story.append(Paragraph("Liberté 4, Allées Khalifa Ababacar Sy, 11000, Dakar - Sénégal", footer_style))
    story.append(Paragraph("Tél: +221 77 590 84 84 | Email: contact@imany.sn | Web: www.seyniproperties.sn", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_invoice_prestataire_pdf(invoice):
    """Genere un PDF pour une facture prestataire - Style IMANY"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # Styles avec couleurs IMANY
    styles = getSampleStyleSheet()
    IMANY_BLUE = colors.HexColor('#23456B')
    IMANY_TERRACOTTA = colors.HexColor('#A25946')
    IMANY_ORANGE = colors.HexColor('#f97316')

    from reportlab.platypus import HRFlowable
    from django.utils import timezone

    story = []

    # === EN-TÊTE ===
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=32,
                                 textColor=IMANY_BLUE, alignment=TA_CENTER,
                                 fontName='Helvetica-Bold', letterSpacing=2, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=20,
                                   textColor=IMANY_ORANGE, alignment=TA_CENTER,
                                   fontName='Helvetica-Bold', spaceAfter=30)

    story.append(Paragraph("FACTURE PRESTATAIRE", title_style))
    story.append(Paragraph("Prestation de Service", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=4, color=IMANY_BLUE, spaceAfter=30))

    # === NUMÉRO DE FACTURE ===
    numero_style = ParagraphStyle('Numero', parent=styles['Normal'], fontSize=18,
                                  textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    numero_data = [[Paragraph(f"N° {invoice.numero_facture} - {invoice.date_emission.strftime('%B %Y').upper()}", numero_style)]]
    numero_table = Table(numero_data, colWidths=[170*mm])
    numero_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), IMANY_BLUE),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(numero_table)
    story.append(Spacer(1, 20))

    # === INFORMATIONS ===
    info_header_style = ParagraphStyle('InfoHeader', parent=styles['Normal'], fontSize=13,
                                      textColor=IMANY_BLUE, fontName='Helvetica-Bold')
    info_content_style = ParagraphStyle('InfoContent', parent=styles['Normal'], fontSize=14, leading=22)

    info_data = [
        [Paragraph("Prestataire", info_header_style), Paragraph("Détails Prestation", info_header_style)],
        [
            Paragraph(f"<b>{invoice.fournisseur_nom}</b><br/>"
                     f"Ref: {invoice.fournisseur_reference or 'N/A'}<br/>"
                     f"{invoice.destinataire_email}<br/>{invoice.destinataire_telephone}", info_content_style),
            Paragraph(f"<b>Date émission:</b> {invoice.date_emission.strftime('%d/%m/%Y')}<br/>"
                     f"<b>Date échéance:</b> {invoice.date_echeance.strftime('%d/%m/%Y')}", info_content_style)
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === DÉTAILS ===
    detail_header_style = ParagraphStyle('DetailHeader', parent=styles['Normal'], fontSize=13,
                                        textColor=colors.white, fontName='Helvetica-Bold')

    details_data = [
        [Paragraph("DÉSIGNATION", detail_header_style), Paragraph("MONTANT", detail_header_style)],
        [Paragraph(invoice.description or "Prestation de service", info_content_style),
         Paragraph(f"{invoice.montant_ht:,.0f} FCFA", ParagraphStyle('Bold', parent=info_content_style, fontName='Helvetica-Bold'))]
    ]

    details_table = Table(details_data, colWidths=[120*mm, 50*mm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), IMANY_ORANGE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))

    # === TOTAUX ===
    tva_montant = invoice.montant_ttc - invoice.montant_ht
    totaux_data = [
        [Paragraph("Montant HT", info_content_style), Paragraph(f"{invoice.montant_ht:,.0f} FCFA", info_content_style)],
        [Paragraph(f"TVA ({invoice.taux_tva}%)", info_content_style), Paragraph(f"{tva_montant:,.0f} FCFA", info_content_style)],
    ]
    totaux_table = Table(totaux_data, colWidths=[120*mm, 50*mm])
    totaux_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(totaux_table)

    # === MONTANT TOTAL ===
    montant_principal_style = ParagraphStyle('MontantP', parent=styles['Normal'], fontSize=18,
                                            textColor=colors.HexColor('#65432B'), fontName='Helvetica-Bold', alignment=TA_CENTER)
    montant_chiffre_style = ParagraphStyle('MontantC', parent=styles['Normal'], fontSize=48,
                                          textColor=IMANY_TERRACOTTA, fontName='Helvetica-Bold', alignment=TA_CENTER)

    montant_data = [
        [Paragraph("Montant Total TTC", montant_principal_style)],
        [Paragraph(f"{invoice.montant_ttc:,.0f} FCFA", montant_chiffre_style)],
    ]

    montant_table = Table(montant_data, colWidths=[170*mm])
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF5F1')),
        ('BOX', (0, 0), (-1, -1), 3, IMANY_TERRACOTTA),
        ('PADDING', (0, 0), (-1, -1), 25),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(montant_table)
    story.append(Spacer(1, 30))

    # === FOOTER ===
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=11,
                                  textColor=colors.HexColor('#999999'), alignment=TA_CENTER)

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("<b>IMANY by Seyni Properties</b> - Gestion Locative Professionnelle", footer_style))
    story.append(Paragraph("Liberté 4, Allées Khalifa Ababacar Sy, 11000, Dakar - Sénégal", footer_style))
    story.append(Paragraph("Tél: +221 77 590 84 84 | Email: contact@imany.sn | Web: www.seyniproperties.sn", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_invoice_default_pdf(invoice):
    """Genere un PDF generique pour les autres types de factures - Style IMANY"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # Styles avec couleurs IMANY
    styles = getSampleStyleSheet()
    IMANY_BLUE = colors.HexColor('#23456B')
    IMANY_TERRACOTTA = colors.HexColor('#A25946')

    from reportlab.platypus import HRFlowable
    from django.utils import timezone

    story = []

    # === EN-TÊTE ===
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=32,
                                 textColor=IMANY_BLUE, alignment=TA_CENTER,
                                 fontName='Helvetica-Bold', letterSpacing=2, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=20,
                                   textColor=IMANY_TERRACOTTA, alignment=TA_CENTER,
                                   fontName='Helvetica-Bold', spaceAfter=30)

    story.append(Paragraph("FACTURE", title_style))
    story.append(Paragraph(invoice.get_type_facture_display() if hasattr(invoice, 'get_type_facture_display') else "Document", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=4, color=IMANY_BLUE, spaceAfter=30))

    # === NUMÉRO DE FACTURE ===
    numero_style = ParagraphStyle('Numero', parent=styles['Normal'], fontSize=18,
                                  textColor=colors.white, alignment=TA_CENTER, fontName='Helvetica-Bold')
    numero_data = [[Paragraph(f"N° {invoice.numero_facture} - {invoice.date_emission.strftime('%B %Y').upper()}", numero_style)]]
    numero_table = Table(numero_data, colWidths=[170*mm])
    numero_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), IMANY_BLUE),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(numero_table)
    story.append(Spacer(1, 20))

    # === INFORMATIONS ===
    client_info = invoice.get_client_info()
    info_header_style = ParagraphStyle('InfoHeader', parent=styles['Normal'], fontSize=13,
                                      textColor=IMANY_BLUE, fontName='Helvetica-Bold')
    info_content_style = ParagraphStyle('InfoContent', parent=styles['Normal'], fontSize=14, leading=22)

    info_data = [
        [Paragraph("Client", info_header_style), Paragraph("Détails", info_header_style)],
        [
            Paragraph(f"<b>{client_info['nom']}</b><br/>"
                     f"{client_info['adresse']}<br/>"
                     f"{client_info['email']}<br/>{client_info['telephone']}", info_content_style),
            Paragraph(f"<b>Date émission:</b> {invoice.date_emission.strftime('%d/%m/%Y')}<br/>"
                     f"<b>Date échéance:</b> {invoice.date_echeance.strftime('%d/%m/%Y')}", info_content_style)
        ]
    ]

    info_table = Table(info_data, colWidths=[85*mm, 85*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # === DÉTAILS ===
    detail_header_style = ParagraphStyle('DetailHeader', parent=styles['Normal'], fontSize=13,
                                        textColor=colors.white, fontName='Helvetica-Bold')

    details_data = [
        [Paragraph("DÉSIGNATION", detail_header_style), Paragraph("MONTANT", detail_header_style)],
        [Paragraph(invoice.description or "Facture", info_content_style),
         Paragraph(f"{invoice.montant_ht:,.0f} FCFA", ParagraphStyle('Bold', parent=info_content_style, fontName='Helvetica-Bold'))]
    ]

    details_table = Table(details_data, colWidths=[120*mm, 50*mm])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))

    # === TOTAUX ===
    tva_montant = invoice.montant_ttc - invoice.montant_ht
    totaux_data = [
        [Paragraph("Montant HT", info_content_style), Paragraph(f"{invoice.montant_ht:,.0f} FCFA", info_content_style)],
        [Paragraph(f"TVA ({invoice.taux_tva}%)", info_content_style), Paragraph(f"{tva_montant:,.0f} FCFA", info_content_style)],
    ]
    totaux_table = Table(totaux_data, colWidths=[120*mm, 50*mm])
    totaux_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    story.append(totaux_table)

    # === MONTANT TOTAL ===
    montant_principal_style = ParagraphStyle('MontantP', parent=styles['Normal'], fontSize=18,
                                            textColor=colors.HexColor('#65432B'), fontName='Helvetica-Bold', alignment=TA_CENTER)
    montant_chiffre_style = ParagraphStyle('MontantC', parent=styles['Normal'], fontSize=48,
                                          textColor=IMANY_TERRACOTTA, fontName='Helvetica-Bold', alignment=TA_CENTER)

    montant_data = [
        [Paragraph("Montant Total TTC", montant_principal_style)],
        [Paragraph(f"{invoice.montant_ttc:,.0f} FCFA", montant_chiffre_style)],
    ]

    montant_table = Table(montant_data, colWidths=[170*mm])
    montant_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF5F1')),
        ('BOX', (0, 0), (-1, -1), 3, IMANY_TERRACOTTA),
        ('PADDING', (0, 0), (-1, -1), 25),
        ('ROUNDEDCORNERS', [12, 12, 12, 12]),
    ]))
    story.append(montant_table)
    story.append(Spacer(1, 30))

    # === FOOTER ===
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=11,
                                  textColor=colors.HexColor('#999999'), alignment=TA_CENTER)

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("<b>IMANY by Seyni Properties</b> - Gestion Locative Professionnelle", footer_style))
    story.append(Paragraph("Liberté 4, Allées Khalifa Ababacar Sy, 11000, Dakar - Sénégal", footer_style))
    story.append(Paragraph("Tél: +221 77 590 84 84 | Email: contact@imany.sn | Web: www.seyniproperties.sn", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()