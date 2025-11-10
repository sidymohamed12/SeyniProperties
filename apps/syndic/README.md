# Module Syndic de Copropriété

Ce module gère les copropriétés dont Imany assure le syndic, complètement séparé du module de gestion locative.

## Concepts clés

### Copropriété vs Gestion Locative

- **Gestion locative** : Imany gère des appartements loués (propriétaire → locataire)
- **Syndic** : Imany gère les parties communes d'une copropriété (syndic → copropriétaires)

Les deux types de gestion sont **complètement séparés** et ne se mélangent pas.

### Structure des modèles

```
Residence (type_gestion='syndic')
    ↓
Copropriete
    ├─ Coproprietaires (avec tantièmes)
    ├─ CotisationSyndic (appels de fonds)
    ├─ BudgetPrevisionnel (budget annuel)
    └─ LigneBudget (détail des dépenses)
```

## Modèles

### 1. Copropriete

Représente une copropriété gérée par Imany.

**Champs principaux :**
- `residence` : Lien vers la résidence (OneToOne)
- `nombre_tantiemes_total` : Nombre total de tantièmes (ex: 10000)
- `periode_cotisation` : Mensuel, Trimestriel, Semestriel, Annuel
- `budget_annuel` : Budget prévisionnel annuel
- `date_debut_gestion` : Date de début de gestion par Imany

### 2. Coproprietaire

Lie un Tiers (avec `type_tiers='coproprietaire'`) à une copropriété.

**Champs principaux :**
- `tiers` : Référence vers le modèle Tiers
- `copropriete` : Référence vers la copropriété
- `nombre_tantiemes` : Tantièmes détenus (ex: 250 sur 10000)
- `quote_part` : Pourcentage calculé automatiquement
- `lots` : Appartements/lots détenus (ManyToMany)

**Calcul automatique :**
```python
quote_part = (nombre_tantiemes / nombre_tantiemes_total) * 100
cotisation_periode = budget_annuel * (quote_part / 100) / nb_periodes_par_an
```

### 3. CotisationSyndic

Appel de fonds (cotisation) pour un copropriétaire.

**Champs principaux :**
- `reference` : Référence unique (COT-2025-Q1-001)
- `coproprietaire` : Copropriétaire concerné
- `periode` : Période (Q1, Q2, M01, etc.)
- `annee` : Année
- `montant_theorique` : Montant calculé selon tantièmes
- `montant_percu` : Montant réellement payé
- `statut` : a_venir, en_cours, paye, impaye, annule

**Statut automatique :**
Le statut est mis à jour automatiquement en fonction des paiements et dates.

### 4. PaiementCotisation

Enregistre un paiement pour une cotisation (support des paiements partiels).

### 5. BudgetPrevisionnel & LigneBudget

Gestion du budget prévisionnel annuel voté en assemblée générale.

## Utilisation

### 1. Créer une copropriété

1. Créer une `Residence` avec `type_gestion='syndic'`
2. Créer une `Copropriete` liée à cette résidence
3. Définir le nombre de tantièmes total et le budget annuel

### 2. Ajouter des copropriétaires

1. Créer ou sélectionner un `Tiers` avec `type_tiers='coproprietaire'`
2. Créer un `Coproprietaire` liant le tiers à la copropriété
3. Attribuer les tantièmes (la quote-part se calcule automatiquement)

### 3. Générer les cotisations

#### Via commande de gestion (recommandé)

```bash
# Générer pour la période courante (automatique)
python manage.py generate_syndic_cotisations

# Générer pour une période spécifique
python manage.py generate_syndic_cotisations --annee 2025 --periode Q1

# Mode simulation (sans créer les cotisations)
python manage.py generate_syndic_cotisations --dry-run

# Forcer la régénération
python manage.py generate_syndic_cotisations --force
```

#### Périodes supportées

- **Trimestres** : Q1, Q2, Q3, Q4
- **Semestres** : S1, S2
- **Année** : A1
- **Mois** : M01, M02, ..., M12

#### Automatisation (cron)

Ajouter dans `railway.json` ou crontab :

