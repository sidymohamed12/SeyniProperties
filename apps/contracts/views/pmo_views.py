# apps/contracts/views/pmo_views.py
"""
Vues pour le module PMO (Project Management Office)
Gestion du workflow de traitement des contrats
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from ..models import ContractWorkflow, DocumentContrat, RentalContract
from ..forms import (
    DocumentUploadForm, VisitePlanificationForm, EtatLieuxUploadForm,
    RemiseClesForm, WorkflowFilterForm, WorkflowNotesForm, WorkflowCreateForm
)
from apps.core.utils import generate_unique_reference


# ============================================================================
# CRÉATION WORKFLOW
# ============================================================================

@login_required
def workflow_create_view(request):
    """Créer un nouveau workflow PMO avec contrat en brouillon"""

    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des workflows PMO.")
        return redirect('contracts:pmo_dashboard')

    if request.method == 'POST':
        form = WorkflowCreateForm(request.POST)
        if form.is_valid():
            # Calculer la date de fin basée sur la durée
            date_debut = form.cleaned_data['date_debut_prevue']
            duree_mois = form.cleaned_data['duree_mois']
            date_fin = date_debut + relativedelta(months=duree_mois)

            # Créer le contrat en mode brouillon
            contrat = RentalContract(
                appartement=form.cleaned_data['appartement'],
                locataire=form.cleaned_data['locataire'],
                date_debut=date_debut,
                date_fin=date_fin,
                duree_mois=duree_mois,
                loyer_mensuel=form.cleaned_data['loyer_mensuel'],
                charges_mensuelles=form.cleaned_data.get('charges_mensuelles', 0),
                frais_agence=form.cleaned_data.get('frais_agence', 0),
                depot_garantie=form.cleaned_data['depot_garantie'],
                travaux_realises=form.cleaned_data.get('travaux_realises', 0),
                type_contrat_usage=form.cleaned_data.get('type_contrat_usage', 'habitation'),
                statut='brouillon',
                cree_par=request.user
            )

            # Générer le numéro de contrat
            contrat.numero_contrat = generate_unique_reference('CNT')
            contrat.save()

            # Récupérer ou créer le workflow PMO associé (le signal l'a peut-être déjà créé)
            workflow, workflow_created = ContractWorkflow.objects.get_or_create(
                contrat=contrat,
                defaults={
                    'responsable_pmo': request.user,
                    'etape_actuelle': 'verification_dossier',
                    'statut_dossier': 'en_cours',
                    'notes_pmo': form.cleaned_data.get('notes_initiales', '')
                }
            )

            # Mettre à jour les notes si le workflow existait déjà
            if not workflow_created and form.cleaned_data.get('notes_initiales'):
                workflow.notes_pmo = form.cleaned_data.get('notes_initiales', '')
                workflow.save()

            # 🆕 Créer les documents requis par défaut SEULEMENT si le workflow vient d'être créé par la vue
            # (sinon le signal l'a déjà fait)
            from apps.contracts.models import DocumentContrat

            # Vérifier si des documents existent déjà (créés par le signal)
            if workflow.documents.count() == 0:
                # Documents communs à tous les types de contrats
                documents_requis = [
                    ('piece_identite', True, "Pièce d'identité (CNI, Passeport)"),
                ]

                # Ajouter les documents selon le type de contrat
                if contrat.type_contrat_usage == 'professionnel':
                    # Contrats professionnels : NINEA et RCCM uniquement
                    documents_requis.extend([
                        ('ninea', True, "Numéro NINEA de l'entreprise"),
                        ('rccm', True, "Registre de Commerce et du Crédit Mobilier"),
                    ])
                else:
                    # Contrats d'habitation : justificatif de revenus et RIB
                    documents_requis.extend([
                        ('justificatif_revenus', True, "Bulletins de salaire (3 derniers mois)"),
                        ('rib', True, "RIB pour prélèvement automatique"),
                        ('attestation_employeur', False, "Attestation de travail"),
                        ('quittance_loyer', False, "Quittance de loyer précédent"),
                    ])

                for type_doc, obligatoire, description in documents_requis:
                    DocumentContrat.objects.create(
                        workflow=workflow,
                        type_document=type_doc,
                        obligatoire=obligatoire,
                        statut='attendu',
                        commentaire=description
                    )
                nb_docs = len(documents_requis)
            else:
                nb_docs = workflow.documents.count()

            messages.success(
                request,
                f"Workflow PMO créé avec succès pour le contrat {contrat.numero_contrat}. "
                f"Locataire: {contrat.locataire.nom_complet}. "
                f"{nb_docs} documents requis ont été ajoutés."
            )

            return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
    else:
        form = WorkflowCreateForm()

    return render(request, 'pmo/workflow_create.html', {
        'form': form,
        'title': 'Créer un nouveau workflow PMO'
    })


@login_required
def workflow_edit_view(request, workflow_id):
    """
    Modifier un workflow PMO en cours
    Permet de modifier les informations du contrat associé
    Seulement autorisé si le workflow n'est pas trop avancé
    """
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)
    contrat = workflow.contrat

    # Vérifier les permissions
    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de modifier ce workflow.")
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    # Vérifier que le workflow peut encore être modifié
    etapes_modifiables = ['verification_dossier', 'attente_facture']
    if workflow.etape_actuelle not in etapes_modifiables:
        messages.error(
            request,
            f"Impossible de modifier ce workflow : il est déjà à l'étape '{workflow.get_etape_actuelle_display()}'. "
            f"Seuls les workflows aux étapes 'Vérification dossier' et 'Attente facture' peuvent être modifiés."
        )
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    # Vérifier que le contrat est en brouillon
    if contrat.statut != 'brouillon':
        messages.error(request, "Impossible de modifier ce workflow : le contrat n'est plus en brouillon.")
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    if request.method == 'POST':
        # Pré-remplir le formulaire avec les données actuelles
        initial_data = {
            'appartement': contrat.appartement,
            'locataire': contrat.locataire,
            'date_debut_prevue': contrat.date_debut,
            'duree_mois': contrat.duree_mois,
            'type_contrat_usage': contrat.type_contrat_usage,
            'loyer_mensuel': contrat.loyer_mensuel,
            'charges_mensuelles': contrat.charges_mensuelles,
            'frais_agence': contrat.frais_agence,
            'depot_garantie': contrat.depot_garantie,
            'travaux_realises': contrat.travaux_realises,
            'notes_initiales': workflow.notes_pmo,
        }

        form = WorkflowCreateForm(request.POST, initial=initial_data)
        if form.is_valid():
            # Calculer la nouvelle date de fin
            date_debut = form.cleaned_data['date_debut_prevue']
            duree_mois = form.cleaned_data['duree_mois']
            date_fin = date_debut + relativedelta(months=duree_mois)

            # Mettre à jour le contrat
            contrat.appartement = form.cleaned_data['appartement']
            contrat.locataire = form.cleaned_data['locataire']
            contrat.date_debut = date_debut
            contrat.date_fin = date_fin
            contrat.duree_mois = duree_mois
            contrat.loyer_mensuel = form.cleaned_data['loyer_mensuel']
            contrat.charges_mensuelles = form.cleaned_data.get('charges_mensuelles', 0)
            contrat.frais_agence = form.cleaned_data.get('frais_agence', 0)
            contrat.depot_garantie = form.cleaned_data['depot_garantie']
            contrat.travaux_realises = form.cleaned_data.get('travaux_realises', 0)
            contrat.type_contrat_usage = form.cleaned_data.get('type_contrat_usage', 'habitation')
            contrat.save()

            # Mettre à jour les notes du workflow
            workflow.notes_pmo = form.cleaned_data.get('notes_initiales', '')
            workflow.save()

            messages.success(
                request,
                f"Workflow {contrat.numero_contrat} modifié avec succès."
            )

            return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
    else:
        # Pré-remplir le formulaire avec les données actuelles
        initial_data = {
            'appartement': contrat.appartement,
            'locataire': contrat.locataire,
            'date_debut_prevue': contrat.date_debut,
            'duree_mois': contrat.duree_mois,
            'type_contrat_usage': contrat.type_contrat_usage,
            'loyer_mensuel': contrat.loyer_mensuel,
            'charges_mensuelles': contrat.charges_mensuelles,
            'frais_agence': contrat.frais_agence,
            'depot_garantie': contrat.depot_garantie,
            'travaux_realises': contrat.travaux_realises,
            'notes_initiales': workflow.notes_pmo,
        }
        form = WorkflowCreateForm(initial=initial_data)

    return render(request, 'pmo/workflow_create.html', {
        'form': form,
        'title': f'Modifier le workflow {contrat.numero_contrat}',
        'workflow': workflow,
        'is_edit': True
    })


@login_required
def workflow_delete_view(request, workflow_id):
    """
    Supprimer un workflow PMO et son contrat associé
    Seulement autorisé si le workflow n'est pas trop avancé
    """
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)
    contrat = workflow.contrat

    # Vérifier les permissions
    if not request.user.is_staff:
        messages.error(request, "Vous n'avez pas l'autorisation de supprimer ce workflow.")
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    # Vérifier que le workflow peut encore être supprimé
    etapes_supprimables = ['verification_dossier', 'attente_facture']
    if workflow.etape_actuelle not in etapes_supprimables:
        messages.error(
            request,
            f"Impossible de supprimer ce workflow : il est déjà à l'étape '{workflow.get_etape_actuelle_display()}'. "
            f"Seuls les workflows aux étapes 'Vérification dossier' et 'Attente facture' peuvent être supprimés."
        )
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    # Vérifier que le contrat est en brouillon
    if contrat.statut != 'brouillon':
        messages.error(request, "Impossible de supprimer ce workflow : le contrat n'est plus en brouillon.")
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    if request.method == 'POST':
        # Sauvegarder les infos pour le message
        numero_contrat = contrat.numero_contrat
        locataire_nom = contrat.locataire.nom_complet

        # Supprimer le workflow (CASCADE supprimera aussi les documents)
        workflow.delete()

        # Supprimer le contrat
        contrat.delete()

        messages.success(
            request,
            f"Workflow et contrat {numero_contrat} (Locataire: {locataire_nom}) supprimés avec succès."
        )

        return redirect('contracts:pmo_dashboard')

    # Afficher une page de confirmation
    return render(request, 'pmo/workflow_confirm_delete.html', {
        'workflow': workflow,
        'contrat': contrat
    })


# ============================================================================
# DASHBOARD PMO
# ============================================================================

class PMODashboardView(LoginRequiredMixin, ListView):
    """Dashboard principal du module PMO"""
    model = ContractWorkflow
    template_name = 'pmo/dashboard.html'
    context_object_name = 'workflows'
    paginate_by = 20

    def get_queryset(self):
        queryset = ContractWorkflow.objects.select_related(
            'contrat__appartement__residence__proprietaire',
            'contrat__locataire',
            'responsable_pmo',
            'facture'
        ).order_by('-created_at')

        # Filtres
        search = self.request.GET.get('search')
        etape = self.request.GET.get('etape')
        statut_dossier = self.request.GET.get('statut_dossier')
        responsable = self.request.GET.get('responsable')

        if search:
            queryset = queryset.filter(
                Q(contrat__numero_contrat__icontains=search) |
                Q(contrat__locataire__nom__icontains=search) |
                Q(contrat__locataire__prenom__icontains=search) |
                Q(contrat__locataire__email__icontains=search)
            )

        if etape:
            queryset = queryset.filter(etape_actuelle=etape)

        if statut_dossier:
            queryset = queryset.filter(statut_dossier=statut_dossier)

        if responsable:
            queryset = queryset.filter(responsable_pmo_id=responsable)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Statistiques globales
        total_workflows = ContractWorkflow.objects.count()

        context['stats'] = {
            'total': total_workflows,
            'verification_dossier': ContractWorkflow.objects.filter(etape_actuelle='verification_dossier').count(),
            'attente_facture': ContractWorkflow.objects.filter(etape_actuelle='attente_facture').count(),
            'facture_validee': ContractWorkflow.objects.filter(etape_actuelle='facture_validee').count(),
            'redaction_contrat': ContractWorkflow.objects.filter(etape_actuelle='redaction_contrat').count(),
            'visite_entree': ContractWorkflow.objects.filter(etape_actuelle='visite_entree').count(),
            'remise_cles': ContractWorkflow.objects.filter(etape_actuelle='remise_cles').count(),
            'termine': ContractWorkflow.objects.filter(etape_actuelle='termine').count(),

            # Statuts dossiers
            'dossier_complet': ContractWorkflow.objects.filter(statut_dossier='complet').count(),
            'dossier_incomplet': ContractWorkflow.objects.filter(statut_dossier='incomplet').count(),
            'dossier_en_cours': ContractWorkflow.objects.filter(statut_dossier='en_cours').count(),
        }

        # Formulaire de filtres
        context['filter_form'] = WorkflowFilterForm(self.request.GET)

        # Workflows urgents (en attente depuis plus de 7 jours)
        sept_jours_avant = timezone.now() - timedelta(days=7)
        context['workflows_urgents'] = ContractWorkflow.objects.filter(
            created_at__lte=sept_jours_avant,
            etape_actuelle__in=['verification_dossier', 'attente_facture']
        ).select_related(
            'contrat__appartement__residence__proprietaire',
            'contrat__locataire'
        )[:5]

        return context


# ============================================================================
# DÉTAIL WORKFLOW
# ============================================================================

class WorkflowDetailView(LoginRequiredMixin, DetailView):
    """Vue détaillée d'un workflow PMO avec timeline"""
    model = ContractWorkflow
    template_name = 'pmo/workflow_detail.html'
    context_object_name = 'workflow'
    pk_url_kwarg = 'workflow_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = self.object

        # Documents du workflow
        context['documents'] = workflow.documents.all().order_by('type_document')

        # Documents obligatoires manquants
        docs_obligatoires = workflow.documents.filter(obligatoire=True)
        context['docs_manquants'] = docs_obligatoires.exclude(statut='verifie')

        # Historique des transitions
        context['historique'] = workflow.historique.all().order_by('-date_transition')

        # Formulaires selon l'étape
        if workflow.etape_actuelle == 'redaction_contrat':
            context['visite_form'] = VisitePlanificationForm(instance=workflow)
        elif workflow.etape_actuelle == 'visite_entree':
            context['etat_lieux_form'] = EtatLieuxUploadForm(instance=workflow)
        elif workflow.etape_actuelle == 'remise_cles':
            context['remise_form'] = RemiseClesForm(instance=workflow)

        # Formulaire de notes
        context['notes_form'] = WorkflowNotesForm(instance=workflow)

        # Peut avancer ?
        context['peut_avancer'] = workflow.peut_avancer

        # Timeline data (pour affichage visuel)
        etapes = [
            {'code': 'verification_dossier', 'label': 'Vérification dossier', 'icon': 'fa-folder-open'},
            {'code': 'attente_facture', 'label': 'Attente facture', 'icon': 'fa-file-invoice'},
            {'code': 'facture_validee', 'label': 'Facture validée', 'icon': 'fa-check-circle'},
            {'code': 'redaction_contrat', 'label': 'Rédaction contrat', 'icon': 'fa-file-signature'},
            {'code': 'visite_entree', 'label': 'Visite d\'entrée', 'icon': 'fa-home'},
            {'code': 'remise_cles', 'label': 'Remise des clés', 'icon': 'fa-key'},
            {'code': 'termine', 'label': 'Terminé', 'icon': 'fa-flag-checkered'},
        ]

        # Marquer l'étape actuelle
        etape_index = next((i for i, e in enumerate(etapes) if e['code'] == workflow.etape_actuelle), 0)
        for i, etape in enumerate(etapes):
            etape['completed'] = i < etape_index
            etape['current'] = i == etape_index
            etape['future'] = i > etape_index

        context['timeline_etapes'] = etapes

        return context


