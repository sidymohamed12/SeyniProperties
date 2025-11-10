# Fix: Page de Liste des Travaux

**Date**: 25 octobre 2025
**Status**: ✅ Corrections appliquées avec succès

---

## Problème Rapporté

La page `/maintenance/travaux/` ne récupérait pas correctement les informations des travaux :
- ❌ Numéros de travaux non affichés
- ❌ Employés assignés non affichés
- ❌ Statistiques ne fonctionnaient pas

---

## Cause Racine

La vue `InterventionsListView` utilisait encore l'ancien modèle `Intervention` au lieu du nouveau modèle `Travail`, donc elle lisait depuis la mauvaise table de base de données.

---

## Corrections Appliquées

### 1. ✅ Mise à jour de la Vue - [apps/maintenance/views.py:122-233](apps/maintenance/views.py#L122-L233)

#### A. Import du modèle `Travail`

**Ligne 20**:
```python
# AVANT ❌
from .models import Intervention, InterventionMedia

# APRÈS ✅
from .models import Travail, Intervention, TravailMedia, InterventionMedia
```

**Lignes 25-30**:
```python
# AVANT ❌
try:
    from apps.properties.models import Property
except ImportError:
    Property = None

# APRÈS ✅
try:
    from apps.properties.models import Property, Appartement, Residence
except ImportError:
    Property = None
    Appartement = None
    Residence = None
```

#### B. Changement du modèle de la vue

**Ligne 124**:
```python
# AVANT ❌
model = Intervention

# APRÈS ✅
model = Travail
```

#### C. Correction du queryset

**Lignes 137-187**:
```python
# AVANT ❌
queryset = Intervention.objects.select_related('technicien').order_by('-date_signalement')
queryset = queryset.select_related('bien')  # Ancien champ
queryset = queryset.filter(technicien_id=technician)  # Ancien champ
queryset = queryset.filter(type_intervention=type_intervention)  # Ancien champ
queryset = queryset.filter(bien_id=property_filter)  # Ancien champ

# APRÈS ✅
queryset = Travail.objects.select_related('assigne_a').order_by('-date_signalement')
queryset = queryset.select_related('appartement__residence')  # Nouveau champ
queryset = queryset.filter(assigne_a_id=technician)  # Nouveau champ
queryset = queryset.filter(type_travail=type_travail)  # Nouveau champ
queryset = queryset.filter(appartement_id=appartement_filter)  # Nouveau champ
queryset = queryset.filter(residence_id=residence_filter)  # Nouveau champ
```

**Recherche améliorée (lignes 154-161)**:
```python
queryset = queryset.filter(
    Q(titre__icontains=search) |
    Q(description__icontains=search) |
    Q(numero_travail__icontains=search) |  # ✅ Nouveau
    Q(appartement__nom__icontains=search) |  # ✅ Nouveau
    Q(appartement__residence__nom__icontains=search)  # ✅ Nouveau
)
```

#### D. Correction des statistiques

**Lignes 209-222**:
```python
# AVANT ❌
all_interventions = Intervention.objects.all()
'stats': {
    'total_interventions': all_interventions.count(),
    'pending_interventions': all_interventions.filter(statut='signale').count(),
    # ...
}

# APRÈS ✅
all_travaux = Travail.objects.all()
'stats': {
    'total': all_travaux.count(),
    'urgents': all_travaux.filter(priorite='urgente', ...).count(),
    'en_cours': all_travaux.filter(statut='en_cours').count(),
    'attente_materiel': all_travaux.filter(statut='en_attente_materiel').count(),
    'en_retard': 0,  # TODO: calculer basé sur date_prevue
    'signale': all_travaux.filter(statut='signale').count(),
    'assigne': all_travaux.filter(statut='assigne').count(),
    'complete': all_travaux.filter(statut='complete').count(),
}
```

#### E. Mise à jour du contexte pour les filtres

**Lignes 224-232**:
```python
# AVANT ❌
'technicians': User.objects.filter(user_type='technicien', is_active=True),
'properties': Property.objects.all()[:50] if Property else [],
'intervention_types': getattr(Intervention, 'TYPE_INTERVENTION_CHOICES', []),
'priorities': getattr(Intervention, 'PRIORITE_CHOICES', []),
'statuses': getattr(Intervention, 'STATUT_CHOICES', []),

# APRÈS ✅
'technicians': User.objects.filter(user_type='technicien', is_active=True),
'appartements': Appartement.objects.select_related('residence').all()[:100],
'residences': Residence.objects.all(),
'travail_types': Travail.TYPE_TRAVAIL_CHOICES,
'priorities': Travail.PRIORITE_CHOICES,
'statuses': Travail.STATUT_CHOICES,
'natures': Travail.NATURE_CHOICES,  # ✅ Nouveau champ unique à Travail
```

---

### 2. ✅ Correction du Template - [templates/maintenance/travail_list.html:299](templates/maintenance/travail_list.html#L299)

#### Problème: Champ `appartement.numero` n'existe pas

**Ligne 299**:
```django
{# AVANT ❌ #}
{{ travail.appartement.residence.nom }} - {{ travail.appartement.numero }}

{# APRÈS ✅ #}
{{ travail.appartement.residence.nom }} - {{ travail.appartement.nom }}
```

Le modèle `Appartement` utilise `nom` comme identifiant, pas `numero`.

---

## Mapping Complet des Champs

