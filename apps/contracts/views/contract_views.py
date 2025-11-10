# apps/contracts/views/contract_views.py
"""
Vues CRUD pour la gestion des contrats de location
"""

from io import BytesIO
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime

from ..models import RentalContract
from ..forms import ContractRenewalForm, RentalContractForm


@login_required
def contract_list_view(request):
    """
    Vue liste des contrats ACTIFS (gestion quotidienne)
    Les nouveaux contrats sont gérés via le module PMO
    """
    # Récupérer les contrats opérationnels (SANS les brouillons qui sont dans PMO)
    contracts = RentalContract.objects.select_related(
        'appartement__residence__proprietaire',
        'locataire',
        'cree_par'
    ).exclude(
        statut='brouillon'  # Les brouillons sont gérés dans le PMO
    ).order_by('-created_at')

    # Filtres
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    show_all = request.GET.get('show_all', '')  # Pour voir tous les contrats si nécessaire

    # Option pour voir TOUS les contrats (y compris brouillons) pour admin
    if show_all == '1' and request.user.is_staff:
        contracts = RentalContract.objects.select_related(
            'appartement__residence__proprietaire',
            'locataire',
            'cree_par'
        ).order_by('-created_at')

    if search:
        contracts = contracts.filter(
            Q(numero_contrat__icontains=search) |
            Q(appartement__nom__icontains=search) |
            Q(appartement__residence__nom__icontains=search) |
            Q(locataire__nom__icontains=search) |
            Q(locataire__prenom__icontains=search) |
            Q(locataire__email__icontains=search)
        )

    if statut:
        contracts = contracts.filter(statut=statut)

    # Permissions selon le type d'utilisateur
    if not request.user.is_staff:
        # Vérifier si l'utilisateur a un tiers associé
        if hasattr(request.user, 'tiers'):
            tiers = request.user.tiers
            # Si c'est un locataire
            if tiers.type_tiers == 'locataire':
                contracts = contracts.filter(locataire=tiers)
            # Si c'est un propriétaire
            elif tiers.type_tiers == 'proprietaire':
                contracts = contracts.filter(appartement__residence__proprietaire=tiers)
            else:
                contracts = contracts.none()
        else:
            contracts = contracts.none()

    # Statistiques réelles (SANS brouillons pour la vue principale)
    all_contracts = contracts  # Base de calcul selon le filtre show_all
    total_contracts = all_contracts.count()
    stats = {
        'total': total_contracts,
        'active': all_contracts.filter(statut='actif').count(),
        'expired': all_contracts.filter(statut='expire').count(),
        'terminated': all_contracts.filter(statut='resilie').count(),
        'renewed': all_contracts.filter(statut='renouvele').count(),
    }

    # Pagination
    paginator = Paginator(contracts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'contracts': page_obj,
        'search': search,
        'statut': statut,
        'show_all': show_all,
        'statut_choices': [
            ('actif', 'Actif'),
            ('expire', 'Expiré'),
            ('resilie', 'Résilié'),
            ('renouvele', 'Renouvelé'),
        ],
        'stats': stats,
    }

    return render(request, 'contracts/list.html', context)


@login_required
def contract_detail_view(request, pk):
    """
    Vue détail d'un contrat
    """
    contract = get_object_or_404(RentalContract, pk=pk)

    # Vérification des permissions
    can_edit = False
    can_view = False

    if request.user.is_staff:
        can_edit = True
        can_view = True
    elif hasattr(request.user, 'tiers'):
        tiers = request.user.tiers
        # Le locataire peut consulter son contrat
        if contract.locataire == tiers:
            can_view = True
            can_edit = False
        # Le propriétaire peut consulter les contrats de ses biens
        elif contract.appartement.residence.proprietaire == tiers:
            can_view = True
            can_edit = False

    if not can_view:
        raise Http404("Contrat non trouvé")

    # Informations supplémentaires pour le template
    context = {
        'contract': contract,
        'can_edit': can_edit,
        'montant_total_mensuel': contract.montant_total_mensuel,
        'jours_restants': contract.jours_restants,
        'arrive_a_echeance': contract.arrive_a_echeance,
    }

    return render(request, 'contracts/detail.html', context)


