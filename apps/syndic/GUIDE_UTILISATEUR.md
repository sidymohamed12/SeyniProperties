# Guide Utilisateur - Module Syndic

## 🚀 Accès au Module

### 1. Se connecter à l'application
- Aller sur la page de connexion
- Entrer vos identifiants

### 2. Accéder au module Syndic
Dans la **sidebar** (menu latéral gauche), vous trouverez une nouvelle section **"Syndic"** avec 4 entrées :

```
┌─ Syndic ─────────────────┐
│ 📊 Tableau de Bord       │
│ 🏢 Copropriétés          │
│ 💰 Cotisations           │
│ 🧮 Budgets               │
└──────────────────────────┘
```

---

## 📊 Tableau de Bord (`/syndic/`)

Le tableau de bord affiche :

### Statistiques principales
- **Copropriétés actives** : Nombre total de copropriétés gérées
- **Montant théorique** : Total des cotisations attendues pour la période
- **Montant perçu** : Total effectivement payé avec % de recouvrement
- **Impayés** : Montant et nombre de cotisations non payées

### Alertes
- **Copropriétaires débiteurs** : Top 10 avec montants impayés
- **Copropriétés gérées** : Liste des 5 dernières avec accès rapide

### Actions rapides
- ➕ Nouvelle copropriété
- 👤 Ajouter copropriétaire
- 📄 Créer cotisation
- 🧮 Nouveau budget

---

## 🏢 Gestion des Copropriétés

### Créer une copropriété

1. **Accès** : Dashboard → "Nouvelle copropriété" OU `/syndic/coproprietes/creer/`

2. **Formulaire** :
   - **Résidence** : Sélectionner une résidence (type syndic ou mixte)
   - **Nombre de tantièmes total** : Ex: 10000 (représente 100% de la copropriété)
   - **Période de cotisation** : Mensuel, Trimestriel, Semestriel, ou Annuel
   - **Budget annuel** : Ex: 5000000 FCFA
   - **Date de début de gestion** : Date de prise en charge par Imany
   - **Compte bancaire** (optionnel) : IBAN du compte de la copropriété
   - **Statut** : Active/Inactive
   - **Notes** (optionnel)

3. **Sauvegarder** → Redirigé vers la page de détails

### Page de détails d'une copropriété

Affiche :
- **4 cartes statistiques** : Tantièmes totaux, Nombre de copropriétaires, Budget annuel, Période
- **Liste des copropriétaires** : Avec tantièmes, quote-part, cotisation par période
- **Budget de l'année** : Si existant
- **Boutons d'action** :
  - ✏️ Modifier
  - 🗑️ Supprimer (avec confirmation)
  - ➕ Ajouter copropriétaire

### Modifier une copropriété
Cliquer "Modifier" → Formulaire pré-rempli → Modifier → Sauvegarder

### Supprimer une copropriété
Cliquer "Supprimer" → Confirmation JavaScript → Suppression

---

## 👥 Gestion des Copropriétaires

### Ajouter un copropriétaire

1. **Accès** :
   - Depuis page copropriété → "Ajouter"
   - Ou `/syndic/coproprietaires/creer/`

2. **Formulaire** :
   - **Tiers** : Sélectionner un tiers existant (type=copropriétaire)
     > 💡 Si le tiers n'existe pas, créer d'abord un Tiers avec type "Copropriétaire"

   - **Copropriété** : Sélectionner la copropriété

   - **Nombre de tantièmes** : Ex: 250 (sur 10000 total)
     > ✅ La **quote-part est calculée automatiquement** : (250/10000) × 100 = 2.5%

   - **Lots** (optionnel) : Appartements détenus

   - **Date d'entrée** : Date d'acquisition des parts

   - **Date de sortie** (optionnel) : Si le copropriétaire a vendu

   - **Statut** : Actif/Inactif

   - **Notes** (optionnel)

3. **Sauvegarder** → Retour à la page copropriété

### Calculs automatiques

Le système calcule automatiquement :
- **Quote-part** : `(nombre_tantiemes / total_tantiemes) × 100`
- **Cotisation par période** : `budget_annuel × (quote_part / 100) / nb_periodes`

**Exemple** :
- Budget annuel : 5 000 000 FCFA
- Périodicité : Trimestrielle (4 périodes)
- Tantièmes : 250 / 10000 (2.5%)
- **Cotisation trimestrielle** : 5000000 × 0.025 / 4 = **31 250 FCFA**

---

## 💰 Gestion des Cotisations

### Créer une cotisation manuellement

1. **Accès** : `/syndic/cotisations/creer/`