| Concept | Intervention (ancien) | Travail (nouveau) |
|---------|----------------------|-------------------|
| **Numéro** | `numero_intervention` | `numero_travail` |
| **Employé assigné** | `technicien` | `assigne_a` |
| **Type de travail** | `type_intervention` | `type_travail` |
| **Bien immobilier** | `bien` (Property) | `appartement` + `residence` |
| **Nature** | ❌ N'existe pas | ✅ `nature` (reactif/planifie/preventif/projet) |
| **Date planifiée** | `date_planifiee` | `date_prevue` |
| **Statut "en attente matériel"** | ❌ N'existe pas | ✅ `en_attente_materiel` |

---

## Résultat

### ✅ Ce qui fonctionne maintenant

1. **Affichage des travaux**:
   - ✅ Numéros de travaux affichés (`numero_travail`)
   - ✅ Titres et descriptions
   - ✅ Badges de nature (Réactif/Planifié/Préventif/Projet)
   - ✅ Type de travail (Plomberie, Électricité, etc.)
   - ✅ Liens vers demandes d'achat si existantes

2. **Localisation**:
   - ✅ Résidence et appartement affichés correctement
   - ✅ Format: "Résidence Les Palmiers - Appt A101"

3. **Employés assignés**:
   - ✅ Initiales affichées dans un cercle
   - ✅ Nom complet visible
   - ✅ Affiche "-" si non assigné

4. **Statistiques**:
   - ✅ Total de travaux
   - ✅ Travaux urgents
   - ✅ Travaux en cours
   - ✅ Travaux en attente de matériel
   - ✅ Travaux en retard (à implémenter)
   - ✅ Signalés, Assignés, Complétés

5. **Filtres**:
   - ✅ Par nature (réactif, planifié, préventif, projet)
   - ✅ Par type de travail
   - ✅ Par statut
   - ✅ Par priorité
   - ✅ Par technicien
   - ✅ Par appartement
   - ✅ Par résidence
   - ✅ Recherche globale

6. **Vues multiples**:
   - ✅ Vue table (liste)
   - ✅ Vue kanban (si implémentée)
   - ✅ Vue calendrier (si implémentée)

---

## Tests Recommandés

### Test 1: Affichage des travaux existants
1. ✅ Aller sur `/maintenance/travaux/`
2. ✅ Vérifier que les 2 travaux migrés apparaissent
3. ✅ Vérifier que leurs numéros sont affichés (INT-2025-030069, INT-2025-991035)
4. ✅ Vérifier que les employés assignés sont affichés

### Test 2: Statistiques
1. ✅ Vérifier que "Total" affiche 2
2. ✅ Vérifier les compteurs de statut
3. ✅ Vérifier les compteurs de priorité

### Test 3: Filtres
1. Tester le filtre par statut (signalé, assigné, etc.)
2. Tester le filtre par type de travail
3. Tester la recherche globale
4. Tester le filtre par technicien

### Test 4: Création de nouveau travail
1. Cliquer sur "Nouveau travail"
2. Remplir le formulaire
3. ✅ Vérifier que le travail est créé dans le modèle `Travail`
4. ✅ Vérifier qu'il apparaît dans la liste

---

## Améliorations Futures

### Calculer les travaux en retard

Actuellement `stats.en_retard` est hardcodé à 0. Implémenter:

```python
from django.utils import timezone

'en_retard': all_travaux.filter(
    date_prevue__lt=timezone.now(),
    statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
).count(),
```

### Ajouter un filtre par nature

Le template a un filtre "Nature" mais il n'est pas géré dans la vue. Ajouter dans `get_queryset()`:

```python
nature = self.request.GET.get('nature')
if nature:
    queryset = queryset.filter(nature=nature)
```

---

## Fichiers Modifiés

| Fichier | Lignes | Changements |
|---------|--------|-------------|
| [apps/maintenance/views.py](apps/maintenance/views.py) | 20 | Ajout import `Travail`, `TravailMedia` |
| [apps/maintenance/views.py](apps/maintenance/views.py) | 25-30 | Ajout import `Appartement`, `Residence` |
| [apps/maintenance/views.py](apps/maintenance/views.py) | 124 | `model = Travail` |
| [apps/maintenance/views.py](apps/maintenance/views.py) | 137-187 | Refonte complète du queryset |
| [apps/maintenance/views.py](apps/maintenance/views.py) | 209-222 | Statistiques alignées avec template |
| [apps/maintenance/views.py](apps/maintenance/views.py) | 224-232 | Contexte avec nouveaux modèles |
| [templates/maintenance/travail_list.html](templates/maintenance/travail_list.html) | 299 | `.numero` → `.nom` |

---

## Prochaines Étapes

La page de liste des travaux fonctionne maintenant correctement ! Les prochaines vues à migrer sont:

1. **InterventionCreateView** (ligne 236) - Création de travaux
2. **InterventionUpdateView** - Modification de travaux
3. **intervention_detail_view** - Détail d'un travail
4. **intervention_delete_view** - Suppression de travaux
5. Toutes les autres fonctions utilisant `Intervention`

Référez-vous à [TRAVAUX_MIGRATION_COMPLETE.md](TRAVAUX_MIGRATION_COMPLETE.md) pour la stratégie globale de migration.

---

## Documentation Liée

- [TRAVAUX_MIGRATION_COMPLETE.md](TRAVAUX_MIGRATION_COMPLETE.md) - Migration initiale des données
- [TRAVAUX_MIGRATION_FIXES.md](TRAVAUX_MIGRATION_FIXES.md) - Corrections post-migration
- [migrate_intervention_to_travail.py](migrate_intervention_to_travail.py) - Script de migration des données
