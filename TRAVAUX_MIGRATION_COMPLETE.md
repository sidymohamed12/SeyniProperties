# Migration Intervention → Travail - Rapport Complet

**Date**: 25 octobre 2025
**Status**: ✅ Migration de données effectuée avec succès

---

## Contexte

Le projet Seyni Properties était en transition d'un ancien modèle `Intervention` vers un nouveau modèle unifié `Travail` pour la gestion des travaux de maintenance.

**Problème rencontré**:
```
ValueError at /payments/demandes-achat/nouvelle/
Cannot assign "<Intervention: INT-2025-991035>": "Invoice.travail_lie" must be a "Travail" instance.
```

### Cause Racine

1. **Modèles dupliqués**:
   - `Travail` (nouveau modèle unifié) → table `maintenance_travail`
   - `Intervention` (ancien modèle) → table `maintenance_intervention`

2. **Données dans la mauvaise table**:
   - Toutes les vues de maintenance utilisaient encore `Intervention`
   - Les interventions étaient créées dans `maintenance_intervention`
   - Le modèle `Invoice.travail_lie` attendait un objet `Travail` de `maintenance_travail`

3. **Incompatibilité**:
   - Formulaire de demande d'achat corrigé pour utiliser `Travail`
   - Mais les données (2 interventions) étaient dans `Intervention`
   - Impossible d'assigner un objet `Intervention` à un champ `ForeignKey` vers `Travail`

---

## Solution Appliquée

### Étape 1: Correction du Formulaire ✅

