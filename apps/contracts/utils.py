import os
from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.http import HttpResponse
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_contract_pdf(contract):
    """
    Génère un PDF du contrat de location
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=20*mm, leftMargin=20*mm,
                          topMargin=20*mm, bottomMargin=20*mm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    # Contenu du PDF
    story = []
    
    # En-tête
    story.append(Paragraph("CONTRAT DE LOCATION", title_style))
    story.append(Paragraph(f"N° {contract.contract_number}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Informations générales
    story.append(Paragraph("INFORMATIONS GÉNÉRALES", heading_style))
    
    # Calcul de la durée en mois
    duration_months = (contract.end_date.year - contract.start_date.year) * 12 + contract.end_date.month - contract.start_date.month
    
    general_data = [
        ["Numéro de contrat:", contract.contract_number],
        ["Date de début:", contract.start_date.strftime("%d/%m/%Y")],
        ["Date de fin:", contract.end_date.strftime("%d/%m/%Y")],
        ["Durée:", f"{duration_months} mois"],
        ["Statut:", contract.get_status_display() if hasattr(contract, 'get_status_display') else contract.status.title()],
        ["Date de création:", contract.created_at.strftime("%d/%m/%Y") if hasattr(contract, 'created_at') else "Non renseignée"],
    ]
    
    general_table = Table(general_data, colWidths=[40*mm, 80*mm])
    general_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(general_table)
    story.append(Spacer(1, 15))
    
    # Informations du bien
    story.append(Paragraph("BIEN IMMOBILIER", heading_style))
    
    bien_data = [
        ["Nom:", contract.property.name],
        ["Type:", contract.property.get_property_type_display() if hasattr(contract.property, 'get_property_type_display') else getattr(contract.property, 'property_type', 'Non spécifié')],
        ["Adresse:", contract.property.address],
    ]
    
    # Ajout conditionnel des champs qui peuvent exister
    if hasattr(contract.property, 'city') and contract.property.city:
        bien_data.append(["Ville:", contract.property.city])
    if hasattr(contract.property, 'area') and contract.property.area:
        bien_data.append(["Superficie:", f"{contract.property.area} m²"])
    if hasattr(contract.property, 'rooms') and contract.property.rooms:
        bien_data.append(["Nombre de pièces:", str(contract.property.rooms)])
    if hasattr(contract.property, 'is_furnished'):
        bien_data.append(["Meublé:", "Oui" if contract.property.is_furnished else "Non"])
    
    bien_table = Table(bien_data, colWidths=[40*mm, 80*mm])
    bien_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(bien_table)
    story.append(Spacer(1, 15))
    
    # Informations du locataire
    story.append(Paragraph("LOCATAIRE", heading_style))
    
    locataire_data = [
        ["Nom complet:", contract.tenant.user.get_full_name()],
        ["Email:", contract.tenant.user.email],
    ]
    
    # Ajout conditionnel des champs qui peuvent exister
    if hasattr(contract.tenant.user, 'phone') and contract.tenant.user.phone:
        locataire_data.append(["Téléphone:", contract.tenant.user.phone])
    if hasattr(contract.tenant, 'move_in_date') and contract.tenant.move_in_date:
        locataire_data.append(["Date d'entrée:", contract.tenant.move_in_date.strftime("%d/%m/%Y")])
    if hasattr(contract.tenant, 'profession') and contract.tenant.profession:
        locataire_data.append(["Situation professionnelle:", contract.tenant.profession])
    if hasattr(contract.tenant, 'guarantor_name') and contract.tenant.guarantor_name:
        locataire_data.extend([
            ["Garant:", contract.tenant.guarantor_name],
            ["Téléphone garant:", getattr(contract.tenant, 'guarantor_phone', 'Non renseigné')],
        ])
    
    locataire_table = Table(locataire_data, colWidths=[40*mm, 80*mm])
    locataire_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(locataire_table)
    story.append(Spacer(1, 15))
    
    # Informations du bailleur
    story.append(Paragraph("BAILLEUR", heading_style))
    
    # Accès au bailleur via la propriété
    landlord = getattr(contract.property, 'landlord', None) or getattr(contract.property, 'owner', None)
    
    if landlord:
        bailleur_data = [
            ["Nom:", landlord.user.get_full_name()],
            ["Email:", landlord.user.email],
        ]
        
        if hasattr(landlord.user, 'phone') and landlord.user.phone:
            bailleur_data.append(["Téléphone:", landlord.user.phone])
        if hasattr(landlord, 'get_landlord_type_display'):
            bailleur_data.append(["Type:", landlord.get_landlord_type_display()])
        elif hasattr(landlord, 'landlord_type'):
            bailleur_data.append(["Type:", landlord.landlord_type.title()])
        if hasattr(landlord, 'company') and landlord.company:
            bailleur_data.append(["Entreprise:", landlord.company])
        if hasattr(landlord, 'siret_number') and landlord.siret_number:
            bailleur_data.append(["SIRET:", landlord.siret_number])
    else:
        bailleur_data = [
            ["Information bailleur:", "Non disponible"],
        ]
    
    bailleur_table = Table(bailleur_data, colWidths=[40*mm, 80*mm])
    bailleur_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(bailleur_table)
    story.append(Spacer(1, 15))
    
    # Conditions financières
    story.append(Paragraph("CONDITIONS FINANCIÈRES", heading_style))
    
    financial_data = [
        ["Loyer mensuel:", f"{contract.monthly_rent:,.0f} FCFA"],
    ]
    
    # Ajout conditionnel des champs financiers qui peuvent exister
    if hasattr(contract, 'monthly_charges') and contract.monthly_charges:
        financial_data.append(["Charges mensuelles:", f"{contract.monthly_charges:,.0f} FCFA"])
        total_monthly = contract.monthly_rent + contract.monthly_charges
        financial_data.append(["Total mensuel:", f"{total_monthly:,.0f} FCFA"])
    else:
        financial_data.append(["Total mensuel:", f"{contract.monthly_rent:,.0f} FCFA"])
    
    if hasattr(contract, 'security_deposit') and contract.security_deposit:
        financial_data.append(["Dépôt de garantie:", f"{contract.security_deposit:,.0f} FCFA"])
    if hasattr(contract, 'agency_fees') and contract.agency_fees:
        financial_data.append(["Frais d'agence:", f"{contract.agency_fees:,.0f} FCFA"])
    if hasattr(contract, 'notice_period') and contract.notice_period:
        financial_data.append(["Préavis:", f"{contract.notice_period} mois"])
    if hasattr(contract, 'is_renewable'):
        financial_data.append(["Renouvelable:", "Oui" if contract.is_renewable else "Non"])
    
    financial_table = Table(financial_data, colWidths=[40*mm, 80*mm])
    financial_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(financial_table)
    story.append(Spacer(1, 20))
    
    # Conditions particulières
    if hasattr(contract, 'special_conditions') and contract.special_conditions:
        story.append(Paragraph("CONDITIONS PARTICULIÈRES", heading_style))
        story.append(Paragraph(contract.special_conditions, normal_style))
        story.append(Spacer(1, 20))
    
    # Signatures
    story.append(Paragraph("SIGNATURES", heading_style))
    
    signature_data = [
        ["", "Le Locataire", "Le Bailleur", "L'Agence"],
        ["Date:", "", "", timezone.now().strftime("%d/%m/%Y")],
        ["Signature:", "", "", ""],
        ["", "", "", ""],
        ["", "", "", ""],
    ]
    
    signature_table = Table(signature_data, colWidths=[30*mm, 40*mm, 40*mm, 40*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(signature_table)
    
    # Pied de page
    story.append(Spacer(1, 30))
    footer_text = "Document généré automatiquement le " + timezone.now().strftime("%d/%m/%Y à %H:%M")
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Construction du PDF
    doc.build(story)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def generate_contract_filename(contract):
    """
    Génère un nom de fichier pour le contrat
    """
    safe_contract_number = contract.contract_number.replace('/', '_').replace(' ', '_')
    tenant_name = contract.tenant.user.last_name.replace(' ', '_')
    return f"contrat_{safe_contract_number}_{tenant_name}.pdf"