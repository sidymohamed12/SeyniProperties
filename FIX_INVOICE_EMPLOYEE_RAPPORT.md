# Corrections - Factures et Employés

**Date**: 25 Octobre 2025
**Statut**: ✅ COMPLET

---

## 🎯 Objectifs

1. Corriger l'erreur NoReverseMatch sur les factures de demande d'achat
2. Ajouter la possibilité de créer un nouvel employé depuis la page employés

---

## 1️⃣ Correction erreur facture demande d'achat

### Problème

```
NoReverseMatch at /payments/factures/5/
Reverse for 'detail' with arguments '('',)' not found.
1 pattern(s) tried: ['contracts/(?P<pk>[0-9]+)/\\Z']
```

**Cause**: Le template [templates/payments/invoice_detail.html](templates/payments/invoice_detail.html:167) essayait d'afficher la section "Contrat associé" pour toutes les factures, mais les factures de type `demande_achat` n'ont pas de contrat associé (`invoice.contrat` est `None`).

### Solution

Ajout d'une condition `{% if invoice.contrat %}` autour de la section "Contrat associé":

**Fichier modifié**: [templates/payments/invoice_detail.html](templates/payments/invoice_detail.html:156-188)

```django
<!-- Contrat associé (seulement pour factures de loyer) -->
{% if invoice.contrat %}
<div class="info-card">
    <h2 class="section-header text-xl font-semibold text-gray-900">
        <i class="fas fa-file-contract text-purple-600 mr-2"></i>
        Contrat associé
    </h2>

    <div class="space-y-3">
        <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Numéro de contrat</label>
            <p class="text-lg text-gray-900">
                <a href="{% url 'contracts:detail' invoice.contrat.pk %}"
                   class="text-blue-600 hover:text-blue-800">
                    {{ invoice.contrat.numero_contrat }}
                </a>
            </p>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Locataire</label>
            <p class="text-lg text-gray-900">{{ invoice.contrat.locataire.nom_complet }}</p>
        </div>

        <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Bien</label>
            <p class="text-lg text-gray-900">
                {{ invoice.contrat.appartement.residence.nom }} - {{ invoice.contrat.appartement.nom }}
            </p>
        </div>
    </div>
</div>
{% endif %}
```

### Résultat

✅ Les factures de loyer affichent toujours la section contrat
✅ Les factures de demande d'achat n'affichent plus cette section
✅ Plus d'erreur NoReverseMatch

---

## 2️⃣ Création d'employé

### Objectif

Permettre aux managers de créer de nouveaux employés directement depuis la page [/employees/](http://127.0.0.1:8000/employees/)

### Fichiers créés/modifiés

#### 1. Vue de création

**Fichier**: [apps/employees/views.py](apps/employees/views.py:398-433)

```python
@login_required
def employee_create_view(request):
    """Créer un nouvel employé"""
    if not request.user.user_type in ['manager', 'accountant']:
        messages.error(request, "Vous n'avez pas l'autorisation de créer des employés.")
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()

            # Récupérer les identifiants générés
            credentials = employee._login_credentials if hasattr(employee, '_login_credentials') else None

            if credentials:
                messages.success(
                    request,
                    f"Employé {employee.user.get_full_name()} créé avec succès! "
                    f"Identifiants: {credentials['username']} / {credentials['password']}"
                )
            else:
                messages.success(request, f"Employé {employee.user.get_full_name()} créé avec succès!")

            return redirect('employees:employee_detail', employee_id=employee.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = EmployeeForm()

    context = {
        'form': form,
        'title': 'Nouvel employé',
    }

    return render(request, 'employees/employee_form.html', context)
```

**Caractéristiques**:
- ✅ Vérification des permissions (manager/accountant uniquement)
- ✅ Utilise le `EmployeeForm` existant (déjà dans le code)
- ✅ Génère automatiquement un compte utilisateur
- ✅ Génère un nom d'utilisateur et mot de passe temporaire
- ✅ Affiche les identifiants dans le message de succès
- ✅ Redirige vers la page détail de l'employé créé

#### 2. Route URL

**Fichier**: [apps/employees/urls.py](apps/employees/urls.py:26)

```python
# ✅ EMPLOYÉS (vues qui existent dans employees)
path('employee/create/', views.employee_create_view, name='employee_create'),
path('employee/<int:employee_id>/', views.employee_detail_view, name='employee_detail'),
```

**URL**: `/employees/employee/create/`

#### 3. Template de formulaire

**Fichier**: [templates/employees/employee_form.html](templates/employees/employee_form.html) (NOUVEAU - 243 lignes)

**Sections du formulaire**:

1. **Informations personnelles**
   - Prénom (requis)
   - Nom (requis)
   - Email (requis)
   - Téléphone (requis)

2. **Profil employé**
   - Type d'employé: Agent de terrain / Technicien (requis)
   - Spécialité (optionnel)
   - Date d'embauche (auto-rempli avec aujourd'hui)
   - Salaire (optionnel)

