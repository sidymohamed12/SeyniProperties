# Rapport de Migration des Templates - Architecture Tiers

Date d'analyse : Wed Oct 22 21:02:40 UTC 2025

## 📊 Statistiques Globales

- **Total fichiers analysés** : 118
- **Fichiers avec problèmes** : 21
- **Total problèmes détectés** : 62

### Par sévérité

- 🔴 **HIGH** : 50 problèmes
- 🟡 **MEDIUM** : 1 problèmes
- 🟢 **LOW** : 11 problèmes

## 📋 Fichiers à Mettre à Jour

| Fichier | Total | 🔴 HIGH | 🟡 MEDIUM | 🟢 LOW |
|---------|-------|---------|-----------|--------|
| `templates/dashboard/enregistrements.html` | 11 | 11 | 0 | 0 |
| `templates/contracts/print.html` | 10 | 5 | 0 | 5 |
| `templates/dashboard/forms/nouveau_bailleur.html` | 6 | 5 | 1 | 0 |
| `templates/dashboard/forms/nouvelle_residence.html` | 5 | 5 | 0 | 0 |
| `templates/contracts/create.html` | 4 | 0 | 0 | 4 |
| `templates/properties/residence_form.html` | 3 | 3 | 0 | 0 |
| `apps/tenants/templates/tenants/fiche_create.html` | 3 | 3 | 0 | 0 |
| `templates/properties/etat_lieux_detail.html` | 2 | 2 | 0 | 0 |
| `templates/properties/etat_lieux_list.html` | 2 | 2 | 0 | 0 |
| `templates/properties/remise_cles_list.html` | 2 | 2 | 0 | 0 |
| `templates/dashboard/financial_overview.html` | 2 | 0 | 0 | 2 |
| `templates/dashboard/forms/nouveau_contrat.html` | 2 | 2 | 0 | 0 |
| `apps/payments/templates/payments/detail.html` | 2 | 2 | 0 | 0 |
| `templates/properties/appartement_form.html` | 1 | 1 | 0 | 0 |
| `templates/properties/remise_cles_form.html` | 1 | 1 | 0 | 0 |
| `templates/properties/residence_detail.html` | 1 | 1 | 0 | 0 |
| `templates/properties/residences_list.html` | 1 | 1 | 0 | 0 |
| `templates/properties/appartement_detail.html` | 1 | 1 | 0 | 0 |
| `templates/properties/property_selection.html` | 1 | 1 | 0 | 0 |
| `templates/properties/etat_lieux_form.html` | 1 | 1 | 0 | 0 |
| `apps/payments/templates/payments/list.html` | 1 | 1 | 0 | 0 |

## 🔍 Détails par Fichier


### 📄 `templates/dashboard/enregistrements.html`

**11 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 248)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <!-- Nouveau Bailleur avec compte -->
  ```

#### 🔴 Problème 2 (Ligne 249)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <div class="action-card imani-card p-6" onclick="openModal('bailleur')">
  ```

#### 🔴 Problème 3 (Ligne 255)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <h3 class="text-lg font-bold text-gray-900">Nouveau Bailleur</h3>
  ```

#### 🔴 Problème 4 (Ligne 278)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  Créez un <strong>Bailleur</strong> ou <strong>Locataire</strong> lorsque la personne a besoin de <strong>se connecter au système</strong> pour :
  ```

#### 🔴 Problème 5 (Ligne 306)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  puis créer un compte utilisateur <strong>Bailleur/Locataire</strong> si la personne a besoin d'un accès système ultérieurement.
  ```

#### 🔴 Problème 6 (Ligne 545)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  'bailleur': {
  ```

#### 🔴 Problème 7 (Ligne 546)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  title: 'Nouveau Bailleur',
  ```

#### 🔴 Problème 8 (Ligne 917)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  if ((type === 'employe' || type === 'locataire' || type === 'bailleur') && data.data && data.data.username && data.data.temp_password) {
  ```

#### 🔴 Problème 9 (Ligne 1084)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  // Fonction spécialisée pour les notifications d'utilisateur avec identifiants (employé, locataire, bailleur)
  ```

#### 🔴 Problème 10 (Ligne 1091)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  'bailleur': 'Bailleur'
  ```

#### 🔴 Problème 11 (Ligne 1091)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  'bailleur': 'Bailleur'
  ```


### 📄 `templates/contracts/print.html`

**10 problème(s) détecté(s)**

#### 🟢 Problème 1 (Ligne 217)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <td>{{ contract.tenant.user.get_full_name }}</td>
  ```

#### 🟢 Problème 2 (Ligne 221)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <td>{{ contract.tenant.user.email }}</td>
  ```

#### 🟢 Problème 3 (Ligne 223)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  {% if contract.tenant.user.phone %}
  ```

#### 🟢 Problème 4 (Ligne 226)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <td>{{ contract.tenant.user.phone }}</td>
  ```

#### 🔴 Problème 5 (Ligne 232)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <!-- Bailleur -->
  ```