@login_required
def contract_create_view(request):
    """Vue création d'un contrat"""
    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des contrats.")
        return redirect('contracts:list')

    if request.method == 'POST':
        form = RentalContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.cree_par = request.user

            # Générer le numéro de contrat s'il n'existe pas
            if not contract.numero_contrat:
                from apps.core.utils import generate_unique_reference
                contract.numero_contrat = generate_unique_reference('CNT')

            contract.save()
            messages.success(request, f"Contrat {contract.numero_contrat} créé avec succès.")
            return redirect('contracts:detail', pk=contract.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs en rouge.")
    else:
        form = RentalContractForm()

    context = {
        'form': form,
        'title': 'Nouveau contrat'
    }

    return render(request, 'contracts/form.html', context)


@login_required
def contract_edit_view(request, pk):
    """
    Vue modification d'un contrat
    """
    contract = get_object_or_404(RentalContract, pk=pk)

    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier des contrats.")
        return redirect('contracts:detail', pk=pk)

    if request.method == 'POST':
        form = RentalContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            contract = form.save()
            messages.success(request, f"Contrat {contract.numero_contrat} modifié avec succès.")
            return redirect('contracts:detail', pk=contract.pk)
        else:
            messages.error(request, "Erreur dans le formulaire. Veuillez corriger les champs en rouge.")
    else:
        form = RentalContractForm(instance=contract)

    context = {
        'form': form,
        'contract': contract,
        'title': f'Modifier le contrat {contract.numero_contrat}'
    }

    return render(request, 'contracts/form.html', context)


@login_required
def contract_delete_view(request, pk):
    """
    Vue suppression d'un contrat
    """
    contract = get_object_or_404(RentalContract, pk=pk)

    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer des contrats.")
        return redirect('contracts:detail', pk=pk)

    if request.method == 'POST':
        contract_number = contract.numero_contrat
        contract.delete()
        messages.success(request, f"Contrat {contract_number} supprimé avec succès.")
        return redirect('contracts:list')

    context = {
        'contract': contract,
    }

    return render(request, 'contracts/confirm_delete.html', context)


@login_required
def contract_renew_view(request, pk):
    """
    Vue pour renouveler un contrat
    """
    contract = get_object_or_404(RentalContract, pk=pk)

    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de renouveler des contrats.")
        return redirect('contracts:detail', pk=pk)

    if request.method == 'POST':
        form = ContractRenewalForm(request.POST, instance=contract)
        if form.is_valid():
            # Créer un nouveau contrat basé sur l'ancien
            new_contract = RentalContract.objects.create(
                appartement=contract.appartement,
                locataire=contract.locataire,
                date_debut=form.cleaned_data['date_debut'],
                date_fin=form.cleaned_data['date_fin'],
                loyer_mensuel=form.cleaned_data['loyer_mensuel'],
                charges_mensuelles=form.cleaned_data.get('charges_mensuelles', contract.charges_mensuelles),
                depot_garantie=contract.depot_garantie,
                type_contrat=contract.type_contrat,
                statut='actif',
                cree_par=request.user
            )

            # Marquer l'ancien contrat comme renouvelé
            contract.statut = 'renouvele'
            contract.save()

            messages.success(request, f"Contrat renouvelé avec succès. Nouveau contrat: {new_contract.numero_contrat}")
            return redirect('contracts:detail', pk=new_contract.pk)
        else:
            messages.error(request, "Erreur dans le formulaire de renouvellement.")
    else:
        form = ContractRenewalForm(instance=contract)

    context = {
        'form': form,
        'contract': contract,
        'title': f'Renouveler le contrat {contract.numero_contrat}'
    }

    return render(request, 'contracts/renew.html', context)


@login_required
def contract_terminate_view(request, pk):
    """
    Vue pour résilier un contrat
    """
    contract = get_object_or_404(RentalContract, pk=pk)

    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de résilier des contrats.")
        return redirect('contracts:detail', pk=pk)

    if request.method == 'POST':
        date_resiliation = request.POST.get('date_resiliation')
        motif = request.POST.get('motif', '')

        if date_resiliation:
            contract.statut = 'resilie'
            contract.date_resiliation = datetime.strptime(date_resiliation, '%Y-%m-%d').date()
            contract.motif_resiliation = motif
            contract.save()

            # Libérer l'appartement
            appartement = contract.appartement
            appartement.statut_occupation = 'libre'
            appartement.save()

            messages.success(request, f"Contrat {contract.numero_contrat} résilié avec succès.")
            return redirect('contracts:detail', pk=pk)
        else:
            messages.error(request, "Date de résiliation requise.")

    context = {
        'contract': contract,
    }

    return render(request, 'contracts/terminate.html', context)


def generate_professional_contract_pdf(contrat):
    """Génère un PDF de contrat professionnel conforme au modèle IMANY"""
    from reportlab.platypus import HRFlowable, KeepTogether, PageBreak, Image
    from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    import os
    import requests
    import tempfile
    from django.conf import settings

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
        topMargin=25*mm,  # Augmenté pour laisser place au logo
        bottomMargin=25*mm,  # Augmenté pour laisser place au footer
    )

    elements = []
    styles = getSampleStyleSheet()

    # Couleurs IMANY
    IMANY_BLUE = colors.HexColor('#23456B')
    IMANY_TERRACOTTA = colors.HexColor('#A25946')

    # Styles personnalisés
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.black,
    )

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=IMANY_BLUE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=15,
        borderWidth=2,
        borderColor=IMANY_BLUE,
        borderPadding=8,
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=IMANY_TERRACOTTA,
        spaceBefore=12,
        spaceAfter=6,
    )

    normal_text_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14,
    )

    bold_text_style = ParagraphStyle(
        'BoldText',
        parent=normal_text_style,
        fontName='Helvetica-Bold',
    )

    # Titre du contrat dans un cadre (le logo est dans l'en-tête de page)
    title_data = [[Paragraph("CONTRAT DE LOCATION PROFESSIONNEL", title_style)]]
    title_table = Table(title_data, colWidths=[170*mm])
    title_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, IMANY_BLUE),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 20))

    # ENTRE (Le Bailleur)
    elements.append(Paragraph("<b>ENTRE</b>", bold_text_style))
    elements.append(Spacer(1, 10))

    bailleur_text = (
        f"La société <b>IMANY SN</b>, Société Unipersonnelle à Responsabilité Limitée (SUARL) au capital social "
        f"d'Un Million (1.000.000) de Francs CFA, ayant son siège social à Dakar-Sénégal, Liberté 4 "
        f"Dieuppeul, immatriculée au Registre du Commerce et du Crédit Mobilier de Dakar sous le "
        f"numéro SN.DKR.2024. B.18099."
    )
    elements.append(Paragraph(bailleur_text, normal_text_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "Représentée par Madame Rokhaya BA agissant en qualité de gérante dûment habilitée aux "
        "fins des présentes.",
        normal_text_style
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph('Ci-après désignée « le Bailleur » D\'une part,', bold_text_style))
    elements.append(Spacer(1, 15))

    # ET (Le Preneur)
    elements.append(Paragraph("<b>ET :</b>", bold_text_style))
    elements.append(Spacer(1, 10))

    locataire = contrat.locataire
    preneur_text = ""

    if locataire:
        # Nom de la société/entité - utiliser nom_complet du Tiers
        nom_entite = locataire.nom_complet

        preneur_text = (
            f"La Société « <b>{nom_entite}</b> », SAS, "
            f"ayant son siège social à Dakar, Sénégal "
            f"{locataire.adresse if locataire.adresse else '[ADRESSE]'}, "
            f"immatriculée au Registre du Commerce et du Crédit Mobilier de Dakar sous le numéro [NINEA]"
        )

    elements.append(Paragraph(preneur_text, normal_text_style))
    elements.append(Spacer(1, 8))

    # Représentant
    representant_text = (
        f"Représentée par Monsieur/Madame [NOM DU REPRÉSENTANT] titulaire de la CNI [NUMÉRO CNI] "
        f"demeurant {locataire.adresse if locataire and locataire.adresse else '[ADRESSE]'} agissant "
        f"en qualité de [QUALITÉ], dûment habilité(e) aux fins des présentés."
    )
    elements.append(Paragraph(representant_text, normal_text_style))

    if locataire and locataire.email:
        elements.append(Paragraph(f"Email : {locataire.email}", normal_text_style))
    if locataire and locataire.telephone:
        elements.append(Paragraph(f"Téléphone : {locataire.telephone}", normal_text_style))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph('Désignée « Le Preneur »', bold_text_style))
    elements.append(Spacer(1, 15))

    elements.append(Paragraph("Ceci exposé, il a été arrêté et convenu ce qui suit :", normal_text_style))
    elements.append(Spacer(1, 15))

    # Article 1er – Objet du contrat
    elements.append(Paragraph("<b>Article 1er – Objet du contrat - bail à usage professionnel</b>", section_title_style))

    appartement = contrat.appartement
    residence = appartement.residence if appartement else None

    bien_description = f"{appartement.get_type_bien_display()} {appartement.nom}" if appartement else "[TYPE BIEN]"
    residence_nom = residence.nom if residence else "[RÉSIDENCE]"

    article1_text = (
        f"1.1. Le présent contrat détermine les conditions suivant lesquelles le Bailleur consent à louer au "
        f"Preneur qui accepte la location {bien_description} de la "
        f"résidence {residence_nom}."
    )
    elements.append(Paragraph(article1_text, normal_text_style))
    elements.append(Spacer(1, 8))

    article1_2 = (
        "1.2. Le présent contrat constitue l'intégralité des accords conclus entre les Parties. Il prévaut sur "
        "toutes les propositions, négociations écrites ou orales intervenues entre les parties ou sur "
        "toutes autres communications émanant des contractants et qui se rapportent à l'objet."
    )
    elements.append(Paragraph(article1_2, normal_text_style))
    elements.append(Spacer(1, 12))

    # Article 2 – Désignation des lieux
    elements.append(Paragraph("<b>Article 2 – Désignation des lieux :</b>", section_title_style))

    elements.append(Paragraph(
        "2.1. Le Bailleur loue au Preneur les locaux dont la description est la suivante :",
        normal_text_style
    ))

    commodites_text = ""
    if appartement:
        commodites = []
        if appartement.nb_chambres:
            commodites.append(f"{appartement.nb_chambres} chambre(s)")
        if appartement.nb_sdb:
            commodites.append(f"{appartement.nb_sdb} salle(s) de bain")
        if appartement.superficie:
            commodites.append(f"{appartement.superficie} m²")
        commodites_text = ", ".join(commodites) if commodites else "COMMODITÉS"
    else:
        commodites_text = "COMMODITÉS"

    elements.append(Paragraph(f"<b>{commodites_text}</b>", normal_text_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "2.2. Le Preneur déclare connaître parfaitement les lieux pour les avoir visités et consentis les "
        "occuper dans l'état où ils se trouvent.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 3 – Destination
    elements.append(Paragraph("<b>Article 3 – Destination :</b>", section_title_style))
    elements.append(Paragraph(
        "3.0. La présente location est consentie exclusivement à usage professionnel. Aucune autre "
        "activité n'est tolérée dans et aux abords des surfaces louées ci-dessus désignés au Preneur qui les "
        "accepte aux conditions définies par le présent contrat.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 4 – Charges et conditions
    elements.append(Paragraph("<b>Article 4 – Charges et conditions :</b>", section_title_style))
    elements.append(Paragraph(
        "4.1. Les parties consentent et acceptent le présent bail aux conditions ci-après stipulées.",
        normal_text_style
    ))
    elements.append(Spacer(1, 8))

    # Calcul des montants
    loyer_base = contrat.loyer_mensuel
    tva = loyer_base * Decimal('0.18')
    total_ttc = loyer_base + tva

    elements.append(Paragraph(f"4.1.1 – Loyer de base : {loyer_base:,.0f} FCFA", normal_text_style))
    elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- TVA : 18% : {tva:,.0f} FCFA à la charge du locataire", normal_text_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Soit un montant TOTAL de : <b>{total_ttc:,.0f} Francs CFA</b>", normal_text_style))
    elements.append(Spacer(1, 8))

    paiement_text = (
        "4.1.2. Le loyer est mensuel et payable au plus tard le cinq (5) de chaque mois à IMANY SN, par "
        "chèque au nom de IMANY SN ou directement sur son compte bancaire N° SN 01001-"
        "006142924101 – 93 domicilié à CORIS BANK."
    )
    elements.append(Paragraph(paiement_text, normal_text_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "4.1.3. Le Preneur ne peut faire aucune retenue sur les loyers ou charges sous aucun prétexte.",
        normal_text_style
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("4.1.4. Tout mois commencé est dû en entier.", normal_text_style))
    elements.append(Spacer(1, 8))

    # Durée
    elements.append(Paragraph("4.2. Durée", bold_text_style))
    elements.append(Spacer(1, 8))

    date_debut = contrat.date_debut.strftime("%d / %m/ %Y") if contrat.date_debut else "XX / XX / XXXX"

    duree_text = (
        "4.2.1. La présente location est consentie et acceptée pour une durée déterminée de 03 ans "
        f"renouvelable par tacite reconduction. Elle prend effet à partir du {date_debut}."
    )
    elements.append(Paragraph(duree_text, normal_text_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "4.2.2. En cas de résiliation du bail, la partie qui en prend l'initiative prévient l'autre partie avant "
        "l'échéance du bail par courrier ou notification par tout moyen permettant d'établir la réception "
        "effective par le destinataire.",
        normal_text_style
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "4.2.3. Chacune des parties pourra en demander la résiliation à la charge d'en prévenir l'autre de "
        "son intention à cet égard par lettre écrite (03) Trois mois par le locataire et Six (6) mois par le "
        "bailleur au moins avant l'échéance du terme fixé pour la durée du présent bail.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 5 - Caution
    elements.append(Paragraph("<b>Article 5 – Caution :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    depot_garantie = contrat.depot_garantie if contrat.depot_garantie else 0
    elements.append(Paragraph(f"5.1. Le Preneur verse à titre de caution la somme de {depot_garantie:,.0f} Francs CFA.", normal_text_style))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("5.2. La caution ne peut être considérée comme une avance sur loyer.", normal_text_style))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "5.3. La caution est remboursée au Preneur dans un délai de quinze (15) jours à compter de la "
        "résiliation du contrat sous réserve du respect des stipulations du paragraphe 5.4 du présent article.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "5.5. Le Preneur autorise le Bailleur à prélever sur cette caution toute somme correspondante aux "
        "dettes qu'il aurait pu contracter tels que notamment les frais de remise en état des locaux.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "5.6. En cas d'indemnisation par le Preneur pour quelque manquement que ce soit, le Bailleur peut, "
        "sur la base d'une compensation, prélever sur la caution toutes somme dues au titre des dommages & "
        "intérêts à concurrence du montant fixé pour ces dommages-intérêts. Si la caution ne couvre pas tout "
        "le montant, le reliquat est dû par le Preneur.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 6 - Abonnement Eau, Electricité
    elements.append(Paragraph("<b>Article 6 – Abonnement Eau, Electricité :</b>", section_title_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "6.0. Les abonnements d'eau et d'électricité sont à la charge du preneur.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 7 - Charges et conditions d'utilisation
    elements.append(Paragraph("<b>Article 7 – Charges et conditions d'utilisation :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "7.1. Le Preneur ne peut faire aucun aménagement ou transformation des locaux sans l'autorisation de "
        "plein droit au Bailleur en fin de bail sans aucune obligation de versement d'une indemnité à la charge "
        "de celui-ci.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "7.2. Le Preneur s'interdit, ainsi que ses ayants-droits et personnes dont il répond, les gaspillages, "
        "les nuisances ou les activités illégales dans les locaux loués.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "7.3. Aucune stipulation du présent contrat n'accorde au Preneur le droit d'utiliser la propriété à une "
        "fin autre que celle décrite ci-dessus.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 8 - Sous location - Cession
    elements.append(Paragraph(
        "<b>Article 8 – Sous location – Cession : préalable et écrite du Bailleur. "
        "Tous les aménagements, embellissements ou améliorations</b>",
        section_title_style
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "8.1. Le Preneur ne peut sous-louer qu'avec l'accord exprès et écrit du bailleur et après avoir notifié "
        "le nom du sous locataire avec indication du taux du sous loyer sous peine de résiliation du bail principal.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "8.2. Le Preneur ne peut céder le contrat de location qu'avec l'accord écrit du bailleur et après lui avoir "
        "notifié le nom du cessionnaire.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 9 - Responsabilité
    elements.append(Paragraph("<b>Article 9– Responsabilité en cas de vol, perte ou dégradations</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "9.1. En cas de vol par effraction dans les locaux loués, le Preneur ne peut intenter aucune action contre "
        "le Bailleur qui ne peut être tenu pour responsable des vols commis chez les locataires.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "9.2. Le Preneur répond des dégradations ou des pertes arrivant pendant sa jouissance, à moins qu'il ne "
        "prouve qu'elles aient eu lieu sans sa faute. Il est tenu des dégradations et pertes qui arrivent par le "
        "fait de ses ayants-droits ou des personnes dont il répond.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 10 - Obligations du Bailleur
    elements.append(Paragraph("<b>Article 10 – Obligations du Bailleur</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "10.1. Le Bailleur remet au Preneur le logement en bon état d'usage. Il établit lors de la remise des clefs, "
        "un état des lieux contradictoire faite au bailleur.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "10.2. Le Bailleur remet une quittance au Preneur lors du paiement du loyer et lui délivre un reçu à chaque "
        "fois que le locataire effectue un paiement.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "10.3. Le Bailleur n'apporte au bien loué aucun changement de son seul gré.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "10.4. Le Bailleur garantit le Preneur contre tous les troubles de jouissance qui relèvent de son fait ou "
        "de celui de ses ayants droits.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "10.5. Le Bailleur garantit pour tous les vices ou défauts de la chose qui en empêche un usage normal, alors "
        "même qu'il ne les a pas connus lors de la conclusion du bail.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "10.6. Le bailleur procède, à ses frais, dans les locaux donnés à bail, à toutes les grosses réparations "
        "devenues nécessaires et urgentes. Les grosses réparations s'entendent comme étant celles qui concernent "
        "les gros murs, les voutes, les poutres, les toitures, les murs de soutènement, les murs de clôture, "
        "les fosses septiques.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 11 - Obligations du Preneur
    elements.append(PageBreak())
    elements.append(Paragraph("<b>Article 11 – Obligations du Preneur :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "11.1. Le Preneur paie le loyer et les charges récupérables aux termes convenus ; en cas de pluralité "
        "de locataires, ceux-ci sont tenus solidairement de toutes les obligations du bail.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.2. Le Preneur est tenu d'user paisiblement des locaux loués en respectant leur destination telle "
        "que définie dans le présent contrat.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.3. Le Preneur est responsable des dégradations ou des pertes survenues au cours du bail.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.4. Le Preneur prend à sa charge l'entretien courant du logement et l'ensemble des réparations "
        "lui incombant.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.5. Le Preneur est tenu de ne faire aucun changement de distribution ou transformation sans l'accord "
        "préalable et écrit du propriétaire sous peine de remise en état des locaux aux frais du locataire ou "
        "de résiliation anticipée du bail suivant la gravité de l'infraction.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.6. Le Preneur informe immédiatement le propriétaire ou son représentant de tous désordres, dégradations, "
        "sinistrés survenant dans les lieux loués.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.7. Le Preneur laisse exécuter sans indemnité tous les travaux nécessaires à la remise en état ou à "
        "l'amélioration des lieux loués et des parties communes.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.8. Le Preneur, en cas de vente ou de nouvelle location régulière, laisse visiter le logement, pendant "
        "la durée du préavis. Les deux parties conviennent ensemble des horaires de visites.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.9. Le Preneur respecte le règlement de l'immeuble, de la copropriété, notamment en ce qui concerne la "
        "destination dès l'immeuble, la jouissance et l'usager de parties privatives et communes, ainsi que les "
        "décisions de la copropriété concernant l'usager de l'immeuble.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.10. Le Preneur fait enregistrer son contrat de location auprès du service des impôts et domaines, "
        "les frais y afférents lui incombent.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "11.11. Le Preneur établit, par ses soins, un état des lieux contradictoire lors de la remise des clefs "
        "en fin de bail.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 12 - Travaux
    elements.append(Paragraph("<b>Article 12 – Travaux</b>", section_title_style))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "12.1. Tous travaux ou ouvrages réalisés par le Preneur requièrent obligatoirement l'autorisation du Bailleur.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 13 - Clause résolutoire
    elements.append(Paragraph("<b>Article 13 – Clause résolutoire :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "13.1. À défaut de paiement au terme convenu de tout ou partie du loyer, des charges et 30 jours après "
        "un commandement de payer demeuré infructueux, la présente location est résiliée de plein droit sur "
        "initiative du Bailleur.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "13.2. Le Preneur, déchu de ses droits locatifs qui refuse de restituer les lieux, peut être expulsé sur "
        "simple ordonnance du juge des référés, exécutoire par provision nonobstant appel.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 14 - Clause pénale
    elements.append(Paragraph("<b>Article 14 – Clause pénale :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "14.1. En cas de non-paiement du loyer ou de ses accessoires et dès le premier acte d'huissier, le locataire "
        "doit payer, en sus des frais de recouvrement et sans préjudice de toute autre charge émanant d'une "
        "condamnation judiciaire, une indemnité égale à 5% de la totalité des sommes dues au Bailleur. L'emplacement "
        "à l'exécution d'une obligation monétaire ne peut être constitutif d'un cas de force majeure.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 15 - Données à caractère Personnel
    elements.append(Paragraph("<b>Article 15 – Données à caractère Personnel</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "15.1. Les données à caractère personnel recueillies par le Bailleur auprès du Preneur font l'objet d'un "
        "traitement informatique ou analogique destiné à assurer le classement et la régularité des informations "
        "relatives au Preneur.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "15.2. Seules les personnes habilitées ont accès aux données à caractère personnel du Preneur faisant "
        "l'objet de traitement.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "15.3. Conformément à la loi n° 2008-12 relative à la protection des données à caractère personnel, le "
        "Preneur bénéficie d'un droit d'accès et de rectification aux informations le concernant. Il peut exercer "
        "ce droit en s'adressant directement au Bailleur, par courrier postal ou électronique à l'adresse suivante : "
        "contact@imany.sn.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 16 - Modification
    elements.append(Paragraph("<b>Article 16 – Modification – Interprétation du contrat</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "16.1. Le présent contrat ne peut être modifié que par avenant signé par les Parties.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "16.2. Dans la mesure du possible, les dispositions du présent contrat sont interprétées pour en favoriser "
        "l'application. Si une disposition du présent contrat est invalidée par le tribunal Compétent, il est de "
        "l'intention des parties que les autres dispositions du contrat demeurent applicables.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 17 - Droit applicable
    elements.append(Paragraph("<b>Article 17– Droit applicable – Litiges :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "17.1. Le présent contrat est soumis aux dispositions pertinentes de l'Acte Uniforme relatif au Droit "
        "Commercial Général de l'OHADA et du Code des Obligations Civiles et Commerciales du Sénégal.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "17.2. Tout différend se rapportant à la validité, la caducité, la nullité, l'interprétation, l'exécution, "
        "l'inexécution, la prorogation, l'interruption, la résiliation ou la résolution du présent contrat est soumis, "
        "à défaut d'un règlement à l'amiable entre les Parties, à la juridiction compétente dans le ressort duquel "
        "se trouve l'immeuble.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 18 - Élection de domicile
    elements.append(Paragraph("<b>Article 18 – Élection de domicile :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "18.1. Pour l'exécution des obligations visées au présent contrat, le Bailleur fait élection de domicile "
        "en sa demeure et le Preneur dans les lieux loués.",
        normal_text_style
    ))
    elements.append(Spacer(1, 12))

    # Article 19 - Langue du contrat
    elements.append(Paragraph("<b>Article 19 – Langue du contrat :</b>", section_title_style))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(
        "19.1. Les présents contrats ainsi que tous les documents qui y sont attachés sont rédigés dans la langue française.",
        normal_text_style
    ))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "19.2. Si pour la commodité de l'un des parties, le document contractuel était rédigé en langue étrangère, "
        "cette version n'aurait qu'une valeur informative, seule la version en langue française fait foi.",
        normal_text_style
    ))
    elements.append(Spacer(1, 20))

    # Fait à Dakar
    date_signature = contrat.date_debut.strftime("%d / %m / %Y") if contrat.date_debut else "XX / XX / XXXX"
    elements.append(Paragraph(
        f"Fait en Quatre (04) exemplaires originaux, À Dakar, le {date_signature}",
        normal_text_style
    ))
    elements.append(Spacer(1, 30))

    # Table de signatures
    signature_data = [
        [
            Paragraph("<b>LE BAILLEUR</b><br/>(Signature précédée de la mention<br/>manuscrite « lu et approuvé »)", normal_text_style),
            Paragraph("<b>LE LOCATAIRE</b><br/>(Signature précédée de la mention<br/>manuscrite « lu et approuvé »)", normal_text_style)
        ],
        ["", ""]  # Espace pour les signatures
    ]

    signature_table = Table(signature_data, colWidths=[85*mm, 85*mm], rowHeights=[None, 40*mm])
    signature_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(signature_table)

    # Construire le PDF avec en-tête et pied de page sur chaque page
    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    pdf = buffer.getvalue()
    buffer.close()

    # Nettoyer le fichier temporaire du logo
    if logo_temp_path and os.path.exists(logo_temp_path):
        try:
            os.unlink(logo_temp_path)
        except:
            pass  # Ignorer les erreurs de suppression

    return pdf


def generate_contract_pdf(contrat):
    """Génère le PDF d'un contrat - détecte le type et appelle le bon générateur"""
    # Si c'est un contrat professionnel, utiliser le générateur spécifique
    if hasattr(contrat, 'type_contrat_usage') and contrat.type_contrat_usage == 'professionnel':
        return generate_professional_contract_pdf(contrat)

    # Sinon, utiliser le générateur standard
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )
    elements = []

    # Styles
    styles = getSampleStyleSheet()

    # Style titre - Couleur IMANY primaire
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#23456b'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Style sous-titre - Couleur IMANY secondaire
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#a25946'),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    # Style section
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#23456b'),
        spaceAfter=8,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )

    # En-tête IMANY
    header_text = "IMANY SN. NINEA /011195816/ RCCM/ SN DKR 2024 B 18099<br/>Allées Khalifa Ababacar Sy, Liberté 4, Dakar, Sénégal : 33 858 17 59"
    elements.append(Paragraph(header_text, ParagraphStyle('Header', parent=normal_style, alignment=TA_CENTER, fontSize=9)))
    elements.append(Spacer(1, 20))

    # Titre
    elements.append(Paragraph("CONTRAT DE LOCATION", title_style))
    elements.append(Paragraph(f"N° {contrat.numero_contrat}", subtitle_style))
    elements.append(Spacer(1, 20))

    # Tableau principal des parties
    parties_data = [
        [Paragraph("<b>PROPRIÉTAIRE</b>", section_style), Paragraph("<b>LOCATAIRE</b>", section_style)]
    ]

    proprietaire = contrat.appartement.residence.proprietaire if contrat.appartement and contrat.appartement.residence else None

    # Info proprietaire
    prop_info = ""
    if proprietaire:
        prop_info = f"<b>{proprietaire.nom_complet}</b><br/>"
        if proprietaire.adresse:
            prop_info += f"{proprietaire.adresse}<br/>"
        if proprietaire.telephone:
            prop_info += f"Tél: {proprietaire.telephone}<br/>"
        if proprietaire.email:
            prop_info += f"Email: {proprietaire.email}"

    # Info locataire
    loc_info = ""
    if contrat.locataire:
        loc_info = f"<b>{contrat.locataire.nom_complet}</b><br/>"
        if contrat.locataire.adresse:
            loc_info += f"{contrat.locataire.adresse}<br/>"
        if contrat.locataire.telephone:
            loc_info += f"Tél: {contrat.locataire.telephone}<br/>"
        if contrat.locataire.email:
            loc_info += f"Email: {contrat.locataire.email}"

    parties_data.append([
        Paragraph(prop_info, normal_style),
        Paragraph(loc_info, normal_style)
    ])

    parties_table = Table(parties_data, colWidths=[85*mm, 85*mm])
    parties_table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        # Corps
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 1), (-1, -1), 10),
        ('RIGHTPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    elements.append(parties_table)
    elements.append(Spacer(1, 20))

    # Section: BIEN LOUÉ
    elements.append(Paragraph("BIEN LOUÉ", section_style))

    bien_data = [
        ["Description", "Détails"],
        ["Résidence", contrat.appartement.residence.nom if contrat.appartement else ""],
        ["Appartement", contrat.appartement.nom if contrat.appartement else ""],
        ["Type", contrat.appartement.get_type_bien_display() if contrat.appartement else ""],
        ["Adresse", f"{contrat.appartement.residence.adresse}, {contrat.appartement.residence.ville}" if contrat.appartement and contrat.appartement.residence else ""],
    ]

    bien_table = Table(bien_data, colWidths=[50*mm, 120*mm])
    bien_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8fafc')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(bien_table)
    elements.append(Spacer(1, 20))

    # Section: DURÉE DU CONTRAT
    elements.append(Paragraph("DURÉE DU CONTRAT", section_style))

    duree_data = [
        ["Période", "Date"],
        ["Date de début", contrat.date_debut.strftime("%d/%m/%Y")],
        ["Date de fin", contrat.date_fin.strftime("%d/%m/%Y")],
        ["Durée", f"{((contrat.date_fin - contrat.date_debut).days // 30)} mois"],
    ]

    duree_table = Table(duree_data, colWidths=[85*mm, 85*mm])
    duree_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8fafc')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(duree_table)
    elements.append(Spacer(1, 20))

    # Section: CONDITIONS FINANCIÈRES
    elements.append(Paragraph("CONDITIONS FINANCIÈRES", section_style))

    montant_total = contrat.montant_total_mensuel

    finance_data = [
        ["Description", "Montant"],
        ["Loyer mensuel", f"{contrat.loyer_mensuel:,.0f} FCFA"],
        ["Charges mensuelles", f"{contrat.charges_mensuelles:,.0f} FCFA" if contrat.charges_mensuelles else "0 FCFA"],
        ["TOTAL MENSUEL", f"{montant_total:,.0f} FCFA"],
        ["", ""],
        ["Dépôt de garantie", f"{contrat.depot_garantie:,.0f} FCFA" if contrat.depot_garantie else "0 FCFA"],
        ["Frais d'agence", f"{contrat.frais_agence:,.0f} FCFA" if contrat.frais_agence else "0 FCFA"],
    ]

    finance_table = Table(finance_data, colWidths=[85*mm, 85*mm])
    finance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#23456b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8fafc')),

        # Total mensuel en gras avec fond
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#dcfce7')),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 11),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#a25946')),

        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(finance_table)
    elements.append(Spacer(1, 30))

    # Signatures
    elements.append(Paragraph("SIGNATURES", section_style))
    elements.append(Spacer(1, 10))

    signature_data = [
        [Paragraph("<b>Le Propriétaire</b>", ParagraphStyle('SigTitle', parent=normal_style, alignment=TA_CENTER)),
         Paragraph("<b>Le Locataire</b>", ParagraphStyle('SigTitle', parent=normal_style, alignment=TA_CENTER))],
        ["", ""],
        ["", ""],
        ["", ""],
        ["Date: _______________", "Date: _______________"],
    ]

    signature_table = Table(signature_data, colWidths=[85*mm, 85*mm], rowHeights=[15*mm, 20*mm, 20*mm, 20*mm, 15*mm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(signature_table)
    elements.append(Spacer(1, 20))

    # Pied de page
    footer_text = (
        "<i>Ce contrat est régi par les lois en vigueur au Sénégal.</i><br/>"
        "IMANY by Seyni Properties - Liberté 4, Allées Khalifa Ababacar Sy, 11000, Dakar - Sénégal<br/>"
        "Tél: +221 77 590 84 84 - Email: contact@imany.sn - Web: www.seyniproperties.sn"
    )

    elements.append(Paragraph(
        footer_text,
        ParagraphStyle('Footer', parent=normal_style,
                      fontSize=8, textColor=colors.HexColor('#94a3b8'),
                      alignment=TA_CENTER)
    ))

    # Générer le PDF
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    return pdf


@login_required
def contract_download_pdf(request, pk):
    """Générer et télécharger le PDF du contrat"""
    contrat = get_object_or_404(RentalContract, pk=pk)

    pdf = generate_contract_pdf(contrat)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contrat_{contrat.numero_contrat}.pdf"'

    return response


@login_required
def contract_preview_pdf(request, pk):
    """Prévisualiser le PDF du contrat dans le navigateur"""
    contrat = get_object_or_404(RentalContract, pk=pk)

    pdf = generate_contract_pdf(contrat)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="contrat_{contrat.numero_contrat}_preview.pdf"'

    return response


@login_required
def contract_print_view(request, pk):
    """
    Affiche le contrat dans une vue imprimable (HTML)
    """
    contract = get_object_or_404(RentalContract, pk=pk)
    context = {
        'contract': contract,
        'print_mode': True,
    }
    return render(request, 'contracts/detail.html', context)