3. **Informations importantes**
   - Encadré bleu expliquant la génération automatique du compte
   - Avertissement de noter les identifiants générés

**Design**:
- ✅ Style Imani cohérent avec le reste de l'app
- ✅ Validation frontend et backend
- ✅ Messages d'erreur inline
- ✅ Responsive (mobile-first)
- ✅ Icônes Font Awesome
- ✅ Boutons d'action (Annuler / Créer)

#### 4. Bouton dans la liste

**Fichier**: [templates/employees/manager_list.html](templates/employees/manager_list.html:59-61)

```html
<a href="{% url 'employees:employee_create' %}"
   class="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:opacity-90 transition-all shadow-md">
    <i class="fas fa-user-plus mr-2"></i>Nouvel employé
</a>
```

**Position**: En haut à droite de la page, à côté du bouton "Voir les travaux"

---

## 📋 Fonctionnalités de création d'employé

### Formulaire EmployeeForm

Le formulaire utilise `EmployeeForm` existant qui:

1. **Crée automatiquement un compte User** avec:
   - Username: `agent_terrain_001`, `technicien_002`, etc. (auto-incrémenté)
   - Mot de passe: 8 caractères aléatoires (lettres + chiffres)
   - Email, nom, prénom, téléphone
   - Type d'utilisateur: `agent_terrain` ou `technicien`

2. **Crée le profil Employee** avec:
   - Lien vers le User créé
   - Spécialité (plomberie, électricité, peinture, etc.)
   - Date d'embauche (par défaut: aujourd'hui)
   - Salaire

3. **Retourne les identifiants** via `employee._login_credentials`:
   ```python
   {
       'username': 'technicien_005',
       'password': 'Xy8kL2mP'
   }
   ```

### Affichage des identifiants

Après création, un message de succès s'affiche:

```
✅ Employé Jean Dupont créé avec succès!
Identifiants: technicien_005 / Xy8kL2mP
```

**Important**: Ces identifiants sont affichés **UNE SEULE FOIS**. L'administrateur doit les noter et les communiquer à l'employé.

### Sécurité

- ✅ Permissions vérifiées (seuls managers et comptables)
- ✅ Mot de passe temporaire sécurisé (8 caractères aléatoires)
- ✅ L'employé peut changer son mot de passe après première connexion
- ✅ Validation des emails (unicité)
- ✅ Protection CSRF

---

## 🎨 Workflow complet

### 1. Accès à la page employés

Manager se connecte → Dashboard → Employés (`/employees/`)

### 2. Création d'un nouvel employé

1. Clic sur **"Nouvel employé"** (bouton bleu)
2. Remplir le formulaire:
   - Informations personnelles (prénom, nom, email, téléphone)
   - Type d'employé (agent de terrain / technicien)
   - Spécialité (optionnel)
   - Date d'embauche (pré-remplie)
   - Salaire (optionnel)
3. Clic sur **"Créer l'employé"**

### 3. Résultat

- ✅ Compte utilisateur créé automatiquement
- ✅ Message de succès avec identifiants affichés
- ✅ Redirection vers page détail de l'employé
- ✅ L'employé apparaît dans la liste

### 4. Communication des identifiants

Le manager note les identifiants affichés et les communique à l'employé:
- **Username**: `technicien_005`
- **Mot de passe**: `Xy8kL2mP`

L'employé peut se connecter sur `/accounts/login/` et accéder à l'interface mobile.

---

## 🧪 Tests à effectuer