#### 🔴 Problème 6 (Ligne 234)

- **Pattern détecté** : `BAILLEUR`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <div class="section-title">BAILLEUR</div>
  ```

#### 🔴 Problème 7 (Ligne 303)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <td class="header-cell" width="25%">Le Bailleur</td>
  ```

#### 🟢 Problème 8 (Ligne 314)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <td>{{ contract.tenant.user.get_full_name }}</td>
  ```

#### 🔴 Problème 9 (Ligne 344)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <p><strong>Article 6 - Obligations du bailleur :</strong> Le bailleur s'engage à :</p>
  ```

#### 🔴 Problème 10 (Ligne 344)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <p><strong>Article 6 - Obligations du bailleur :</strong> Le bailleur s'engage à :</p>
  ```


### 📄 `templates/dashboard/forms/nouveau_bailleur.html`

**6 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 40)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <!-- Type de bailleur -->
  ```

#### 🔴 Problème 2 (Ligne 43)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  Type de bailleur <span class="text-red-500">*</span>
  ```

#### 🟡 Problème 3 (Ligne 45)

- **Pattern détecté** : `landlord`
- **Type** : landlord_reference
- **Description** : Référence à landlord (terme anglais)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <select name="landlord_type" required class="form-control" id="landlord-type-select">
  ```

#### 🔴 Problème 4 (Ligne 67)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  placeholder="Adresse complète du bailleur"></textarea>
  ```

#### 🔴 Problème 5 (Ligne 94)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <li>• Le bailleur recevra ses identifiants par email</li>
  ```

#### 🔴 Problème 6 (Ligne 106)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  console.log('DOM chargé, initialisation du formulaire bailleur');
  ```


### 📄 `templates/dashboard/forms/nouvelle_residence.html`

**5 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 15)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <!-- Bailleur -->
  ```

#### 🔴 Problème 2 (Ligne 18)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  Bailleur propriétaire <span class="text-red-500">*</span>
  ```

#### 🔴 Problème 3 (Ligne 21)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <option value="">-- Sélectionner un bailleur --</option>
  ```

#### 🔴 Problème 4 (Ligne 22)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  {% for bailleur in proprietaires %}
  ```

#### 🔴 Problème 5 (Ligne 23)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <option value="{{ bailleur.id }}">
  ```


### 📄 `templates/contracts/create.html`

**4 problème(s) détecté(s)**

#### 🟢 Problème 1 (Ligne 104)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  {% for tenant in available_tenants %}
  ```

#### 🟢 Problème 2 (Ligne 105)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <option value="{{ tenant.id }}">
  ```

#### 🟢 Problème 3 (Ligne 106)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  {{ tenant.user.get_full_name }} - {{ tenant.user.email }}
  ```

#### 🟢 Problème 4 (Ligne 106)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  {{ tenant.user.get_full_name }} - {{ tenant.user.email }}
  ```


### 📄 `templates/properties/residence_form.html`

**3 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 135)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  Bailleur propriétaire <span class="required-field">*</span>
  ```

#### 🔴 Problème 2 (Ligne 330)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <li>Vérifiez que le bailleur propriétaire est correct</li>
  ```

#### 🔴 Problème 3 (Ligne 341)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <li>Invitez le bailleur à valider les informations</li>
  ```


### 📄 `apps/tenants/templates/tenants/fiche_create.html`

**3 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 205)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <!-- Section 8: Ancien bailleur -->
  ```

#### 🔴 Problème 2 (Ligne 209)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <i class="fas fa-history mr-2"></i>8. Précédent Bailleur
  ```

#### 🔴 Problème 3 (Ligne 215)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <label class="block text-sm font-medium text-gray-700 mb-2">Ancien bailleur</label>
  ```


### 📄 `templates/properties/etat_lieux_detail.html`

**2 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 265)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <!-- Bailleur -->
  ```

#### 🔴 Problème 2 (Ligne 268)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <h3 class="font-semibold text-gray-900 mb-2">Bailleur</h3>
  ```


### 📄 `templates/properties/etat_lieux_list.html`

**2 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 117)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <span class="text-green-700">Bailleur signé</span>
  ```

#### 🔴 Problème 2 (Ligne 120)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <span class="text-yellow-700">Bailleur en attente</span>
  ```


### 📄 `templates/properties/remise_cles_list.html`

**2 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 123)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <span class="text-green-700">Bailleur ✓</span>
  ```

#### 🔴 Problème 2 (Ligne 126)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <span class="text-yellow-700">Bailleur en attente</span>
  ```


### 📄 `templates/dashboard/financial_overview.html`

**2 problème(s) détecté(s)**