2. **Formulaire** :
   - **Copropriétaire** : Liste déroulante avec format : "Nom - Résidence (Quote-part%)"
   - **Période** : Q1, Q2, Q3, Q4 (trimestres) ou M01-M12 (mois)
   - **Année** : 2025
   - **Montant théorique** : Calculé selon la quote-part
   - **Date d'émission** : Date de création
   - **Date d'échéance** : Date limite de paiement
   - **Statut** : À venir, En cours, Payé, Impayé, Annulé
   - **Notes** (optionnel)

3. **Sauvegarder** → Page de détails de la cotisation

### Générer automatiquement (recommandé)

```bash
# Génération pour la période courante
python manage.py generate_syndic_cotisations

# Pour une période spécifique
python manage.py generate_syndic_cotisations --annee 2025 --periode Q1

# Mode simulation (sans créer)
python manage.py generate_syndic_cotisations --dry-run
```

La commande :
- Parcourt toutes les copropriétés actives
- Crée une cotisation pour chaque copropriétaire actif
- Calcule le montant selon les tantièmes
- Définit les dates automatiquement

### Page de détails d'une cotisation

Affiche :
- **Informations** : Référence, Copropriétaire, Copropriété, Période
- **Montants** : Théorique, Perçu, Restant
- **Statut** : Mis à jour automatiquement
- **Historique des paiements** : Liste de tous les paiements effectués
- **Actions** :
  - 💵 Enregistrer un paiement
  - ✏️ Modifier
  - 🗑️ Supprimer

### Enregistrer un paiement

1. **Accès** : Page cotisation → "Enregistrer un paiement"

2. **Formulaire** :
   - **Montant** : Pré-rempli avec le montant restant
   - **Mode de paiement** : Cash, Virement, Chèque, Orange Money, Wave, Autre
   - **Date de paiement**
   - **Référence paiement** (optionnel) : N° chèque, référence virement, etc.
   - **Notes** (optionnel)

3. **Sauvegarder** → Mise à jour automatique :
   - `montant_percu` += montant du paiement
   - `statut` mis à jour (passe à "Payé" si montant_percu >= montant_theorique)
   - Retour à la page cotisation avec historique mis à jour

### Paiements partiels

Une cotisation peut avoir **plusieurs paiements** :

**Exemple** :
- Cotisation : 150 000 FCFA
- Paiement 1 : 75 000 FCFA (cash) → Statut : En cours
- Paiement 2 : 75 000 FCFA (virement) → Statut : Payé ✅

### Filtres sur la liste

- **Par statut** : À venir, En cours, Payé, Impayé
- **Par année** : 2024, 2025, etc.
- **Par période** : Q1, Q2, Q3, Q4, etc.

---

## 🧮 Gestion des Budgets

### Créer un budget prévisionnel

1. **Accès** : `/syndic/budgets/creer/`

2. **Formulaire** :
   - **Copropriété**
   - **Année** : 2025
   - **Montant total** : Budget annuel
   - **Date AG** : Date de l'assemblée générale
   - **Date de vote** : Date du vote du budget
   - **Statut** : Brouillon, Proposé, Voté, En cours, Clôturé
   - **Document** (optionnel) : Upload PV d'AG
   - **Notes** (optionnel)

3. **Sauvegarder** → Page de détails

### Page de détails d'un budget

