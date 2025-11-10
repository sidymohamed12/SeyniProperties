"""
Vues pour la gestion des tiers
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Tiers, TiersBien
from .forms import TiersForm, TiersBienForm, TiersSearchForm


@login_required
def tiers_liste(request):
    """
    Vue pour afficher la liste des tiers avec recherche et filtres
    """
    # Récupérer tous les tiers
    tiers_list = Tiers.objects.select_related('cree_par').annotate(
        nb_biens=Count('biens_lies')
    )

    # Formulaire de recherche
    search_form = TiersSearchForm(request.GET)

    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        type_tiers = search_form.cleaned_data.get('type_tiers')
        statut = search_form.cleaned_data.get('statut')
        ville = search_form.cleaned_data.get('ville')

        # Filtrage par recherche textuelle
        if search:
            tiers_list = tiers_list.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(email__icontains=search) |
                Q(telephone__icontains=search) |
                Q(reference__icontains=search)
            )

        # Filtrage par type
        if type_tiers:
            tiers_list = tiers_list.filter(type_tiers=type_tiers)

        # Filtrage par statut
        if statut:
            tiers_list = tiers_list.filter(statut=statut)

        # Filtrage par ville
        if ville:
            tiers_list = tiers_list.filter(ville__icontains=ville)

    # Pagination
    paginator = Paginator(tiers_list, 25)  # 25 tiers par page
    page_number = request.GET.get('page')
    tiers = paginator.get_page(page_number)

    # Statistiques
    stats = {
        'total': Tiers.objects.count(),
        'actifs': Tiers.objects.filter(statut='actif').count(),
        'proprietaires': Tiers.objects.filter(type_tiers='proprietaire').count(),
        'locataires': Tiers.objects.filter(type_tiers='locataire').count(),
        'prestataires': Tiers.objects.filter(type_tiers='prestataire').count(),
    }

    context = {
        'tiers': tiers,
        'search_form': search_form,
        'stats': stats,
        'page_title': 'Gestion des Tiers',
    }

    return render(request, 'tiers/tiers_liste.html', context)


@login_required
def tiers_detail(request, pk):
    """
    Vue pour afficher les détails d'un tiers
    """
    tiers = get_object_or_404(
        Tiers.objects.select_related('cree_par', 'modifie_par'),
        pk=pk
    )

    # Récupérer les biens liés
    biens_lies = TiersBien.objects.filter(tiers=tiers).select_related(
        'appartement',
        'residence',
        'cree_par'
    ).order_by('-date_debut')

    context = {
        'tiers': tiers,
        'biens_lies': biens_lies,
        'page_title': f'Tiers - {tiers.nom_complet}',
    }

    return render(request, 'tiers/tiers_detail.html', context)


@login_required
def tiers_ajouter(request):
    """
    Vue pour ajouter un nouveau tiers
    """
    if request.method == 'POST':
        form = TiersForm(request.POST, request.FILES)

        if form.is_valid():
            tiers = form.save(commit=False)
            tiers.cree_par = request.user
            tiers.save()

            # Vérifier si on doit créer un compte utilisateur
            creer_compte = request.POST.get('creer_compte') == 'on'

            if creer_compte and not tiers.user:
                from django.contrib.auth import get_user_model
                from django.utils import timezone

                User = get_user_model()

                # Générer un mot de passe temporaire
                mot_de_passe_temp = tiers.generer_mot_de_passe_temporaire()

                # Créer le compte utilisateur
                try:
                    # Username = email
                    username = tiers.email

                    # Créer l'utilisateur
                    user = User.objects.create_user(
                        username=username,
                        email=tiers.email,
                        first_name=tiers.prenom or '',
                        last_name=tiers.nom,
                        password=mot_de_passe_temp
                    )

                    # Définir le type d'utilisateur selon le type de tiers
                    if tiers.type_tiers == 'proprietaire':
                        user.user_type = 'landlord'
                    elif tiers.type_tiers == 'locataire':
                        user.user_type = 'tenant'
                    else:
                        user.user_type = 'other'

                    user.save()

                    # Associer le compte au tiers
                    tiers.user = user
                    tiers.mot_de_passe_temporaire = mot_de_passe_temp
                    tiers.date_creation_compte = timezone.now()
                    tiers.compte_active = False  # Sera activé à la première connexion
                    tiers.save()

                    messages.success(
                        request,
                        f"Le tiers {tiers.nom_complet} et son compte utilisateur ont été créés avec succès. Identifiants disponibles sur la page de détails."
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Le tiers {tiers.nom_complet} a été créé mais il y a eu une erreur lors de la création du compte : {str(e)}"
                    )
            else:
                messages.success(
                    request,
                    f"Le tiers {tiers.nom_complet} a été ajouté avec succès."
                )

            # Redirection selon le bouton cliqué
            if 'save_and_add' in request.POST:
                return redirect('tiers:tiers_ajouter')
            elif 'save_and_link' in request.POST:
                return redirect('tiers:tiers_bien_ajouter', tiers_pk=tiers.pk)
            else:
                return redirect('tiers:tiers_detail', pk=tiers.pk)
        else:
            messages.error(
                request,
                "Erreur lors de l'ajout du tiers. Veuillez vérifier les informations saisies."
            )
    else:
        form = TiersForm()

    context = {
        'form': form,
        'page_title': 'Ajouter un Tiers',
        'action': 'Ajouter',
    }

    return render(request, 'tiers/tiers_form.html', context)


@login_required
def tiers_modifier(request, pk):
    """
    Vue pour modifier un tiers existant
    """
    tiers = get_object_or_404(Tiers, pk=pk)

    if request.method == 'POST':
        form = TiersForm(request.POST, request.FILES, instance=tiers)

        if form.is_valid():
            tiers = form.save(commit=False)
            tiers.modifie_par = request.user
            tiers.save()

            messages.success(
                request,
                f"Le tiers {tiers.nom_complet} a été modifié avec succès."
            )

            return redirect('tiers:tiers_detail', pk=tiers.pk)
        else:
            messages.error(
                request,
                "Erreur lors de la modification. Veuillez vérifier les informations saisies."
            )
    else:
        form = TiersForm(instance=tiers)

    context = {
        'form': form,
        'tiers': tiers,
        'page_title': f'Modifier - {tiers.nom_complet}',
        'action': 'Modifier',
    }

    return render(request, 'tiers/tiers_form.html', context)


@login_required
@require_http_methods(["POST"])
def tiers_supprimer(request, pk):
    """
    Vue pour supprimer un tiers
    """
    tiers = get_object_or_404(Tiers, pk=pk)

    # Vérifier s'il y a des biens liés
    if tiers.biens_lies.exists():
        messages.error(
            request,
            f"Impossible de supprimer {tiers.nom_complet}. Ce tiers est lié à {tiers.biens_lies_count} bien(s)."
        )
        return redirect('tiers:tiers_detail', pk=pk)

    nom_complet = tiers.nom_complet
    tiers.delete()

    messages.success(
        request,
        f"Le tiers {nom_complet} a été supprimé avec succès."
    )

    return redirect('tiers:tiers_liste')


# ===== GESTION DES LIAISONS TIERS-BIEN =====

@login_required
def tiers_bien_ajouter(request, tiers_pk=None):
    """
    Vue pour lier un tiers à un bien
    """
    tiers_instance = None
    if tiers_pk:
        tiers_instance = get_object_or_404(Tiers, pk=tiers_pk)

    if request.method == 'POST':
        form = TiersBienForm(request.POST, request.FILES)

        if form.is_valid():
            tiers_bien = form.save(commit=False)
            tiers_bien.cree_par = request.user
            tiers_bien.save()

            messages.success(
                request,
                f"Le tiers a été lié au bien avec succès."
            )

            return redirect('tiers:tiers_detail', pk=tiers_bien.tiers.pk)
        else:
            messages.error(
                request,
                "Erreur lors de la liaison. Veuillez vérifier les informations saisies."
            )
    else:
        initial = {}
        if tiers_instance:
            initial['tiers'] = tiers_instance

        form = TiersBienForm(initial=initial)

    context = {
        'form': form,
        'tiers': tiers_instance,
        'page_title': 'Lier un Tiers à un Bien',
        'action': 'Lier',
    }

    return render(request, 'tiers/tiers_bien_form.html', context)


@login_required
def tiers_bien_modifier(request, pk):
    """
    Vue pour modifier une liaison tiers-bien
    """
    tiers_bien = get_object_or_404(TiersBien, pk=pk)

    if request.method == 'POST':
        form = TiersBienForm(request.POST, request.FILES, instance=tiers_bien)

        if form.is_valid():
            tiers_bien = form.save()

            messages.success(
                request,
                "La liaison a été modifiée avec succès."
            )

            return redirect('tiers:tiers_detail', pk=tiers_bien.tiers.pk)
        else:
            messages.error(
                request,
                "Erreur lors de la modification. Veuillez vérifier les informations saisies."
            )
    else:
        form = TiersBienForm(instance=tiers_bien)

    context = {
        'form': form,
        'tiers_bien': tiers_bien,
        'page_title': f'Modifier la liaison',
        'action': 'Modifier',
    }

    return render(request, 'tiers/tiers_bien_form.html', context)


@login_required
@require_http_methods(["POST"])
def tiers_bien_supprimer(request, pk):
    """
    Vue pour supprimer une liaison tiers-bien
    """
    tiers_bien = get_object_or_404(TiersBien, pk=pk)
    tiers_pk = tiers_bien.tiers.pk

    tiers_bien.delete()

    messages.success(
        request,
        "La liaison a été supprimée avec succès."
    )

    return redirect('tiers:tiers_detail', pk=tiers_pk)


# ===== API POUR RECHERCHE AJAX =====

@login_required
def tiers_search_api(request):
    """
    API pour la recherche de tiers (AJAX)
    """
    search = request.GET.get('q', '')

    if len(search) < 2:
        return JsonResponse({'results': []})

    tiers_list = Tiers.objects.filter(
        Q(nom__icontains=search) |
        Q(prenom__icontains=search) |
        Q(email__icontains=search) |
        Q(telephone__icontains=search) |
        Q(reference__icontains=search)
    ).filter(statut='actif')[:10]

    results = [
        {
            'id': tiers.pk,
            'text': f"{tiers.nom_complet} ({tiers.get_type_tiers_display()})",
            'reference': tiers.reference,
            'email': tiers.email,
            'telephone': tiers.telephone,
        }
        for tiers in tiers_list
    ]

    return JsonResponse({'results': results})


@login_required
def tiers_statistiques(request):
    """
    Vue pour afficher les statistiques des tiers
    """
    # Statistiques par type
    stats_par_type = {}
    for type_code, type_label in Tiers.TYPE_TIERS_CHOICES:
        stats_par_type[type_label] = Tiers.objects.filter(type_tiers=type_code).count()

    # Statistiques par statut
    stats_par_statut = {}
    for statut_code, statut_label in Tiers.STATUT_CHOICES:
        stats_par_statut[statut_label] = Tiers.objects.filter(statut=statut_code).count()

    # Statistiques par type de contrat
    stats_par_contrat = {}
    for contrat_code, contrat_label in TiersBien.TYPE_CONTRAT_CHOICES:
        stats_par_contrat[contrat_label] = TiersBien.objects.filter(type_contrat=contrat_code).count()

    # Top 10 tiers avec le plus de biens liés
    top_tiers = Tiers.objects.annotate(
        nb_biens=Count('biens_lies')
    ).filter(nb_biens__gt=0).order_by('-nb_biens')[:10]

    context = {
        'stats_par_type': stats_par_type,
        'stats_par_statut': stats_par_statut,
        'stats_par_contrat': stats_par_contrat,
        'top_tiers': top_tiers,
        'page_title': 'Statistiques des Tiers',
    }

    return render(request, 'tiers/tiers_statistiques.html', context)


# ===== GESTION DES COMPTES UTILISATEURS =====

@login_required
@require_http_methods(["POST"])
def tiers_reinitialiser_mot_de_passe(request, pk):
    """
    Vue pour réinitialiser le mot de passe d'un tiers
    """
    tiers = get_object_or_404(Tiers, pk=pk)

    if not tiers.user:
        messages.error(
            request,
            f"{tiers.nom_complet} n'a pas de compte utilisateur associé."
        )
        return redirect('tiers:tiers_detail', pk=pk)

    from django.utils import timezone

    # Générer un nouveau mot de passe temporaire
    nouveau_mot_de_passe = tiers.generer_mot_de_passe_temporaire()

    # Mettre à jour le mot de passe de l'utilisateur
    tiers.user.set_password(nouveau_mot_de_passe)
    tiers.user.save()

    # Stocker le mot de passe temporaire dans le tiers
    tiers.mot_de_passe_temporaire = nouveau_mot_de_passe
    tiers.compte_active = False  # Marquer comme non activé
    tiers.modifie_par = request.user
    tiers.save()

    messages.success(
        request,
        f"Le mot de passe de {tiers.nom_complet} a été réinitialisé. Le nouveau mot de passe temporaire est affiché sur la page."
    )

    return redirect('tiers:tiers_detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def tiers_creer_compte(request, pk):
    """
    Vue pour créer un compte utilisateur pour un tiers qui n'en a pas
    """
    tiers = get_object_or_404(Tiers, pk=pk)

    if tiers.user:
        messages.warning(
            request,
            f"{tiers.nom_complet} a déjà un compte utilisateur."
        )
        return redirect('tiers:tiers_detail', pk=pk)

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    User = get_user_model()

    # Générer un mot de passe temporaire
    mot_de_passe_temp = tiers.generer_mot_de_passe_temporaire()

    try:
        # Username = email
        username = tiers.email

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=tiers.email,
            first_name=tiers.prenom or '',
            last_name=tiers.nom,
            password=mot_de_passe_temp
        )

        # Définir le type d'utilisateur selon le type de tiers
        if tiers.type_tiers == 'proprietaire':
            user.user_type = 'landlord'
        elif tiers.type_tiers == 'locataire':
            user.user_type = 'tenant'
        else:
            user.user_type = 'other'

        user.save()

        # Associer le compte au tiers
        tiers.user = user
        tiers.mot_de_passe_temporaire = mot_de_passe_temp
        tiers.date_creation_compte = timezone.now()
        tiers.compte_active = False
        tiers.modifie_par = request.user
        tiers.save()

        messages.success(
            request,
            f"Le compte utilisateur de {tiers.nom_complet} a été créé avec succès."
        )
    except Exception as e:
        messages.error(
            request,
            f"Erreur lors de la création du compte : {str(e)}"
        )

    return redirect('tiers:tiers_detail', pk=pk)