# ============================================================================
# GESTION DES DOCUMENTS
# ============================================================================

@login_required
def upload_document(request, workflow_id, document_id=None):
    """
    Upload un document pour un workflow
    Si document_id est fourni, met à jour le document existant
    Sinon, crée un nouveau document
    """
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    # Si un document_id est fourni, on met à jour ce document
    document_existant = None
    if document_id:
        document_existant = get_object_or_404(DocumentContrat, pk=document_id, workflow=workflow)

    if request.method == 'POST':
        if document_existant:
            # Mise à jour du document existant
            form = DocumentUploadForm(request.POST, request.FILES, instance=document_existant)
            # Forcer le type_document et obligatoire à leurs valeurs d'origine
            # car le champ est readonly et n'est pas modifiable
            if form.is_valid():
                document = form.save(commit=False)
                document.workflow = workflow
                document.statut = 'recu'
                document.type_document = document_existant.type_document
                document.obligatoire = document_existant.obligatoire
                document.save()

                messages.success(request, f'Document "{document.get_type_document_display()}" mis à jour avec succès.')
                return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
        else:
            # Création d'un nouveau document
            form = DocumentUploadForm(request.POST, request.FILES)

            if form.is_valid():
                document = form.save(commit=False)
                document.workflow = workflow
                document.statut = 'recu'
                document.save()

                messages.success(request, f'Document "{document.get_type_document_display()}" ajouté avec succès.')
                return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
    else:
        if document_existant:
            # Pré-remplir le formulaire avec le type de document existant
            form = DocumentUploadForm(instance=document_existant)
            # Rendre le champ type_document readonly (pas disabled car disabled n'envoie pas la valeur)
            form.fields['type_document'].widget.attrs['readonly'] = 'readonly'
            form.fields['type_document'].widget.attrs['class'] = 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 cursor-not-allowed pointer-events-none'
            # Rendre le champ obligatoire readonly aussi
            form.fields['obligatoire'].widget.attrs['disabled'] = 'disabled'
            form.fields['obligatoire'].widget.attrs['class'] = 'w-4 h-4 text-imani-primary border-gray-300 rounded cursor-not-allowed'
        else:
            form = DocumentUploadForm()

    return render(request, 'pmo/upload_document.html', {
        'form': form,
        'workflow': workflow,
        'document_existant': document_existant
    })


