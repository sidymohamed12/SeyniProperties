# Rapport de Migration - Portail Employé vers Modèle Travail Unifié

**Date:** 28 Octobre 2025
**Objectif:** Migrer le portail employé mobile pour utiliser le modèle `Travail` unifié au lieu de `Intervention` et `Task`

## ✅ Tâches Complétées

### 1. Migration du Dashboard Mobile

**Fichier:** `apps/employees/views.py` - `employee_dashboard_mobile()` (lignes 486-603)

**Changements effectués:**
- ✅ Remplacement des imports `Task` et `Intervention` par `Travail`
- ✅ Utilisation d'une seule requête pour récupérer les travaux:
  ```python
  user_travaux = Travail.objects.filter(
      assigne_a=request.user
  ).select_related('appartement__residence', 'residence')
  ```
- ✅ Simplification de la logique de classification des travaux
- ✅ Mise à jour des statistiques pour utiliser le modèle Travail:
  - `total_pending`: statuts 'signale' + 'assigne'
  - `total_in_progress`: statut 'en_cours'
  - `total_completed_today`: statut 'termine' avec date du jour
  - `total_overdue`: travaux non terminés avec date_prevue dépassée

**Structure des données `work_item`:**
```python
{
    'id': travail.id,
    'type': 'travail',  # Unifié
    'numero': travail.numero_travail,
    'titre': travail.titre,
    'statut': travail.statut,
    'priorite': travail.priorite,
    'type_travail': travail.type_travail,
    'bien_nom': "Résidence - Appartement",
    'date_prevue': travail.date_prevue,
    'detail_url': reverse('employees_mobile:travail_detail', args=[travail.id]),
    ...
}
```

## 🔄 Tâches En Cours

### 2. Vue Détail du Travail Mobile

**Besoin:** Créer `travail_detail_mobile()` pour afficher les détails d'un travail

**Fonctionnalités requises:**
- Affichage des informations complètes du travail
- Checklist de tâches (modèle `TravailChecklist`)
- Photos/médias (modèle `TravailMedia`)
- Actions: Démarrer, Compléter, Mettre en pause
- Rapport de fin de travail
- Gestion des demandes d'achat liées

**Template associé:** `templates/employees/mobile/travail_detail.html`

### 3. Mise à Jour des URLs

**Fichier:** `apps/employees/urls.py` (namespace `employees_mobile`)

**URLs à ajouter/modifier:**
```python
# Nouveau
path('travaux/<int:travail_id>/', views.travail_detail_mobile, name='travail_detail'),
path('travaux/<int:travail_id>/start/', views.travail_start, name='travail_start'),
path('travaux/<int:travail_id>/complete/', views.travail_complete, name='travail_complete'),
path('travaux/<int:travail_id>/checklist/', views.travail_checklist, name='travail_checklist'),

# Deprecated (garder pour compatibilité)
path('tasks/<int:task_id>/', views.task_detail_redirect, name='task_detail'),
path('interventions/<int:intervention_id>/', views.intervention_detail_redirect, name='intervention_detail'),
```

## 📋 Tâches Restantes

### 4. Migration de `my_tasks_mobile()`

**Fichier:** `apps/employees/views.py` (lignes 652-700+)

**Problème:** Utilise encore `Task` et `Intervention`

**Solution:**
```python
def my_tasks_mobile(request):
    """Vue unifiée des travaux mobile - UTILISE MODÈLE TRAVAIL"""
    from apps.maintenance.models import Travail

    # Récupérer SEULEMENT les travaux
    work_list = Travail.objects.filter(
        assigne_a=request.user
    ).select_related('appartement__residence', 'residence')

    # Appliquer filtres (statut, priorité, etc.)
    # Retourner liste unifiée
```

### 5. Autres Vues à Migrer

**Vues utilisant encore l'ancien système:**
- `intervention_detail_view()` → Rediriger vers `travail_detail_mobile()`
- `task_detail_view()` → Rediriger vers `travail_detail_mobile()`
- Toutes les vues de manipulation de Task/Intervention

### 6. Templates à Mettre à Jour

**Templates existants utilisant ancien système:**
```
templates/employees/mobile/
├── interventions_list.html     → SUPPRIMER (utiliser work_list.html)
├── intervention_detail.html    → SUPPRIMER (utiliser travail_detail.html)
├── tasks_list.html             → SUPPRIMER (utiliser work_list.html)
├── task_detail.html            → SUPPRIMER (utiliser travail_detail.html)
└── work_list.html              → ✅ GARDER (déjà unifié)
```

