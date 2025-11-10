# Rapport de Corrections Automatiques - Templates

Date : 2025-10-22 21:10:52

**Mode** : Simulation (Dry-Run)

## 📊 Statistiques

- **Fichiers traités** : 118
- **Fichiers modifiés** : 22
- **Total remplacements** : 59

## 📝 Remplacements par Pattern

| Pattern | Description | Occurrences |
|---------|-------------|-------------|
| `bailleur_text_singular` | Texte "bailleur" → "proprietaire" | 44 |
| `tenant_to_locataire` | tenant → locataire | 7 |
| `locataire_user_get_full_name` | locataire.user.get_full_name → locataire.nom_complet | 3 |
| `bailleurs_text_plural` | Texte "bailleurs" → "proprietaires" | 2 |
| `locataire_user_email` | locataire.user.email → locataire.email | 2 |
| `bailleur_to_proprietaire_variable` | Variable bailleur → proprietaire | 1 |

## 📄 Fichiers Modifiés


### `templates/dashboard/enregistrements.html` (11 modifications)

- **Texte "bailleur" → "proprietaire"** : 11 remplacement(s)

### `templates/contracts/print.html` (10 modifications)

- **Texte "bailleur" → "proprietaire"** : 5 remplacement(s)
- **tenant → locataire** : 5 remplacement(s)

### `templates/dashboard/forms/nouveau_bailleur.html` (5 modifications)

- **Texte "bailleur" → "proprietaire"** : 5 remplacement(s)

### `templates/dashboard/forms/nouvelle_residence.html` (5 modifications)

- **Variable bailleur → proprietaire** : 1 remplacement(s)
- **Texte "bailleur" → "proprietaire"** : 4 remplacement(s)

### `templates/properties/residence_form.html` (3 modifications)

- **Texte "bailleur" → "proprietaire"** : 3 remplacement(s)

### `apps/tenants/templates/tenants/fiche_create.html` (3 modifications)

- **Texte "bailleur" → "proprietaire"** : 3 remplacement(s)

### `templates/properties/etat_lieux_detail.html` (2 modifications)

- **Texte "bailleur" → "proprietaire"** : 2 remplacement(s)

### `templates/properties/etat_lieux_list.html` (2 modifications)

- **Texte "bailleur" → "proprietaire"** : 2 remplacement(s)

### `templates/properties/remise_cles_list.html` (2 modifications)

- **Texte "bailleur" → "proprietaire"** : 2 remplacement(s)

### `templates/dashboard/financial_overview.html` (2 modifications)

- **tenant → locataire** : 2 remplacement(s)

### `templates/dashboard/forms/nouveau_contrat.html` (2 modifications)

- **locataire.user.get_full_name → locataire.nom_complet** : 1 remplacement(s)
- **locataire.user.email → locataire.email** : 1 remplacement(s)

### `apps/payments/templates/payments/detail.html` (2 modifications)

- **locataire.user.get_full_name → locataire.nom_complet** : 1 remplacement(s)
- **locataire.user.email → locataire.email** : 1 remplacement(s)

### `templates/home.html` (1 modifications)

- **Texte "bailleurs" → "proprietaires"** : 1 remplacement(s)

### `templates/properties/residence_detail.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `templates/properties/residences_list.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `templates/properties/appartement_form.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `templates/properties/property_selection.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `templates/properties/appartement_detail.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `templates/properties/etat_lieux_form.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `templates/properties/remise_cles_form.html` (1 modifications)

- **Texte "bailleur" → "proprietaire"** : 1 remplacement(s)

### `apps/employees/templates/employees/base_mobile.html` (1 modifications)

- **Texte "bailleurs" → "proprietaires"** : 1 remplacement(s)

### `apps/payments/templates/payments/list.html` (1 modifications)

- **locataire.user.get_full_name → locataire.nom_complet** : 1 remplacement(s)
