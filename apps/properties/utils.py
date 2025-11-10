# apps/properties/utils.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY  # ✅ AJOUTE TA_RIGHT ici

from io import BytesIO
from django.utils import timezone


def generate_etat_lieux_pdf(etat_lieux):
    """
    Génère un état des lieux en PDF selon le modèle IMANY
    
    Args:
        etat_lieux: Instance du modèle EtatDesLieux
        
    Returns:
        BytesIO contenant le PDF généré
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Style titre principal - Couleur IMANY primaire avec fond
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.white,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=12,
        backColor=colors.HexColor('#23456b')
    )
    
    # Style normal
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )
    
    # Style bold
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold'
    )
    
    # En-tête entreprise
    header_text = (
        "IMANY SN SUARL. NINEA /011195816/ RCCM/SN DKR 2023 B 18099.<br/>"
        "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"
    )
    story.append(Paragraph(header_text, ParagraphStyle('Header', parent=normal_style, alignment=TA_CENTER, fontSize=9)))
    story.append(Spacer(1, 20))
    
    # Titre principal
    titre = f"ÉTAT DES LIEUX {'ENTREE' if etat_lieux.type_etat == 'entree' else 'SORTIE'}"
    story.append(Paragraph(titre, title_style))
    story.append(Spacer(1, 20))
    
    # Date
    date_str = etat_lieux.date_etat.strftime('%d/%m/%Y')
    story.append(Paragraph(f"<b>Date : {date_str}</b>", ParagraphStyle('Date', parent=normal_style, alignment=TA_RIGHT)))
    story.append(Spacer(1, 15))
    
    # Informations du bien
    residence_nom = etat_lieux.residence.nom if etat_lieux.residence else "N/A"
    story.append(Paragraph(f"<b>Résidence ({residence_nom.upper()}) :</b>", bold_style))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph(f"Appartement : {etat_lieux.appartement.nom or 'N/A'}", normal_style))
    story.append(Paragraph(f"Niveau : {etat_lieux.appartement.etage or 'N/A'}", normal_style))
    
    # Locataire
    locataire_nom = etat_lieux.locataire.nom_complet if etat_lieux.locataire else "N/A"
    story.append(Paragraph(f"Locataire ou représentant : {locataire_nom}", normal_style))
    
    # Commercial IMANY
    commercial = etat_lieux.commercial_imany or "N/A"
    story.append(Paragraph(f"Commercial IMANY : {commercial}", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Tableau des détails
    # En-têtes du tableau
    table_data = [
        [Paragraph('<b>Pièces</b>', bold_style), 
         Paragraph('<b>Corps d\'état</b>', bold_style), 
         Paragraph('<b>Observations</b>', bold_style)]
    ]
    
    # Ajouter les détails
    details = etat_lieux.details.all().order_by('ordre', 'piece')
    
    if details.exists():
        for detail in details:
            table_data.append([
                Paragraph(detail.piece, normal_style),
                Paragraph(detail.corps_etat, normal_style),
                Paragraph(detail.observations or '', normal_style)
            ])
    else:
        # Si pas de détails, ajouter des lignes vides pour remplissage manuel
        for _ in range(15):
            table_data.append(['', '', ''])
    
    # Créer le tableau
    col_widths = [50*mm, 50*mm, 70*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # En-tête - Couleur IMANY primaire
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Contenu
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Grille
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Observation globale
    story.append(Paragraph("<b>Observation globale :</b>", bold_style))
    story.append(Spacer(1, 5))
    
    if etat_lieux.observation_globale:
        story.append(Paragraph(etat_lieux.observation_globale, normal_style))
    else:
        # Lignes vides pour remplissage manuel
        for _ in range(6):
            story.append(Paragraph("…" * 100, normal_style))
            story.append(Spacer(1, 3))
    
    story.append(Spacer(1, 30))
    
    # Tableau signatures
    story.append(Paragraph("<b>SIGNATURE</b>", bold_style))
    story.append(Spacer(1, 10))
    
    sig_data = [
        [Paragraph('<b>Bailleur</b>', ParagraphStyle('SigHeader', parent=bold_style, alignment=TA_CENTER)),
         Paragraph('<b>Locataire</b>', ParagraphStyle('SigHeader', parent=bold_style, alignment=TA_CENTER))],
        ['', ''],
        ['', ''],
        ['', ''],
    ]
    
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm], rowHeights=[12*mm, 35*mm, 10*mm, 10*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
    ]))
    story.append(sig_table)
    
    # Pied de page
    story.append(Spacer(1, 20))
    footer = (
        "IMANY SN SUARL. NINEA /011195816/ RCCM/SN DKR 2023 B 18099.<br/>"
        "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"
    )
    story.append(Paragraph(footer, ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    # Construction du PDF
    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_etat_lieux_filename(etat_lieux):
    """
    Génère un nom de fichier pour l'état des lieux
    """
    type_str = "entree" if etat_lieux.type_etat == "entree" else "sortie"
    safe_numero = etat_lieux.numero_etat.replace('/', '_').replace(' ', '_')
    appt = etat_lieux.appartement.nom.replace('/', '_').replace(' ', '_')
    return f"etat_lieux_{type_str}_{safe_numero}_{appt}.pdf"




# apps/properties/utils.py

def generate_remise_cles_pdf(remise):
    """
    Génère une attestation de remise des clés en PDF selon le modèle IMANY SIMPLIFIÉ
    
    Args:
        remise: Instance du modèle RemiseDesCles
        
    Returns:
        BytesIO contenant le PDF généré
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30*mm,
        leftMargin=30*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # ============ STYLES ============
    
    # Style titre principal - Couleur IMANY primaire
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#23456b'),
        spaceAfter=30,
        spaceBefore=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        underlineWidth=1,
    )
    
    # Style normal
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        leading=16,
        alignment=TA_JUSTIFY,
    )
    
    # Style bold
    bold_style = ParagraphStyle(
        'Bold',
        parent=normal_style,
        fontName='Helvetica-Bold',
        fontSize=11
    )
    
    # ============ HEADER ENTREPRISE ============
    
    header_text = (
        "IMANY SN. NINEA /011195816/ RCCM/ SN DKR 2024 B 18099<br/>"
        "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"
    )
    story.append(Paragraph(header_text, ParagraphStyle('Header', parent=normal_style, alignment=TA_CENTER, fontSize=9)))
    story.append(Spacer(1, 15))
    
    # ============ TITRE ============
    
    titre = "ATTESTATION DE REMISE DE CLES"
    story.append(Paragraph(titre, title_style))
    story.append(Spacer(1, 30))
    
    # ============ TEXTE PRINCIPAL ============
    
    # Déterminer le type de bien
    type_bien_display = remise.appartement.get_type_bien_display() if remise.appartement else "Appartement"
    
    # Adresse complète
    adresse = ""
    if remise.appartement and remise.appartement.residence:
        residence = remise.appartement.residence
        adresse = f"{residence.adresse}, {residence.ville}"
    
    # Nom du locataire
    nom_locataire = remise.recu_par or (remise.locataire.nom_complet if remise.locataire else "")

    # Date formatée
    date_remise_fr = remise.date_remise.strftime('%d/%m/%Y')

    # Paragraphe principal - Utiliser M. pour éviter le problème de genre
    texte_principal = f"""
    Nous soussignée <b>Syndic Imany</b>, attestons avoir procédé à la remise des clés de
    <b>{type_bien_display}</b> située à <b>{adresse}</b>, à M.
    <b>{nom_locataire}</b>, locataire dudit logement.
    """

    story.append(Paragraph(texte_principal, normal_style))
    story.append(Spacer(1, 15))

    # Paragraphe 2
    texte_date = f"""
    Cette remise a eu lieu le <b>{date_remise_fr}</b>, en présence des deux parties, après vérification
    de l'état du logement.
    """

    story.append(Paragraph(texte_date, normal_style))
    story.append(Spacer(1, 15))

    # Reconnaissance - Utiliser "Le locataire" de manière neutre
    story.append(Paragraph(f"Le locataire reconnait avoir reçu les clés suivantes :", normal_style))
    story.append(Spacer(1, 10))
    
    # ============ LISTE DES CLÉS ============
    
    # Calculer le total de clés
    total_cles = remise.nombre_cles_appartement
    if remise.nombre_cles_boite_lettres:
        total_cles += remise.nombre_cles_boite_lettres
    if remise.nombre_cles_garage:
        total_cles += remise.nombre_cles_garage
    
    # Déterminer le texte du type de bien
    type_bien_text = type_bien_display.lower()
    if type_bien_text == "studio":
        type_bien_text = "studio"
    elif type_bien_text in ["villa", "maison"]:
        type_bien_text = "villa"
    else:
        type_bien_text = "l'appartement"
    
    cles_text = f"<b>{total_cles}</b> clés de la porte principale de {type_bien_text}"
    
    # Ajouter une puce
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=normal_style,
        leftIndent=30,
        bulletIndent=10,
        fontSize=11,
    )
    
    story.append(Paragraph(f"• {cles_text}", bullet_style))
    story.append(Spacer(1, 40))
    
    # ============ DATE ET SIGNATURES ============
    
    story.append(Paragraph(f"Fait à Dakar, le {date_remise_fr}", ParagraphStyle('DateFait', parent=normal_style, alignment=TA_RIGHT, fontSize=11)))
    story.append(Spacer(1, 30))
    
    # Table de signatures
    sig_data = [
        [
            Paragraph('<b>Syndic</b>', ParagraphStyle('SigHeader', parent=bold_style, alignment=TA_CENTER)),
            Paragraph('<b>Locataire</b>', ParagraphStyle('SigHeader', parent=bold_style, alignment=TA_CENTER))
        ],
        ["", ""],
        ["", ""],
        ["", ""],
    ]
    
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm], rowHeights=[15*mm, 30*mm, 30*mm, 15*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
    ]))
    story.append(sig_table)
    
    # ============ PIED DE PAGE ============
    
    story.append(Spacer(1, 30))
    footer = (
        "IMANY SN. NINEA /011195816/ RCCM/ SN DKR 2024 B 18099<br/>"
        "Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"
    )
    story.append(Paragraph(footer, ParagraphStyle('Footer', parent=normal_style, fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    # Construction du PDF
    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_remise_cles_filename(remise):
    """
    Génère un nom de fichier pour l'attestation de remise des clés
    """
    type_str = "entree" if remise.type_remise == "entree" else "sortie"
    safe_numero = remise.numero_attestation.replace('/', '_').replace(' ', '_')
    appt = remise.appartement.nom.replace('/', '_').replace(' ', '_')
    return f"remise_cles_{type_str}_{safe_numero}_{appt}.pdf"