@login_required
def valider_document(request, document_id):
    """Valide un document (marque comme vérifié)"""
    document = get_object_or_404(DocumentContrat, pk=document_id)

    if request.method == 'POST':
        document.marquer_comme_verifie(request.user)
        messages.success(request, f'Document "{document.get_type_document_display()}" validé.')

    return redirect('contracts:pmo_workflow_detail', workflow_id=document.workflow.id)


@login_required
def refuser_document(request, document_id):
    """Refuse un document"""
    document = get_object_or_404(DocumentContrat, pk=document_id)

    if request.method == 'POST':
        commentaire = request.POST.get('commentaire', '')
        document.statut = 'refuse'
        document.commentaire = commentaire
        document.save()

        messages.warning(request, f'Document "{document.get_type_document_display()}" refusé.')

    return redirect('contracts:pmo_workflow_detail', workflow_id=document.workflow.id)


# ============================================================================
# PLANIFICATION VISITE
# ============================================================================

@login_required
def planifier_visite(request, workflow_id):
    """Planifie une visite d'entrée"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    if request.method == 'POST':
        form = VisitePlanificationForm(request.POST, instance=workflow)
        if form.is_valid():
            form.save()
            messages.success(request, 'Visite planifiée avec succès.')
            return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
    else:
        form = VisitePlanificationForm(instance=workflow)

    return render(request, 'pmo/planifier_visite.html', {
        'form': form,
        'workflow': workflow
    })


@login_required
def upload_etat_lieux(request, workflow_id):
    """Upload le rapport d'état des lieux"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    if request.method == 'POST':
        form = EtatLieuxUploadForm(request.POST, request.FILES, instance=workflow)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rapport d\'état des lieux enregistré.')
            return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
    else:
        form = EtatLieuxUploadForm(instance=workflow)

    return render(request, 'pmo/upload_etat_lieux.html', {
        'form': form,
        'workflow': workflow
    })