**Nouveaux templates à créer:**
```
templates/employees/mobile/
├── travail_detail.html         → Détail complet d'un travail
├── travail_checklist.html      → Checklist du travail (existe déjà!)
└── profil.html                 → Profil employé (nouvelle fonctionnalité)
```

## 🆕 Nouvelles Fonctionnalités à Ajouter

### 7. Changement de Mot de Passe à la Première Connexion

**Fichier:** `apps/accounts/models.py` - Champ `CustomUser`

**Ajout nécessaire:**
```python
class CustomUser(AbstractUser):
    ...
    mot_de_passe_temporaire = models.BooleanField(
        default=False,
        help_text="True si l'utilisateur doit changer son mot de passe à la prochaine connexion"
    )
```

**Migration:** `apps/accounts/migrations/0XXX_add_temporary_password_field.py`

**Logique:**
```python
# Dans apps/employees/views.py
@login_required
def check_temporary_password(request):
    if request.user.mot_de_passe_temporaire:
        return redirect('employees_mobile:change_password_required')
    return redirect('employees_mobile:dashboard')
```

### 8. Page Profil Employé

**Vue:** `employee_profile_mobile()`

**Fonctionnalités:**
- Afficher informations personnelles
- Changer mot de passe
- Changer photo de profil
- Voir statistiques personnelles
- Historique des travaux complétés

**Template:** `templates/employees/mobile/profil.html`

### 9. Mise à Jour des Couleurs Imani

**Fichiers à modifier:**
```
templates/employees/mobile/dashboard.html
├── Ligne 27-28: Remplacer seyni-primary/secondary
    'seyni-primary': '#a25946',    → 'imani-secondary': '#a25946',
    'seyni-secondary': '#23456b',  → 'imani-primary': '#23456b',

├── Ligne 76: Gradient
    background: linear-gradient(135deg, #a25946 0%, #23456b 100%);
    → background: linear-gradient(135deg, #23456b 0%, #a25946 100%);
```

## 🎯 Plan d'Action Recommandé

**Phase 1: Migration Complète vers Travail** (PRIORITÉ HAUTE)
1. ✅ Migrer `employee_dashboard_mobile()` → **FAIT**
2. ⏳ Créer `travail_detail_mobile()`
3. ⏳ Migrer `my_tasks_mobile()`
4. ⏳ Mettre à jour les URLs
5. ⏳ Créer/adapter les templates

**Phase 2: Nouvelles Fonctionnalités** (PRIORITÉ MOYENNE)
6. ⏳ Ajouter champ `mot_de_passe_temporaire`
7. ⏳ Implémenter changement de mot de passe obligatoire
8. ⏳ Créer page profil employé

**Phase 3: Amélioration Visuelle** (PRIORITÉ BASSE)
9. ⏳ Mettre à jour couleurs vers Imani
10. ⏳ Améliorer UX mobile

## 📊 Progression Actuelle

- **Dashboard mobile migré:** ✅ 100%
- **Vues de détail migrées:** ⏳ 0%
- **URLs mises à jour:** ⏳ 0%
- **Templates adaptés:** ⏳ 0%
- **Nouvelles fonctionnalités:** ⏳ 0%

**Progression globale:** 🔵 15%

## ⚠️ Points d'Attention

1. **Backward Compatibility:** Garder les anciennes URLs avec redirections pour éviter de casser l'application
2. **Données Existantes:** Les anciens Task et Intervention existent encore en base - ne pas les supprimer immédiatement
3. **Tests:** Tester chaque vue migrée avec un compte employé réel
4. **Mobile First:** Toutes les vues doivent être optimisées pour mobile (touch, responsive)

## 🔗 Fichiers Clés

- **Vues:** `apps/employees/views.py`
- **URLs:** `apps/employees/urls.py`
- **Modèles:** `apps/maintenance/models.py` (Travail, TravailChecklist, TravailMedia)
- **Templates:** `templates/employees/mobile/`
- **User Model:** `apps/accounts/models.py` (CustomUser)

---

**Prochaine étape recommandée:** Créer la vue `travail_detail_mobile()` et son template associé.
