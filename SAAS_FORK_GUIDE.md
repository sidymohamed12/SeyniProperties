# Guide de Fork SaaS - Seyni Platform

## Vue d'Ensemble

Ce document explique la stratégie de fork du projet Seyni (Imani) vers Seyni SaaS.

---

## 🗂️ Structure des Repos

### Repo 1 : `seyni` (Imani - Single Tenant)
- **URL** : (votre repo actuel)
- **Branche principale** : `main`
- **Déploiement** : Railway (Imani Production)
- **Base de données** : PostgreSQL (single tenant)
- **Mode** : `MULTI_TENANT = False`

### Repo 2 : `seyni-saas` (Multi-Tenant)
- **URL** : (à créer)
- **Branche principale** : `main`
- **Déploiement** : Railway (SaaS Production)
- **Base de données** : PostgreSQL (multi-tenant avec `organization_id`)
- **Mode** : `MULTI_TENANT = True`

---

## 📋 Checklist de Création du Repo SaaS

### Phase 1 : Fork Initial (Jour 1)

- [ ] Cloner le repo Imani vers `seyni-saas`
- [ ] Créer nouveau repo GitHub `seyni-saas`
- [ ] Connecter le clone au nouveau remote
- [ ] Premier push

**Commandes :**
```bash
cd c:\Users\user\Desktop
git clone c:\Users\user\Desktop\seyni seyni-saas
cd seyni-saas
git remote remove origin
git remote add origin https://github.com/VOTRE-COMPTE/seyni-saas.git
git push -u origin main
```

### Phase 2 : Nettoyage (Jours 2-3)

- [ ] Supprimer fichiers `.bak` :
  - `apps/contracts/forms.py.bak`
  - `apps/contracts/models.py.bak`
  - `apps/contracts/views.py.bak`
  - `apps/contracts/views_pmo.py.bak`

- [ ] Supprimer/modifier documentation Imani-spécifique :
  - [ ] Créer nouveau `README.md` pour SaaS
  - [ ] Renommer `README.md` actuel en `README_IMANI_ARCHIVE.md`
  - [ ] Créer nouveau `CLAUDE.md` adapté au SaaS

- [ ] Nettoyer configurations :
  - [ ] Modifier `railway.json` pour SaaS
  - [ ] Créer `.env.example.saas`

- [ ] Supprimer fixtures Imani-spécifiques (si existantes)

**Script de nettoyage :**
```bash
# Dans seyni-saas
git checkout -b feature/cleanup

# Supprimer backups
rm apps/contracts/*.bak

# Archiver ancien README
mv README.md README_IMANI_ARCHIVE.md

# Commit
git add .
git commit -m "chore: Clean up Imani-specific files for SaaS fork"
git push origin feature/cleanup
```

### Phase 3 : Corrections Critiques (Semaine 1)

Avant de commencer le SaaS, corriger les bugs critiques identifiés :

- [ ] **Bug 1 : Dépendance manquante**
  ```bash
  # Dans requirements.txt
  # Ajouter : django-cron==0.6.0
  ```

- [ ] **Bug 2 : Commande manquante**
  - [ ] Créer `apps/payments/management/commands/send_payment_reminders.py`
  - [ ] OU retirer du `railway.json`

- [ ] **Bug 3 : Credentials hardcodés**
  - [ ] Nettoyer `seyni_properties/settings.py` lignes 175-177
  - [ ] Utiliser env vars uniquement

- [ ] **Bug 4 : SECRET_KEY par défaut**
  - [ ] Retirer la fallback key de `settings.py`
  - [ ] Forcer l'utilisation de variable d'environnement

### Phase 4 : Architecture Multi-Tenant (Semaines 2-4)

- [ ] **Créer app `organizations`**
  ```bash
  cd seyni-saas
  python manage.py startapp organizations apps/organizations
  ```

- [ ] **Modèles Organizations**
  - [ ] `Organization` (tenant principal)
  - [ ] `OrganizationMembership` (users dans une org)
  - [ ] `Subscription` (abonnements)
  - [ ] `Plan` (plans tarifaires)

- [ ] **Modifier modèles existants**
  - [ ] Ajouter `organization = ForeignKey(Organization, null=True)` à :
    - [ ] `Tiers`
    - [ ] `Residence`
    - [ ] `Appartement`
    - [ ] `RentalContract`
    - [ ] `Invoice`
    - [ ] `Payment`
    - [ ] `Employee`
    - [ ] `Notification`
    - [ ] Tous les autres modèles principaux