# ============================================================================
# RÉDACTION ET SIGNATURE DU CONTRAT
# ============================================================================

@login_required
def upload_contrat_signe(request, workflow_id):
    """Upload du contrat signé par le locataire et le bailleur"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)
    contrat = workflow.contrat

    if request.method == 'POST':
        fichier_contrat = request.FILES.get('fichier_contrat')
        signe_locataire = request.POST.get('signe_par_locataire') == 'on'
        signe_bailleur = request.POST.get('signe_par_bailleur') == 'on'

        if fichier_contrat:
            contrat.fichier_contrat = fichier_contrat
            contrat.signe_par_locataire = signe_locataire
            contrat.signe_par_bailleur = signe_bailleur

            # Si le contrat est signé par les deux parties, le passer à "actif"
            # Note: on garde "brouillon" jusqu'à la fin du workflow PMO
            # Le passage à "actif" se fera à l'étape finale
            contrat.save()

            messages.success(request, f'Contrat signé uploadé avec succès. Signatures : Locataire {"✓" if signe_locataire else "✗"} | Bailleur {"✓" if signe_bailleur else "✗"}')
            return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
        else:
            messages.error(request, 'Veuillez sélectionner un fichier.')

    return render(request, 'pmo/upload_contrat.html', {
        'workflow': workflow,
        'contrat': contrat
    })


# ============================================================================
# REMISE DES CLÉS
# ============================================================================

@login_required
def remise_cles(request, workflow_id):
    """Enregistre la remise des clés"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    if request.method == 'POST':
        form = RemiseClesForm(request.POST, instance=workflow)
        if form.is_valid():
            workflow_obj = form.save(commit=False)
            workflow_obj.cles_remises_par = request.user
            workflow_obj.save()

            messages.success(request, 'Remise des clés enregistrée avec succès.')
            return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)
    else:
        # Pré-remplir la date avec maintenant
        form = RemiseClesForm(instance=workflow)
        if not workflow.date_remise_cles:
            form.initial['date_remise_cles'] = timezone.now()

    return render(request, 'pmo/remise_cles.html', {
        'form': form,
        'workflow': workflow
    })


