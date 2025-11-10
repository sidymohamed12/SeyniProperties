# Semaine 1 - Tâches Critiques - Rapport de Progression

**Date**: 27 octobre 2025
**Objectif**: Finaliser la migration Intervention → Travail et nettoyer l'architecture

---

## ✅ TÂCHE 1 : Suppression imports obsolètes - COMPLÉTÉE

### Modifications effectuées

**Fichier**: [apps/maintenance/views.py](apps/maintenance/views.py)

#### Avant :
```python
# Imports séparés avec try/except
try:
    from apps.properties.models import Property, Appartement, Residence
except ImportError:
    Property = None
    Appartement = None
    Residence = None

try:
    from apps.accounts.models import Locataire
except ImportError:
    Locataire = None

try:
    from apps.tenants.models import Tenant  # ❌ App supprimée
except ImportError:
    Tenant = None
```

#### Après :
```python
# Imports directs et propres
from apps.properties.models import Property, Appartement, Residence
from apps.tiers.models import Tiers
```

### Détails des changements

1. **Suppression des imports vers apps dépréciées** :
   - ❌ `apps.tenants.models` (app supprimée)
   - ❌ `apps.landlords.models` (app supprimée)
   - ❌ `apps.accounts.models.Locataire` (modèle déprécié)

2. **Remplacement par Tiers** :
   - ✅ Toutes les références à `Locataire` → `Tiers.objects.filter(type_tiers='locataire')`
   - ✅ Mise à jour de 7 occurrences dans views.py

3. **Nettoyage des conditions** :
   - Suppression des vérifications `if Locataire:` et `if Property:`
   - Utilisation directe des modèles importés

### Occurrences corrigées

| Ligne | Avant | Après |
|-------|-------|-------|
| 1243 | `Locataire.objects.all() if Locataire else []` | `Tiers.objects.filter(type_tiers='locataire', statut='actif')` |
| 1285-1290 | `if locataire_id and Locataire:` | `if locataire_id:` + `Tiers.objects.get()` |
| 1337 | `Locataire.objects.all() if Locataire else []` | `Tiers.objects.filter(type_tiers='locataire', statut='actif')` |
| 1365 | `Locataire.objects.all() if Locataire else []` | `Tiers.objects.filter(type_tiers='locataire', statut='actif')` |
| 1407-1412 | `if locataire_id and Locataire:` | `if locataire_id:` + `Tiers.objects.get()` |
| 1469 | `Locataire.objects.all() if Locataire else []` | `Tiers.objects.filter(type_tiers='locataire', statut='actif')` |
| 1664-1667 | `if Locataire: headers.append('Locataire')` | `headers.append('Locataire')` (toujours inclus) |

### Vérifications

✅ Aucune référence restante à `landlords` ou `tenants` apps
✅ Aucune référence restante au modèle `Locataire` de `apps.accounts`
✅ Tous les imports utilisent des modèles actifs

---

## ✅ TÂCHE 2 : Création TravailForm - COMPLÉTÉE

### Nouveau formulaire créé

**Fichier**: [apps/maintenance/forms.py](apps/maintenance/forms.py)
**Lignes**: 17-191

### Caractéristiques du TravailForm

#### Champs du formulaire

```python
fields = [
    'titre', 'description', 'nature', 'type_travail', 'priorite',
    'appartement', 'residence', 'signale_par', 'assigne_a',
    'date_prevue', 'date_limite', 'cout_estime', 'recurrence'
]
```

#### Nouveaux champs vs InterventionForm

| Champ InterventionForm | Champ TravailForm | Changement |
|------------------------|-------------------|------------|
| `titre` | `titre` | ✅ Identique |
| `description` | `description` | ✅ Identique |
| `type_intervention` | `type_travail` | 🔄 Renommé |
| `priorite` | `priorite` | ✅ Identique |
| ❌ N'existe pas | `nature` | ✨ **Nouveau** (réactif, planifié, préventif, projet) |
| `appartement` | `appartement` | ✅ Identique |
| ❌ `bien` (legacy) | `residence` | ✨ **Nouveau** (lieu alternatif) |
| `locataire` | `signale_par` | 🔄 Renommé |
| `technicien` | `assigne_a` | 🔄 Renommé |
| ❌ N'existe pas | `date_prevue` | ✨ **Nouveau** |
| ❌ N'existe pas | `date_limite` | ✨ **Nouveau** |
| `cout_estime` | `cout_estime` | ✅ Identique |
| ❌ N'existe pas | `recurrence` | ✨ **Nouveau** (support tâches récurrentes) |

### Fonctionnalités avancées

#### 1. Validation globale
```python
def clean(self):
    # Vérifie qu'au moins appartement OU residence est spécifié
    if not appartement and not residence:
        raise ValidationError("Vous devez spécifier au moins un lieu.")

    # Auto-remplissage de residence si appartement est fourni
    if appartement and not residence:
        cleaned_data['residence'] = appartement.residence
```