**Fichier**: [apps/payments/forms.py:398-405](apps/payments/forms.py#L398-L405)

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Filtrer uniquement les travaux en attente de matériel ou non assignés
    from apps.maintenance.models import Travail  # ✅ Utilise Travail
    self.fields['travail_lie'].queryset = Travail.objects.filter(
        statut__in=['signale', 'assigne', 'en_cours', 'en_attente_materiel']
    ).select_related('appartement__residence').order_by('-date_creation')
    self.fields['travail_lie'].required = False
```

**Avant**: Utilisait `Intervention`
**Après**: Utilise `Travail` ✅

### Étape 2: Migration des Données ✅

**Script créé**: [migrate_intervention_to_travail.py](migrate_intervention_to_travail.py)

**Mapping des champs**:
```python
Intervention                →  Travail
-----------------             ------------------
numero_intervention          →  numero_travail
titre                        →  titre
description                  →  description
type_intervention            →  type_travail
-                            →  nature = 'reactif' (par défaut)
priorite                     →  priorite
appartement                  →  appartement
technicien                   →  assigne_a
date_signalement             →  date_signalement
date_planifiee               →  date_prevue
statut                       →  statut
cout_estime                  →  cout_estime
cout_final                   →  cout_reel
```

**Résultats de la migration**:
```
[INFO] 2 intervention(s) trouvee(s) a migrer
  [OK] Migre: INT-2025-030069 -> INT-2025-030069
  [OK] Migre: INT-2025-991035 -> INT-2025-991035

[RESULTATS]
  Migres: 2
  Erreurs: 0
  Total: 2
```

✅ Les 2 interventions ont été copiées avec succès dans la table `Travail`

### Étape 3: Vérification ✅

```bash
$ env/Scripts/python manage.py shell -c "from apps.maintenance.models import Travail; print(Travail.objects.count())"
2

$ env/Scripts/python manage.py shell -c "from apps.maintenance.models import Travail; [print(t.numero_travail, t.titre, t.statut) for t in Travail.objects.all()]"
INT-2025-991035 kkkskssksss assigne
INT-2025-030069 [titre] assigne
```

---

## État Actuel

### ✅ Ce qui fonctionne maintenant

1. **Formulaire de demande d'achat**:
   - Affiche correctement les travaux depuis le modèle `Travail`
   - Le dropdown "Travail lié" montre les 2 travaux migrés
   - Peut assigner un travail à une demande d'achat sans erreur

2. **Modèle Invoice**:
   - Le champ `travail_lie` ForeignKey vers `Travail` fonctionne
   - Accepte les objets `Travail` correctement

3. **Données**:
   - Les 2 interventions existantes sont maintenant disponibles comme `Travail`
   - Les numéros sont préservés (INT-2025-030069, INT-2025-991035)

### ⚠️ Travail Restant

#### 1. Mettre à jour TOUTES les vues de maintenance

**Fichier**: [apps/maintenance/views.py](apps/maintenance/views.py)

**Ligne 20** - Import:
```python
from .models import Intervention, InterventionMedia  # ❌ À changer
```

**Doit devenir**:
```python
from .models import Travail, TravailMedia  # ✅ Nouveau
```

**Occurrences à corriger** (trouvées via grep):
- Ligne 52, 57, 62: `Intervention.STATUT_CHOICES`, `PRIORITE_CHOICES`, `TYPE_INTERVENTION_CHOICES`
- Ligne 137: `Intervention.objects.select_related...`
- Ligne 189: `Intervention.objects.all()`
- Ligne 1137-1151: Statistiques utilisant `Intervention.objects`
- Ligne 1181: `Intervention.objects.filter...`
- Ligne 1298: `Intervention.objects.create`
- Ligne 1500, 1518-1526: Requêtes technicien `Intervention.objects.filter(technicien=...)`
- Ligne 1554, 1603, 1605: Queries `Intervention.objects`
- Ligne 1660, 1702-1704, 1710, 1716, 1752: Dashboard stats

**Estimation**: ~20-25 occurrences à remplacer

#### 2. Mettre à jour les formulaires de maintenance

**Fichier**: [apps/maintenance/forms.py](apps/maintenance/forms.py)

Vérifie les imports et usages d'`Intervention`.

#### 3. Mettre à jour les templates

Templates affichant des interventions doivent utiliser les nouveaux noms de champs:
- `numero_intervention` → `numero_travail`
- `type_intervention` → `type_travail`
- Ajouter affichage de `nature` (réactif, planifié, préventif, projet)

#### 4. Décider du sort des anciennes données

Les données `Intervention` existent toujours dans `maintenance_intervention`:

**Option A**: Garder temporairement pour référence
**Option B**: Supprimer après vérification complète (recommandé après migration des vues)
**Option C**: Laisser le modèle `Intervention` en read-only

#### 5. Créer une migration Django pour lier les demandes d'achat existantes

Si des `Invoice` (demandes d'achat) pointaient vers des `Intervention` avant, il faut:
1. Créer une data migration Django
2. Trouver les `Invoice` avec `travail_lie` null mais ayant un historique d'`Intervention`
3. Les lier au `Travail` correspondant

---

## Différences Clés entre Intervention et Travail

| Caractéristique | Intervention | Travail |
|----------------|--------------|---------|
| **Scope** | Interventions réactives uniquement | Unifié: réactif, planifié, préventif, projets |
| **Numéro** | `numero_intervention` | `numero_travail` |
| **Type** | `type_intervention` | `type_travail` |
| **Nature** | ❌ N'existe pas | ✅ `nature` (reactif/planifie/preventif/projet) |
| **Table DB** | `maintenance_intervention` | `maintenance_travail` |
| **Status** | Ancien modèle (à déprécier) | Nouveau modèle (actif) |
| **Champ technicien** | `technicien` | `assigne_a` |
| **Date planifiée** | `date_planifiee` | `date_prevue` |
| **Coût final** | `cout_final` | `cout_reel` |

---

## Prochaines Étapes Recommandées

### Priorité 1: Corriger les vues de maintenance (URGENT)

Actuellement, les utilisateurs ne peuvent PAS créer de nouveaux travaux via l'interface car les vues utilisent `Intervention`. Il faut:

1. Remplacer tous les imports `Intervention` par `Travail`
2. Mettre à jour les queryset
3. Adapter les formulaires
4. Tester la création/modification/suppression

### Priorité 2: Migrer les templates

1. Chercher toutes les références à `numero_intervention`, `type_intervention`
2. Remplacer par `numero_travail`, `type_travail`
3. Ajouter affichage du champ `nature`

### Priorité 3: Nettoyer le code

1. Marquer le modèle `Intervention` comme déprécié dans la docstring
2. Ajouter un warning si quelqu'un utilise `Intervention`
3. Après validation complète, supprimer le modèle `Intervention`

### Priorité 4: Data migration complexe

Si nécessaire, créer une migration Django pour:
- Migrer les relations des modèles liés (factures, médias, etc.)
- Supprimer les anciens enregistrements `Intervention`
- Supprimer la table `maintenance_intervention`

---

## Fichiers Modifiés

| Fichier | Statut | Description |
|---------|--------|-------------|
| [apps/payments/forms.py:398-405](apps/payments/forms.py#L398-L405) | ✅ Corrigé | Formulaire DemandeAchat utilise Travail |
| [migrate_intervention_to_travail.py](migrate_intervention_to_travail.py) | ✅ Créé | Script de migration de données |
| [apps/maintenance/views.py](apps/maintenance/views.py) | ⚠️ À corriger | Toutes les vues utilisent encore Intervention |
| [apps/maintenance/forms.py](apps/maintenance/forms.py) | ⚠️ À vérifier | Formulaires à adapter |
| Templates maintenance | ⚠️ À vérifier | Champs à renommer |

---

## Commandes Utiles

### Vérifier les données
```bash
# Compter les Travaux
env/Scripts/python manage.py shell -c "from apps.maintenance.models import Travail; print(Travail.objects.count())"

# Compter les Interventions (anciennes)
env/Scripts/python manage.py shell -c "from apps.maintenance.models import Intervention; print(Intervention.objects.count())"

# Lister tous les Travaux
env/Scripts/python manage.py shell -c "from apps.maintenance.models import Travail; [print(f'{t.numero_travail}: {t.titre} [{t.nature}]') for t in Travail.objects.all()]"
```

### Re-migrer si nécessaire
```bash
# Supprimer les Travaux migrés
env/Scripts/python manage.py shell -c "from apps.maintenance.models import Travail; Travail.objects.all().delete()"

# Re-exécuter la migration
echo "oui" | env/Scripts/python migrate_intervention_to_travail.py
```

---

## Conclusion

✅ **Migration de données réussie**: Les 2 interventions existantes sont maintenant accessibles comme objets `Travail`

✅ **Demandes d'achat fonctionnelles**: Le formulaire peut maintenant lier des travaux aux demandes d'achat

⚠️ **Travail restant**: Les vues de maintenance doivent être migrées pour créer de nouveaux travaux

🎯 **Objectif final**: Déprécier complètement le modèle `Intervention` et utiliser uniquement `Travail` partout
