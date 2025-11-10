# Migration Travaux - Corrections Post-Migration

**Date**: 25 octobre 2025
**Status**: ✅ Erreurs post-migration corrigées

---

## Erreurs Rencontrées Après Migration

Suite à la migration des données d'`Intervention` vers `Travail`, deux erreurs FieldError sont apparues dues aux différences de noms de champs entre les deux modèles.

---

## Erreur 1: FieldError `date_creation` ❌ → `created_at` ✅

### Symptôme
```
FieldError at /payments/demandes-achat/nouvelle/
Cannot resolve keyword 'date_creation' into field.
Choices are: ..., created_at, ..., date_signalement, ...
```

### Cause
Le formulaire `DemandeAchatForm` tentait de trier par `date_creation` alors que le modèle `Travail` utilise `created_at` (hérité de `BaseModel`).

### Fichier Affecté
[apps/payments/forms.py:404](apps/payments/forms.py#L404)

### Correction Appliquée
```python
# AVANT ❌
.order_by('-date_creation')

# APRÈS ✅
.order_by('-created_at')
```

**Changement complet**:
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    from apps.maintenance.models import Travail
    self.fields['travail_lie'].queryset = Travail.objects.filter(
        statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
    ).select_related('appartement__residence').order_by('-created_at')  # ✅ Corrigé
    self.fields['travail_lie'].required = False
```

---

## Erreur 2: FieldError `numero` ❌ → `nom` ✅

### Symptôme
```
FieldError at /dashboard/
Cannot resolve keyword 'numero' into field.
Choices are: ..., nom, ..., reference, ...
```

### Cause
Le dashboard tentait de trier les appartements par `numero` alors que le modèle `Appartement` utilise `nom` comme identifiant.

### Fichier Affecté
[apps/dashboard/views.py:145](apps/dashboard/views.py#L145)

### Correction Appliquée
```python
# AVANT ❌
appartements_list = Appartement.objects.select_related('residence').all().order_by('residence__nom', 'numero')

# APRÈS ✅
appartements_list = Appartement.objects.select_related('residence').all().order_by('residence__nom', 'nom')
```

**Contexte**: Cette ligne préparait la liste des appartements pour le formulaire de création de travaux dans le dashboard.

---

## Tableau Récapitulatif des Différences de Noms de Champs

Ces erreurs soulignent l'importance de connaître les différences entre `Intervention` (ancien) et `Travail` (nouveau):

| Concept | Intervention (ancien) | Travail (nouveau) |
|---------|----------------------|-------------------|
| **Numéro unique** | `numero_intervention` | `numero_travail` |
| **Type de travail** | `type_intervention` | `type_travail` |
| **Nature** | ❌ N'existe pas | ✅ `nature` (reactif/planifie/preventif/projet) |
| **Date création** | ❌ Pas de convention | ✅ `created_at` (BaseModel) |
| **Technicien** | `technicien` | `assigne_a` |
| **Date planifiée** | `date_planifiee` | `date_prevue` |
| **Coût final** | `cout_final` | `cout_reel` |

| Concept | Appartement |
|---------|-------------|
| **Identifiant** | `nom` (pas `numero`) |
| **Référence** | `reference` (auto-généré) |

---

## État Actuel - Résumé

### ✅ Ce qui fonctionne
1. **Migration de données**: 2 interventions → 2 travaux ✅
2. **Formulaire demande d'achat**: Affiche les travaux, tri correct ✅
3. **Dashboard**: Chargement sans erreur, liste appartements correcte ✅

### ⚠️ Toujours à faire
Les vues de maintenance ([apps/maintenance/views.py](apps/maintenance/views.py)) utilisent encore `Intervention`. Cela signifie:
- ❌ Impossible de créer de nouveaux travaux via l'interface actuelle
- ❌ Les listes de travaux affichent la table vide `maintenance_travail` au lieu de `maintenance_intervention`
- ⚠️ Les 2 travaux migrés sont visibles UNIQUEMENT via le modèle `Travail`, pas via les vues maintenance existantes

### 📋 Prochaine Étape Critique
**Migrer [apps/maintenance/views.py](apps/maintenance/views.py)** pour utiliser `Travail` au lieu d'`Intervention`.

Estimation: ~20-25 occurrences de `Intervention` à remplacer par `Travail`.

---

## Fichiers Modifiés dans Cette Session

| Fichier | Ligne | Changement |
|---------|-------|-----------|
| [apps/payments/forms.py](apps/payments/forms.py) | 401 | Import: `Intervention` → `Travail` |
| [apps/payments/forms.py](apps/payments/forms.py) | 404 | Sort: `-date_creation` → `-created_at` |
| [apps/dashboard/views.py](apps/dashboard/views.py) | 145 | Sort: `'numero'` → `'nom'` |

---

## Tests Recommandés

### Test 1: Création de demande d'achat
1. ✅ Aller sur `/payments/demandes-achat/nouvelle/`
2. ✅ Vérifier que le dropdown "Travail lié" affiche les 2 travaux
3. ✅ Sélectionner un travail et créer la demande
4. ✅ Vérifier que la demande est créée sans erreur

### Test 2: Dashboard
1. ✅ Aller sur `/dashboard/`
2. ✅ Vérifier que la page charge sans erreur FieldError
3. ✅ Ouvrir le modal "Nouveau Travail" (si existant)
4. ✅ Vérifier que la liste des appartements s'affiche correctement

### Test 3: Lien travail → demande d'achat
1. Créer une demande d'achat liée à un travail
2. Vérifier que le travail est marqué `en_attente_materiel`
3. Vérifier que depuis le travail, on peut voir la demande liée

---

## Leçons Apprises

1. **Toujours vérifier les noms de champs** lors d'une migration de modèle
2. **BaseModel utilise `created_at`/`updated_at`**, pas `date_creation`
3. **Tester tous les points d'entrée** après une migration (forms, views, templates)
4. **Les migrations de données ne suffisent pas** - il faut aussi migrer le code qui les utilise

---

## Documentation Liée

- [TRAVAUX_MIGRATION_COMPLETE.md](TRAVAUX_MIGRATION_COMPLETE.md) - Migration initiale des données
- [MIGRATION_INTERVENTION_TO_TRAVAIL.md](MIGRATION_INTERVENTION_TO_TRAVAIL.md) - Analyse pré-migration (si existe)
- [migrate_intervention_to_travail.py](migrate_intervention_to_travail.py) - Script de migration