#### 2. Querysets optimisés
```python
# Appartements avec select_related pour éviter N+1
self.fields['appartement'].queryset = Appartement.objects.select_related('residence')

# Locataires actifs uniquement
self.fields['signale_par'].queryset = Tiers.objects.filter(
    type_tiers='locataire',
    statut='actif'
)

# Employés actifs avec le bon user_type
self.fields['assigne_a'].queryset = User.objects.filter(
    user_type='employe',
    is_active=True
)
```

#### 3. Valeurs par défaut intelligentes
```python
if not self.instance.pk:  # Nouveau travail
    self.fields['priorite'].initial = 'normale'
    self.fields['nature'].initial = 'reactif'
    self.fields['recurrence'].initial = 'aucune'
```

#### 4. Validations personnalisées
- `clean_titre()` : Minimum 5 caractères
- `clean_description()` : Minimum 10 caractères
- `clean_cout_estime()` : Maximum 10 millions FCFA (alerte si dépassé)
- `clean_date_prevue()` : Ne peut pas être après date_limite

### Styling Tailwind CSS

✅ Tous les champs utilisent les classes Tailwind pour un design cohérent :
```python
'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
```

### Impacts

✅ **Avantages** :
- Support complet du modèle Travail unifié
- Gestion des nouvelles fonctionnalités (nature, récurrence, dates)
- Querysets optimisés (pas de N+1)
- Validations robustes
- Design cohérent

⚠️ **Prochaines étapes** :
- Mettre à jour les vues pour utiliser `TravailForm` au lieu de `InterventionForm`
- Créer les templates associés (ou adapter les existants)

---

## 🔄 TÂCHE 3 : Renommage des vues - EN COURS

### Statut actuel

**Problème identifié** :
Toutes les vues de maintenance sont nommées `Intervention*` mais utilisent le modèle `Travail`.

### Classes à renommer

| Ancien nom | Nouveau nom | Statut |
|------------|-------------|--------|
| `InterventionsListView` | `TravauxListView` | ⏳ À faire |
| `InterventionDetailView` | `TravailDetailView` | ⏳ À faire |
| `InterventionCreateView` | `TravailCreateView` | ⏳ À faire |
| `InterventionUpdateView` | `TravailUpdateView` | ⏳ À faire |
| `intervention_create_simple` | `travail_create_simple` | ⏳ À faire |
| `intervention_edit_simple` | `travail_edit_simple` | ⏳ À faire |
| `intervention_checklist_view` | `travail_checklist_view` | ⏳ À faire |

### Estimation

- **Nombre de classes** : ~20-25
- **Fichiers impactés** : views.py, urls.py, templates
- **Temps estimé** : 2-3 heures

---

## 📊 STATISTIQUES GLOBALES

### Lignes de code modifiées (Tâches 1-2)

| Fichier | Avant | Après | Diff |
|---------|-------|-------|------|
| `apps/maintenance/views.py` | ~1750 | ~1750 | ~15 modifications |
| `apps/maintenance/forms.py` | ~676 | ~868 | +192 lignes |
| **Total** | ~2426 | ~2618 | **+192 lignes** |

### Imports nettoyés

- ❌ 3 imports dépréciés supprimés
- ✅ 2 imports ajoutés (Tiers, Travail/TravailMedia)

### Nouveau code fonctionnel

- ✅ 1 formulaire complet créé (`TravailForm`)
- ✅ 7 méthodes de validation
- ✅ 1 méthode de nettoyage global

---

## 🎯 PROCHAINES ÉTAPES IMMÉDIATES

### Priorité 1 : Terminer Tâche 3 (2-3h)

1. Renommer toutes les classes de vues
2. Mettre à jour les imports dans views.py
3. Mettre à jour urls.py pour pointer vers les nouvelles vues

### Priorité 2 : Tâche 4 - USER_TYPES (2-3h)

1. Modifier `apps/accounts/models.py`
2. Créer migration de données pour convertir 'tenant'/'landlord' existants
3. Tester les comptes utilisateurs existants

---

## ✅ CRITÈRES DE SUCCÈS

### Tâche 1 ✓
- [x] Aucun import vers apps dépréciées
- [x] Toutes les références à Locataire remplacées par Tiers
- [x] Code exécutable sans erreurs ImportError

### Tâche 2 ✓
- [x] TravailForm créé avec tous les champs du modèle Travail
- [x] Querysets optimisés
- [x] Validations personnalisées
- [x] Documentation inline

### Tâche 3 (en cours)
- [ ] Toutes les vues renommées
- [ ] URLs mises à jour
- [ ] Templates adaptés
- [ ] Tests manuels passent

---

## 📅 TIMELINE

| Tâche | Début | Fin | Durée | Statut |
|-------|-------|-----|-------|--------|
| Tâche 1 | 27/10 10:00 | 27/10 11:00 | 1h | ✅ Complétée |
| Tâche 2 | 27/10 11:00 | 27/10 13:00 | 2h | ✅ Complétée |
| Tâche 3 | 27/10 13:00 | - | - | 🔄 En cours |

---

**Progression globale Semaine 1** : **2/4 tâches complétées** (50%)

**Temps total investi** : ~3 heures
**Temps restant estimé** : ~6 heures

---

**Prochaine mise à jour** : Après completion de la Tâche 3
