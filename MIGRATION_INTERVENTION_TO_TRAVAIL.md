# Migration : Intervention → Travail (Structure Unifiée)

**Date**: 25 octobre 2025
**Objectif**: Migrer complètement de l'ancien modèle `Intervention` vers le nouveau modèle unifié `Travail`

---

## 📊 État Actuel

### Modèles dans `apps/maintenance/models.py`

| Modèle | Ligne | Statut | Usage |
|--------|-------|--------|-------|
| **`Travail`** | 18 | ✅ NOUVEAU - Unifié | Structure cible |
| `TravailMedia` | 481 | ✅ NOUVEAU | Pour `Travail` |
| `TravailChecklist` | 537 | ✅ NOUVEAU | Pour `Travail` |
| **`Intervention`** | 606 | ❌ ANCIEN - Legacy | À remplacer |
| `InterventionMedia` | 830 | ❌ ANCIEN | À remplacer |
| `InterventionChecklistItem` | 1301 | ❌ ANCIEN | À remplacer |

### Différences Clés

**`Travail` (NOUVEAU)**:
```python
class Travail(BaseModel):
    """Modèle unifié pour tous les travaux
    Remplace les anciens modèles Intervention et Tache"""

    nature = models.CharField(choices=NATURE_CHOICES)  # ✅ Nouveau: réactif, planifié, préventif, projet
    type_travail = models.CharField(choices=TYPE_TRAVAIL_CHOICES)  # ✅ Nom correct
    numero_travail = models.CharField(...)  # ✅ Numéro unifié
```

**`Intervention` (ANCIEN)**:
```python
class Intervention(BaseModel):
    """Modèle pour les interventions de maintenance"""  # ❌ Ancien commentaire

    # PAS de champ 'nature'  # ❌ Incomplet
    type_intervention = models.CharField(...)  # ❌ Ancien nom
    numero_intervention = models.CharField(...)  # ❌ Ancien nom
```

---

## 🔍 Analyse de l'Utilisation Actuelle

### Fichiers utilisant `Intervention` (à migrer)

| Fichier | Lignes | Problème |
|---------|--------|----------|
| `apps/maintenance/views.py` | 20 | Import `Intervention` |
| `apps/maintenance/forms.py` | ? | Formulaire `InterventionForm` |
| `apps/maintenance/urls.py` | Multiple | URLs avec `/interventions/` |
| `apps/payments/forms.py` | 401 | Queryset `Intervention.objects` ❌ |
| `apps/employees/views.py` | 377 | Queryset `Intervention.objects` |
| Templates | Multiple | Références `intervention` |

### Fichiers DÉJÀ corrects (pointent vers `Travail`)

| Fichier | Ligne | Status |
|---------|-------|--------|
| `apps/payments/models.py` | 464 | ✅ `travail_lie = ForeignKey('maintenance.Travail')` |

---

## ⚠️ Problème Actuel

**Erreur rencontrée**:
```
ValueError: Cannot assign "<Intervention: ...>":
"Invoice.travail_lie" must be a "Travail" instance.
```

**Cause**:
1. `Invoice.travail_lie` attend un objet `Travail`
2. Le formulaire `DemandeAchatForm` charge des objets `Intervention`
3. Tentative d'assigner `Intervention` → `travail_lie` → ❌ Échec

---

## 🎯 Plan de Migration

### Phase 1: Vérifier si des données `Travail` existent

```sql
SELECT COUNT(*) FROM maintenance_travail;
SELECT COUNT(*) FROM maintenance_intervention;
```

**Options**:
- **Si `maintenance_travail` est vide** → Toutes les données sont dans `Intervention`
- **Si les deux ont des données** → Migration en cours, besoin de synchronisation

### Phase 2: Décider de la stratégie

#### Option A: Migration complète (recommandé si pas de données `Travail`)
1. Garder le modèle `Intervention` en base de données
2. Créer un alias: `Travail = Intervention` temporairement
3. Migrer progressivement les vues
4. Renommer la table en base après

#### Option B: Coexistence (si migration déjà commencée)
1. Garder les deux modèles
2. Synchroniser les données
3. Rediriger `Travail` vers la table `intervention`

#### Option C: Migration brutale (si peu de données)
1. Exporter les données `Intervention`
2. Les importer dans `Travail`
3. Supprimer `Intervention`

### Phase 3: Actions Immédiates (Solution Temporaire)

**Pour débloquer immédiatement** :

1. **Corriger le formulaire `DemandeAchatForm`**:
```python
# apps/payments/forms.py ligne 401
from apps.maintenance.models import Travail  # ✅ Pas Intervention
self.fields['travail_lie'].queryset = Travail.objects.filter(...)
```

2. **Vérifier quelle table est utilisée**:
- Si formulaire de création utilise `Intervention` → les données sont dans `maintenance_intervention`
- Mais `Invoice.travail_lie` attend `Travail` → cherche dans `maintenance_travail`
- **Conflit !**

---

## 🛠️ Solution Immédiate

### Scénario probable: Toutes les données sont dans `Intervention`

**Actions**:

1. **Faire pointer `Travail` vers la table `intervention`**:
```python
# apps/maintenance/models.py
class Travail(BaseModel):
    class Meta:
        db_table = 'maintenance_intervention'  # ✅ Réutiliser la table existante
```

2. **OU** Faire pointer `Invoice.travail_lie` vers `Intervention`:
```python
# apps/payments/models.py ligne 464
travail_lie = models.ForeignKey(
    'maintenance.Intervention',  # ✅ Temporaire: utiliser l'ancien modèle
    ...
)
```

3. **OU** Créer une migration de données:
```python
# Migration pour copier Intervention → Travail
from apps.maintenance.models import Intervention, Travail

for intervention in Intervention.objects.all():
    Travail.objects.create(
        titre=intervention.titre,
        description=intervention.description,
        type_travail=intervention.type_intervention,  # Mapper les champs
        numero_travail=intervention.numero_intervention,
        # ... tous les autres champs
    )
```

---

## 📝 Recommandations

### Choix Recommandé: **Option A - Migration Progressive**

**Pourquoi**:
- Pas de perte de données
- Migration progressive sans casser le système
- Possibilité de rollback

**Étapes**:
1. ✅ Identifier quelle table contient les données (`maintenance_intervention` probablement)
2. ✅ Faire pointer `Travail` vers cette table avec `db_table`
3. ✅ Ajouter les champs manquants à la table si nécessaire
4. ✅ Mettre à jour toutes les vues pour utiliser `Travail`
5. ✅ Renommer `InterventionForm` → `TravailForm`
6. ✅ Supprimer le modèle `Intervention` quand tout est migré

---

## ✅ TODO Immédiat

- [ ] Vérifier quelle table contient les données actuelles
- [ ] Décider si `Travail` doit pointer vers `maintenance_intervention` (table existante)
- [ ] Corriger `apps/payments/forms.py` pour utiliser le bon modèle
- [ ] Créer une migration Django si nécessaire
- [ ] Tester la création de demande d'achat

---

## 🚨 IMPORTANT

**Ne PAS faire**:
- ❌ Modifier aléatoirement les imports sans comprendre la structure
- ❌ Créer deux tables séparées avec données dupliquées
- ❌ Supprimer des données existantes

**Toujours faire**:
- ✅ Vérifier d'abord l'état de la base de données
- ✅ Comprendre où sont les données actuellement
- ✅ Faire une sauvegarde avant toute migration
- ✅ Tester sur un petit échantillon d'abord