Affiche :
- **Statistiques** : Montant total, Montant dépensé, Taux d'exécution, Montant restant
- **Lignes budgétaires** : Détail des dépenses prévues et réalisées
- **Actions** :
  - ✏️ Modifier
  - ➕ Ajouter ligne budgétaire (via admin pour l'instant)

### Lignes budgétaires

Catégories disponibles :
- Entretien courant
- Jardinage
- Nettoyage
- Gardiennage
- Électricité
- Eau
- Assurance
- Réparations
- Travaux
- Honoraires syndic
- Charges bancaires
- Provisions
- Autre

Pour chaque ligne :
- **Montant prévu** : Budget alloué
- **Montant réalisé** : Dépense effective
- **Écart** : Calculé automatiquement
- **Taux de réalisation** : En %

---

## 🎯 Workflows Complets

### Scénario 1 : Nouvelle copropriété de A à Z

1. **Créer la résidence** (si n'existe pas)
   - `/properties/residences/creer/`
   - Type de gestion : "Syndic"

2. **Créer la copropriété**
   - `/syndic/coproprietes/creer/`
   - Sélectionner la résidence
   - Définir tantièmes total : 10000
   - Budget annuel : 5000000 FCFA
   - Période : Trimestriel

3. **Créer les tiers** (si n'existent pas)
   - `/tiers/creer/`
   - Type : "Copropriétaire"
   - Remplir nom, téléphone, email, etc.

4. **Ajouter les copropriétaires**
   - Depuis page copropriété → "Ajouter"
   - Sélectionner tiers
   - Définir tantièmes
   - Quote-part calculée automatiquement

5. **Créer le budget annuel**
   - `/syndic/budgets/creer/`
   - Année : 2025
   - Montant : 5000000 FCFA

6. **Générer les cotisations**
   ```bash
   python manage.py generate_syndic_cotisations --annee 2025 --periode Q1
   ```

7. **Enregistrer les paiements**
   - Liste cotisations → Cliquer cotisation
   - "Enregistrer un paiement"
   - Montant, mode, date → Sauvegarder

### Scénario 2 : Gestion trimestrielle

**Début de trimestre (ex: 1er janvier pour Q1)**

1. Générer les cotisations :
   ```bash
   python manage.py generate_syndic_cotisations --periode Q1
   ```

2. Consulter la liste : `/syndic/cotisations/`
   - Filtrer par période : Q1
   - Vérifier que toutes sont créées

3. Envoyer les avis de cotisation (manuel ou via notifications)

**Pendant le trimestre**

1. Enregistrer les paiements au fur et à mesure
2. Consulter le dashboard pour suivre le taux de recouvrement
3. Identifier les impayés (liste des débiteurs)

**Fin de trimestre**

1. Relancer les impayés
2. Marquer les cotisations impayées
3. Préparer le trimestre suivant

---

## 💡 Conseils et Bonnes Pratiques

### Tantièmes
- ✅ Toujours vérifier que le total des tantièmes attribués ne dépasse pas le total de la copropriété
- ✅ Le système bloque automatiquement si dépassement
- ✅ Exemple : Sur 10000 tantièmes, si 9500 sont attribués, il reste 500 disponibles

### Cotisations
- ✅ Privilégier la génération automatique plutôt que manuelle
- ✅ Utiliser `--dry-run` pour vérifier avant de créer
- ✅ Les statuts se mettent à jour automatiquement
- ✅ Support des paiements partiels

### Paiements
- ✅ Toujours indiquer la référence pour les virements/chèques
- ✅ La date de paiement peut être différente de la date d'enregistrement
- ✅ Les paiements partiels sont supportés
- ✅ Le montant restant est calculé automatiquement

### Sécurité
- ✅ Toujours confirmer avant suppression
- ✅ Les suppressions sont définitives
- ✅ Les paiements sont protégés (on ne peut pas supprimer une cotisation avec paiements)

---

## ❓ FAQ

### Q: Comment créer un copropriétaire ?
**R:** Il faut d'abord créer un Tiers avec type "Copropriétaire", puis l'ajouter à une copropriété.

### Q: Pourquoi la liste des copropriétaires est vide ?
**R:** Vérifiez que vous avez créé des Tiers avec type "Copropriétaire".

### Q: Comment calculer les tantièmes ?
**R:** Les tantièmes représentent la part de propriété. Total = 100% = souvent 10000. Un copropriétaire avec 250 tantièmes = 2.5%.

### Q: Peut-on modifier une cotisation déjà payée ?
**R:** Oui, mais attention à ne pas changer le montant si des paiements existent.

### Q: Comment annuler une cotisation ?
**R:** Modifier le statut à "Annulé" ou la supprimer si aucun paiement.

### Q: Les cotisations se génèrent automatiquement ?
**R:** Non, il faut lancer la commande manuellement ou via cron job.

### Q: Quelle est la différence avec la gestion locative ?
**R:**
- **Gestion locative** : Loyers mensuels pour des locataires
- **Syndic** : Cotisations trimestrielles pour des copropriétaires (basées sur tantièmes)

---

## 🆘 Support

En cas de problème :
1. Vérifier que toutes les données sont remplies
2. Consulter les messages d'erreur (en rouge)
3. Vérifier que les Tiers/Résidences existent
4. Contacter l'administrateur système

---

## 🚀 Pour Aller Plus Loin

### Automatisation

Configurer un cron job pour générer automatiquement les cotisations :

```bash
# Tous les 1er du mois à 8h pour le trimestre
0 8 1 */3 * cd /chemin/projet && python manage.py generate_syndic_cotisations
```

### Notifications

Le module peut être étendu pour :
- Envoyer des SMS/emails de rappel
- Alertes pour impayés
- Convocations AG
- Rapports mensuels

### Export

Possibilité d'ajouter :
- Export Excel des cotisations
- Export PDF des reçus de paiement
- Génération de rapports comptables

---

**Module Syndic - Version 1.0**
Documentation complète disponible dans `apps/syndic/README.md`