- [ ] **Middleware tenant**
  - [ ] Créer `TenantMiddleware`
  - [ ] Détecter tenant via subdomain
  - [ ] Fallback sur session/user

- [ ] **Managers tenant-aware**
  - [ ] Créer `TenantAwareManager`
  - [ ] Appliquer sur tous les modèles

- [ ] **Tests isolation**
  - [ ] Tester qu'un tenant ne peut pas voir les données d'un autre
  - [ ] Tester le filtrage automatique

### Phase 5 : Billing & Subscriptions (Semaines 5-6)

- [ ] **Intégration Stripe**
  - [ ] Créer compte Stripe
  - [ ] Installer `stripe` package
  - [ ] Créer webhook endpoints
  - [ ] Tester en mode test

- [ ] **Plans tarifaires**
  - [ ] Plan Starter (5 appartements, 2 users)
  - [ ] Plan Pro (50 appartements, 10 users)
  - [ ] Plan Enterprise (illimité, illimité)

- [ ] **Gestion limites**
  - [ ] Middleware pour vérifier les quotas
  - [ ] Bloquer si limite atteinte
  - [ ] Afficher upgrade prompts

### Phase 6 : Onboarding (Semaines 7-8)

- [ ] **Landing page SaaS**
  - [ ] Page d'accueil marketing
  - [ ] Pricing page
  - [ ] Features page

- [ ] **Wizard inscription**
  - [ ] Step 1 : Créer compte utilisateur
  - [ ] Step 2 : Créer organization
  - [ ] Step 3 : Choisir plan
  - [ ] Step 4 : Paiement
  - [ ] Step 5 : Onboarding (tutoriel)

- [ ] **Demo automatique**
  - [ ] Générer données de démo
  - [ ] Mode "demo" avec reset quotidien

### Phase 7 : Admin & Analytics (Semaines 9-10)

- [ ] **Super Admin**
  - [ ] Vue de toutes les organizations
  - [ ] Statistiques globales
  - [ ] Gestion des suspensions
  - [ ] Support client intégré

- [ ] **Analytics par tenant**
  - [ ] Dashboard metrics
  - [ ] Rapports exportables
  - [ ] Graphiques

### Phase 8 : Polish & Launch (Semaines 11-12)

- [ ] **Tests complets**
  - [ ] Tests unitaires (80%+ couverture)
  - [ ] Tests d'intégration
  - [ ] Tests E2E (Playwright/Selenium)
  - [ ] Load testing (Locust)

- [ ] **Documentation**
  - [ ] API docs (Swagger)
  - [ ] Guide utilisateur
  - [ ] Guide admin
  - [ ] Changelog

- [ ] **Beta launch**
  - [ ] 3-5 beta clients
  - [ ] Feedback loop
  - [ ] Itérations rapides

- [ ] **Production**
  - [ ] Migration base de données
  - [ ] Monitoring (Sentry)
  - [ ] Logs (Papertrail)
  - [ ] Backups automatiques

---

## 🔄 Synchronisation des Repos

### Quand Corriger un Bug

**Si le bug affecte les deux projets :**

1. **Corriger dans Imani** (repo `seyni`) :
   ```bash
   cd c:\Users\user\Desktop\seyni
   git checkout -b fix/bug-description
   # ... corriger le bug
   git commit -m "fix: description"
   git push origin fix/bug-description
   ```

2. **Cherry-pick dans SaaS** (repo `seyni-saas`) :
   ```bash
   cd c:\Users\user\Desktop\seyni-saas

   # Ajouter le repo Imani comme remote
   git remote add imani c:\Users\user\Desktop\seyni
   git fetch imani

   # Cherry-pick le commit
   git cherry-pick <commit-hash>
   git push origin main
   ```

**Si le bug est spécifique à un repo :**
- Corriger uniquement dans ce repo

### Partager une Nouvelle Feature

**Si feature utile pour les deux :**

Option A : Développer dans Imani, porter vers SaaS
Option B : Développer dans SaaS (sans logique multi-tenant), porter vers Imani

**Recommandation** : Développer les features business dans Imani (plus simple), puis porter vers SaaS.

---

## 📊 Différences Clés Entre les Repos