# ============================================================================
# ACTIONS WORKFLOW
# ============================================================================

@login_required
def passer_etape_suivante(request, workflow_id):
    """Fait avancer le workflow à l'étape suivante"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    if not workflow.peut_avancer:
        messages.error(request, 'Les conditions pour avancer ne sont pas remplies.')
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    if workflow.passer_etape_suivante():
        messages.success(request, f'Workflow passé à l\'étape : {workflow.get_etape_actuelle_display()}')
    else:
        messages.error(request, 'Impossible de faire avancer le workflow.')

    return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)


@login_required
def envoyer_finance(request, workflow_id):
    """Envoie le workflow au service Finance"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    if workflow.etape_actuelle == 'verification_dossier' and workflow.statut_dossier == 'complet':
        workflow.passer_etape_suivante()
        messages.success(request, 'Dossier envoyé au service Finance (Marie).')

        # TODO: Envoyer notification email à Marie
    else:
        messages.error(request, 'Le dossier doit être complet avant envoi à Finance.')

    return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)


@login_required
def ajouter_notes(request, workflow_id):
    """Ajoute des notes au workflow"""
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)

    if request.method == 'POST':
        form = WorkflowNotesForm(request.POST, instance=workflow)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notes ajoutées.')

    return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)


@login_required
def supprimer_document(request, workflow_id, document_id):
    """
    Supprime un document uploadé dans le workflow PMO
    Le document passe au statut 'attendu' et le fichier est supprimé
    """
    workflow = get_object_or_404(ContractWorkflow, pk=workflow_id)
    document = get_object_or_404(DocumentContrat, pk=document_id, workflow=workflow)

    if request.method == 'POST':
        # Sauvegarder le nom du type de document pour le message
        type_doc_display = document.get_type_document_display()

        # Supprimer le fichier physique s'il existe
        if document.fichier:
            try:
                import os
                if os.path.isfile(document.fichier.path):
                    os.remove(document.fichier.path)
            except Exception as e:
                messages.warning(request, f"Fichier supprimé de la base de données mais erreur lors de la suppression physique: {e}")

        # Remettre le document à l'état 'attendu' au lieu de le supprimer complètement
        # pour garder la trace dans le workflow
        document.fichier = None
        document.statut = 'attendu'
        document.verifie_par = None
        document.date_verification = None
        document.commentaire_verification = ''
        document.save()

        messages.success(request, f'Le fichier "{type_doc_display}" a été supprimé avec succès. Le document est de nouveau en attente.')
        return redirect('contracts:pmo_workflow_detail', workflow_id=workflow.id)

    # Page de confirmation
    return render(request, 'pmo/confirmer_suppression_document.html', {
        'workflow': workflow,
        'document': document
    })