#### 🟢 Problème 1 (Ligne 249)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <p class="font-semibold text-gray-800">{{ payment.facture.contrat.tenant.user.get_full_name }}</p>
  ```

#### 🟢 Problème 2 (Ligne 296)

- **Pattern détecté** : `tenant`
- **Type** : tenant_reference
- **Description** : Référence à tenant (terme anglais)
- **Suggestion** : Remplacer par locataire
- **Contexte** :
  ```django
  <p class="font-semibold text-gray-800">{{ invoice.contrat.tenant.user.get_full_name }}</p>
  ```


### 📄 `templates/dashboard/forms/nouveau_contrat.html`

**2 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 31)

- **Pattern détecté** : `locataire.user.get_full_name`
- **Type** : locataire_user_access
- **Description** : Accès via locataire.user (devrait être direct)
- **Suggestion** : Utiliser locataire.nom_complet, locataire.email, etc.
- **Contexte** :
  ```django
  {{ locataire.user.get_full_name }} - {{ locataire.user.email }}
  ```

#### 🔴 Problème 2 (Ligne 31)

- **Pattern détecté** : `locataire.user.email`
- **Type** : locataire_user_access
- **Description** : Accès via locataire.user (devrait être direct)
- **Suggestion** : Utiliser locataire.nom_complet, locataire.email, etc.
- **Contexte** :
  ```django
  {{ locataire.user.get_full_name }} - {{ locataire.user.email }}
  ```


### 📄 `apps/payments/templates/payments/detail.html`

**2 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 226)

- **Pattern détecté** : `locataire.user.get_full_name`
- **Type** : locataire_user_access
- **Description** : Accès via locataire.user (devrait être direct)
- **Suggestion** : Utiliser locataire.nom_complet, locataire.email, etc.
- **Contexte** :
  ```django
  {{ payment.facture.contrat.locataire.user.get_full_name }}
  ```

#### 🔴 Problème 2 (Ligne 234)

- **Pattern détecté** : `locataire.user.email`
- **Type** : locataire_user_access
- **Description** : Accès via locataire.user (devrait être direct)
- **Suggestion** : Utiliser locataire.nom_complet, locataire.email, etc.
- **Contexte** :
  ```django
  {{ payment.facture.contrat.locataire.user.email }}
  ```


### 📄 `templates/properties/appartement_form.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 542)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <li>Vérifiez les informations avec le bailleur</li>
  ```


### 📄 `templates/properties/remise_cles_form.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 206)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <span class="text-gray-700">Signé par le bailleur</span>
  ```


### 📄 `templates/properties/residence_detail.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 74)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <div class="text-sm text-purple-200 mb-1">Bailleur</div>
  ```


### 📄 `templates/properties/residences_list.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 145)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <div class="text-xs text-purple-200">Bailleur</div>
  ```


### 📄 `templates/properties/appartement_detail.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 370)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <div class="text-sm text-gray-600 mb-1">Bailleur</div>
  ```


### 📄 `templates/properties/property_selection.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 180)

- **Pattern détecté** : `Bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <div class="text-sm text-purple-200">Bailleur</div>
  ```


### 📄 `templates/properties/etat_lieux_form.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 192)

- **Pattern détecté** : `bailleur`
- **Type** : bailleur_reference
- **Description** : Référence à bailleur (devrait être proprietaire)
- **Suggestion** : Remplacer par proprietaire
- **Contexte** :
  ```django
  <span class="text-gray-700">Signé par le bailleur</span>
  ```


### 📄 `apps/payments/templates/payments/list.html`

**1 problème(s) détecté(s)**

#### 🔴 Problème 1 (Ligne 170)

- **Pattern détecté** : `locataire.user.get_full_name`
- **Type** : locataire_user_access
- **Description** : Accès via locataire.user (devrait être direct)
- **Suggestion** : Utiliser locataire.nom_complet, locataire.email, etc.
- **Contexte** :
  ```django
  <div class="text-sm text-gray-900">{{ payment.facture.contrat.locataire.user.get_full_name }}</div>
  ```


## 📖 Guide de Migration

### Patterns de Remplacement

#### 1. Bailleur → Propriétaire

```django
<!-- AVANT -->
{{ residence.bailleur.user.get_full_name }}
{{ residence.bailleur.user.email }}

<!-- APRÈS -->
{{ residence.proprietaire.nom_complet }}
{{ residence.proprietaire.email }}
```

#### 2. Locataire - Accès Direct

```django
<!-- AVANT -->
{{ contrat.locataire.user.get_full_name }}
{{ contrat.locataire.user.email }}
{{ contrat.locataire.user.phone }}

<!-- APRÈS -->
{{ contrat.locataire.nom_complet }}
{{ contrat.locataire.email }}
{{ contrat.locataire.telephone }}
```

#### 3. Boucles et Filtres

```django
<!-- AVANT -->
{% for bailleur in bailleurs %}
  {{ bailleur.user.get_full_name }}
{% endfor %}

<!-- APRÈS -->
{% for proprietaire in proprietaires %}
  {{ proprietaire.nom_complet }}
{% endfor %}
```

#### 4. Initiales (Avatars)

```django
<!-- AVANT -->
{{ locataire.user.first_name.0 }}{{ locataire.user.last_name.0 }}

<!-- APRÈS -->
{{ locataire.prenom.0 }}{{ locataire.nom.0 }}
```