| Aspect | Seyni (Imani) | Seyni SaaS |
|--------|---------------|------------|
| **Tenant** | Single (Imani uniquement) | Multi (plusieurs entreprises) |
| **Organization field** | N/A | Sur tous les modèles |
| **Middleware** | Standard | TenantMiddleware |
| **Managers** | Standard | TenantAwareManager |
| **Apps** | 13 apps | 14 apps (+ organizations) |
| **Settings** | Simples | Mode-aware (MULTI_TENANT) |
| **Billing** | N/A | Stripe + subscriptions |
| **Onboarding** | Admin crée users | Self-service signup |
| **Domain** | imani.seyni.sn | *.seyni.sn |
| **Database** | Shared schema | Shared schema + org_id |
| **Tests** | Minimal | Comprehensive |
| **Security** | Standard | Renforcée (isolation) |

---

## 🚀 Commandes Utiles

### Développement Local

**Imani :**
```bash
cd c:\Users\user\Desktop\seyni
python manage.py runserver 8000
```

**SaaS :**
```bash
cd c:\Users\user\Desktop\seyni-saas
python manage.py runserver 8001
```

### Tests

**Imani :**
```bash
cd c:\Users\user\Desktop\seyni
python manage.py test
```

**SaaS :**
```bash
cd c:\Users\user\Desktop\seyni-saas
python manage.py test

# Tests spécifiques multi-tenancy
python manage.py test apps.organizations
python manage.py test apps.tiers.tests.TenantIsolationTests
```

### Migrations

**Imani :**
```bash
python manage.py makemigrations
python manage.py migrate
```

**SaaS :**
```bash
# Créer migrations pour organizations
python manage.py makemigrations organizations

# Ajouter organization_id à tous les modèles
python manage.py makemigrations

# Appliquer
python manage.py migrate
```

---

## ⚠️ Pièges à Éviter

### 1. Ne Pas Tester l'Isolation
**Problème** : Un tenant voit les données d'un autre
**Solution** : Tests automatisés d'isolation dans chaque model test

### 2. Oublier organization_id dans une Query
**Problème** : Fuite de données cross-tenant
**Solution** : Toujours utiliser les managers custom, jamais `.all_objects`

### 3. Hardcoder des IDs
**Problème** : `if organization_id == 1:` (logique spéciale Imani)
**Solution** : Utiliser des flags ou settings

### 4. Partager des Secrets
**Problème** : API keys Stripe dans les deux repos
**Solution** : Secrets séparés, même en dev

### 5. Dupliquer les Migrations
**Problème** : Conflits de numéros de migrations
**Solution** : Ne JAMAIS copier les fichiers de migration, toujours recréer

---

## 📝 Variables d'Environnement

### Seyni (Imani) - `.env`
```bash
SECRET_KEY=...
DATABASE_URL=postgresql://...
DEPLOYMENT_MODE=IMANI
MULTI_TENANT=False

# Imani specific
COMPANY_NAME="Imani Properties"
ALLOWED_HOSTS=imani.seyni.sn,localhost
```

### Seyni SaaS - `.env`
```bash
SECRET_KEY=...
DATABASE_URL=postgresql://...
DEPLOYMENT_MODE=SAAS
MULTI_TENANT=True

# SaaS specific
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

ALLOWED_HOSTS=*.seyni.sn,localhost
```

---

## 🎯 Success Metrics

### Imani (Stabilité)
- ✅ Zéro downtime
- ✅ Bugs critiques < 1 par mois
- ✅ Performance stable
- ✅ Users satisfaits

### SaaS (Croissance)
- ✅ 10 organizations en beta (Mois 3)
- ✅ 50 organizations (Mois 6)
- ✅ 200 organizations (Mois 12)
- ✅ Churn < 5%
- ✅ Uptime > 99.9%

---

## 📞 Questions / Décisions

### Décisions Architecturales

**Q : Database per tenant ou Shared database ?**
**R : Shared database avec `organization_id`** (plus simple, moins cher)

**Q : Subdomains ou Path-based ?**
**R : Subdomains** (`acme.seyni.sn` vs `seyni.sn/acme`)

**Q : Soft delete ou Hard delete ?**
**R : Soft delete** (ajouter `deleted_at` partout)

**Q : Isolation niveau query ou middleware ?**
**R : Les deux** (defense in depth)

---

## 🔗 Ressources

- [Django Multi-Tenant Best Practices](https://books.agiliq.com/projects/django-multi-tenant/en/latest/)
- [Stripe Billing Documentation](https://stripe.com/docs/billing)
- [Row-Level Security in PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Django Tenants (library)](https://django-tenants.readthedocs.io/)

---

**Dernière mise à jour** : 2025-10-30
**Auteur** : Équipe Seyni Platform