### Test 1: Facture de loyer (avec contrat)

```
1. Créer/ouvrir une facture de type loyer
2. Aller sur /payments/factures/<id>/
3. ✅ Vérifier que la section "Contrat associé" s'affiche
4. ✅ Vérifier le lien vers le contrat fonctionne
5. ✅ Vérifier l'affichage du locataire et du bien
```

### Test 2: Facture de demande d'achat (sans contrat)

```
1. Créer/ouvrir une facture de type demande_achat
2. Aller sur /payments/factures/<id>/
3. ✅ Vérifier que la section "Contrat associé" n'apparaît PAS
4. ✅ Vérifier qu'aucune erreur ne s'affiche
5. ✅ Vérifier les autres sections (montant, statut, etc.) fonctionnent
```

### Test 3: Création d'employé

```
1. Se connecter en tant que manager
2. Aller sur /employees/
3. Cliquer sur "Nouvel employé"
4. Remplir le formulaire:
   - Prénom: "Jean"
   - Nom: "Dupont"
   - Email: "jean.dupont@example.com"
   - Téléphone: "+221 77 123 45 67"
   - Type: "Technicien"
   - Spécialité: "Plomberie"
5. Cliquer sur "Créer l'employé"
6. ✅ Vérifier le message de succès avec identifiants
7. ✅ Vérifier la redirection vers page détail
8. ✅ Vérifier que l'employé apparaît dans la liste
9. ✅ Se déconnecter et tester connexion avec les identifiants générés
```

### Test 4: Permissions

```
1. Se connecter en tant que locataire (tenant)
2. Essayer d'accéder /employees/employee/create/
3. ✅ Vérifier redirection vers dashboard
4. ✅ Vérifier message d'erreur de permissions
```

### Test 5: Validation formulaire

```
1. Aller sur /employees/employee/create/
2. Soumettre le formulaire vide
3. ✅ Vérifier affichage des erreurs de validation
4. Remplir avec email invalide
5. ✅ Vérifier erreur de validation email
```

---

## 📊 Résumé des modifications

### Fichiers modifiés

1. ✅ [templates/payments/invoice_detail.html](templates/payments/invoice_detail.html) - Ajout condition `{% if invoice.contrat %}`
2. ✅ [apps/employees/views.py](apps/employees/views.py:398-433) - Ajout `employee_create_view`
3. ✅ [apps/employees/urls.py](apps/employees/urls.py:26) - Ajout route `employee/create/`
4. ✅ [templates/employees/manager_list.html](templates/employees/manager_list.html:59-61) - Ajout bouton "Nouvel employé"

### Fichiers créés

1. ✅ [templates/employees/employee_form.html](templates/employees/employee_form.html) - Nouveau template (243 lignes)
2. ✅ [FIX_INVOICE_EMPLOYEE_RAPPORT.md](FIX_INVOICE_EMPLOYEE_RAPPORT.md) - Ce rapport

### Lignes de code

- **Modifiées**: ~40 lignes
- **Créées**: ~280 lignes
- **Total**: ~320 lignes

---

## ✨ Résultat final

### Avant

❌ Erreur NoReverseMatch sur factures demande d'achat
❌ Impossible de créer un employé depuis l'interface

### Après

✅ Toutes les factures fonctionnent (avec ou sans contrat)
✅ Bouton "Nouvel employé" dans la liste
✅ Formulaire complet de création d'employé
✅ Génération automatique du compte utilisateur
✅ Affichage des identifiants temporaires
✅ Permissions vérifiées
✅ Interface cohérente avec le design Imani

---

## 🔜 Améliorations futures possibles

1. **Export des identifiants**: Bouton pour télécharger un PDF avec les identifiants
2. **Email automatique**: Envoyer les identifiants par email à l'employé
3. **Import en masse**: Importer plusieurs employés depuis un fichier CSV/Excel
4. **QR Code**: Générer un QR code avec les identifiants pour faciliter la connexion mobile
5. **Gestion des permissions avancées**: Rôles personnalisés au-delà d'agent/technicien
6. **Historique**: Tracker les modifications de profil employé

---

**Fin du rapport**
**Date**: 25 Octobre 2025
**Statut**: ✅ COMPLET