```json
{
  "cron": [
    {
      "schedule": "0 0 1 */3 * *",
      "command": "python manage.py generate_syndic_cotisations"
    }
  ]
}
```

### 4. Enregistrer un paiement

#### Via l'admin Django

1. Aller dans "Cotisations syndic"
2. Sélectionner la cotisation
3. Ajouter un paiement dans la section "Paiements"

#### Via code Python

```python
from apps.syndic.models import CotisationSyndic

cotisation = CotisationSyndic.objects.get(reference='COT-2025-Q1-001')

# Enregistrer un paiement
cotisation.enregistrer_paiement(
    montant=150000,
    mode_paiement='virement',
    date_paiement='2025-01-15',
    reference_paiement='VIR20250115'
)

# Le montant_percu et le statut sont mis à jour automatiquement
```

## Interface utilisateur

### Dashboards

- **`/syndic/`** : Tableau de bord général avec statistiques
- **`/syndic/coproprietes/`** : Liste des copropriétés
- **`/syndic/coproprietes/<id>/`** : Détails d'une copropriété
- **`/syndic/cotisations/`** : Liste des cotisations avec filtres

### Admin Django

Tous les modèles sont accessibles via l'admin Django avec :
- Interfaces inline pour les relations
- Filtres et recherche
- Actions groupées (marquer comme payé, envoyer relance)
- Statistiques et indicateurs

## Différences avec la gestion locative

| Aspect | Gestion Locative | Syndic |
|--------|------------------|--------|
| **Entité principale** | Appartement | Copropriété |
| **Relation** | Propriétaire → Locataire | Syndic → Copropriétaires |
| **Type de paiement** | Loyer mensuel | Cotisation trimestrielle |
| **Base de calcul** | Montant fixe par appartement | Quote-part (tantièmes) |
| **Document** | Contrat de bail | Budget prévisionnel |
| **Périodicité** | Mensuel | Configurable |

## Intégration avec le système existant

### Modèle Tiers

Le module syndic utilise le modèle `Tiers` unifié avec le type `'coproprietaire'`.

Un même tiers peut avoir plusieurs types :
```python
# Un propriétaire qui est aussi copropriétaire
tiers = Tiers.objects.create(
    nom='Diop',
    prenom='Aminata',
    type_tiers='proprietaire',  # Ou 'coproprietaire', selon le contexte principal
    ...
)
```

### Modèle Residence

Une résidence peut avoir différents types de gestion :
- `'location'` : Gestion locative classique
- `'syndic'` : Syndic de copropriété
- `'mixte'` : Les deux (certains lots loués, d'autres en copropriété)

### Notifications

Le module syndic peut utiliser `apps.notifications` pour :
- Rappels de cotisations
- Alertes d'impayés
- Convocations aux assemblées générales

## Points d'attention

### Tantièmes

- Le total des tantièmes attribués ne doit **jamais dépasser** le nombre total
- Validation automatique à la sauvegarde
- Vérifier les tantièmes disponibles avant d'ajouter un copropriétaire

### Cotisations

- Une cotisation par période et par copropriétaire
- Les cotisations futures (`statut='a_venir'`) peuvent être créées à l'avance
- Le statut se met à jour automatiquement

### Paiements partiels

Une cotisation peut avoir plusieurs paiements :
```python
# Paiement en 2 fois
cotisation.enregistrer_paiement(75000, 'cash', '2025-01-15')
cotisation.enregistrer_paiement(75000, 'virement', '2025-02-15')
# Total perçu = 150000, statut = 'paye' si montant_theorique = 150000
```

## TODO / Améliorations futures

- [ ] Export Excel des cotisations
- [ ] Envoi automatique de relances par email/SMS
- [ ] Génération de reçus PDF
- [ ] Tableau de bord pour les copropriétaires (portail)
- [ ] Gestion des travaux votés en AG
- [ ] Suivi du fonds de roulement
- [ ] Comptabilité séparée par copropriété

## Support

Pour toute question sur le module syndic, consulter :
- Ce README
- Le fichier `CLAUDE.md` à la racine du projet
- Les docstrings dans les modèles
- L'admin Django pour tester les fonctionnalités
