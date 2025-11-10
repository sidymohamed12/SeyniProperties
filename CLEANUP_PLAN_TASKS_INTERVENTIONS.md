# Plan de nettoyage - Suppression ancienne logique Tâches & Interventions

**Date**: 25 Octobre 2025
**Objectif**: Supprimer proprement l'ancienne logique séparée Tâches/Interventions
**Nouveau système**: Travaux unifié (Travail model)

---

## 📋 Fichiers à supprimer (13 fichiers - Total estimé: ~6000+ lignes)

### Phase 1: Dashboard Forms (SÛRE) ✅
**Impact**: Faible - Modals seulement

- ❌ `templates/dashboard/forms/nouvelle_intervention.html` (140 lignes)
- ❌ `templates/dashboard/forms/nouvelle_tache.html` (70 lignes)

**Raison**: Remplacés par `nouveau_travail.html`

---

### Phase 2: Maintenance Templates (Interventions) ⚠️
**Impact**: Moyen - Ancien système maintenance

- ❌ `templates/maintenance/interventions_list.html` (400 lignes)
- ❌ `templates/maintenance/intervention_detail.html` (997 lignes)
- ❌ `templates/maintenance/intervention_form.html` (427 lignes)

**Raison**: Remplacés par `travail_list.html`, `travail_detail.html`, `travail_form.html`

**Vérifications requises**:
- ✅ Vues utilisent déjà les nouveaux templates (fait précédemment)
- ⏳ Aucune référence directe dans d'autres templates

---

### Phase 3: Employee Portal Templates (Tâches) ✅ COMPLET
**Impact**: Moyen - Ancien système employés

- ✅ `templates/employees/task_form.html` (457 lignes) - SUPPRIMÉ
- ✅ `templates/employees/task_detail.html` (816 lignes) - SUPPRIMÉ
- ✅ `templates/employees/tasks.html` (~2000 lignes) - SUPPRIMÉ
- ✅ `templates/employees/tasks_management.html` (~1200 lignes) - SUPPRIMÉ

**Total**: 4 fichiers (~4473 lignes supprimées)

**Raison**: Système Tasks séparé remplacé par Travaux unifié

**Vérifications effectuées**:
- ✅ Tous les templates sauvegardés dans `backup_old_templates_20251025/`
- ✅ 5 vues mises à jour dans `apps/employees/views.py`:
  - TasksListView → Redirection vers `maintenance:travail_list`
  - task_detail_view → Redirection intelligente (mobile/Travaux)
  - TaskCreateView → Redirection vers `maintenance:travail_create`
  - TaskUpdateView → Redirection vers `maintenance:travail_list`
  - task_delete_view → Redirection vers `maintenance:travail_list`
- ✅ Messages informatifs ajoutés pour tous les redirects
- ✅ Interface mobile préservée pour employés terrain

**Documentation**: Voir [CLEANUP_PHASE3_EMPLOYEES_RAPPORT.md](CLEANUP_PHASE3_EMPLOYEES_RAPPORT.md)

---

### Phase 4: Mobile Templates (Tâches & Interventions) ⏸️ EN PAUSE
**Impact**: Élevé - Interface mobile field agents
**Décision**: CONSERVÉS comme référence pour futur portail employé

- ⏸️ `templates/employees/mobile/interventions_list.html` (1043 lignes)
- ⏸️ `templates/employees/mobile/intervention_detail.html` (~600 lignes)
- ⏸️ `templates/employees/mobile/tasks_list.html` (~500 lignes)
- ⏸️ `templates/employees/mobile/task_detail.html` (~816 lignes)
- ⏸️ `templates/employees/mobile/task_complete_form.html` (~300 lignes)
- ⏸️ `templates/employees/mobile/work_list.html` (~600 lignes)
- ⏸️ `templates/employees/mobile/dashboard.html` (~400 lignes)
- ⏸️ `templates/employees/mobile/schedule.html` (~300 lignes)
- ⏸️ `templates/employees/mobile/modals/` (3 fichiers)

**Total conservé**: ~11 fichiers (~3,500+ lignes)

**Raison de conservation**:
- ✅ Interface mobile fonctionnelle pour employés terrain
- ✅ Référence UX/UI pour futur portail employé unifié
- ✅ Patterns d'interaction tactile à réutiliser
- ✅ Composants (caméra, géolocalisation, timer) à migrer

**Décision documentée**: Voir [PHASE4_MOBILE_DECISION.md](PHASE4_MOBILE_DECISION.md)

---

## 🔍 Vérifications préalables

### 1. Rechercher références dans le code

```bash
# Chercher références aux anciens templates
grep -r "intervention_form.html" apps/ templates/
grep -r "intervention_detail.html" apps/ templates/
grep -r "interventions_list.html" apps/ templates/
grep -r "task_form.html" apps/ templates/
grep -r "task_detail.html" apps/ templates/
grep -r "tasks.html" apps/ templates/
grep -r "nouvelle_intervention.html" apps/ templates/
grep -r "nouvelle_tache.html" apps/ templates/
```

### 2. Vérifier les vues

```bash
# Chercher dans apps/maintenance/views.py
grep "intervention_form.html" apps/maintenance/views.py
grep "intervention_detail.html" apps/maintenance/views.py
grep "interventions_list.html" apps/maintenance/views.py

# Chercher dans apps/employees/views.py
grep "task_form.html" apps/employees/views.py
grep "task_detail.html" apps/employees/views.py
grep "tasks.html" apps/employees/views.py
```

### 3. Vérifier les URLs

```bash
# Chercher URLs intervention/task
grep -E "(intervention|task)" apps/maintenance/urls.py
grep -E "(intervention|task)" apps/employees/urls.py
grep -E "(intervention|task)" apps/employees/mobile_urls.py
```

---

## ⚙️ Ordre d'exécution recommandé

### Étape 1: Backup (SÉCURITÉ)
```bash
# Créer backup des fichiers avant suppression
mkdir backup_old_templates_$(date +%Y%m%d)
cp templates/dashboard/forms/nouvelle_intervention.html backup_old_templates_$(date +%Y%m%d)/
cp templates/dashboard/forms/nouvelle_tache.html backup_old_templates_$(date +%Y%m%d)/
cp templates/maintenance/intervention*.html backup_old_templates_$(date +%Y%m%d)/
cp templates/employees/task*.html backup_old_templates_$(date +%Y%m%d)/
cp templates/employees/tasks*.html backup_old_templates_$(date +%Y%m%d)/
cp -r templates/employees/mobile/*intervention*.html backup_old_templates_$(date +%Y%m%d)/ 2>/dev/null
cp -r templates/employees/mobile/*task*.html backup_old_templates_$(date +%Y%m%d)/ 2>/dev/null
```

### Étape 2: Phase 1 - Dashboard Forms (SÛRE)
```bash
# Supprimer les anciens modals dashboard
rm templates/dashboard/forms/nouvelle_intervention.html
rm templates/dashboard/forms/nouvelle_tache.html

# Tester que le dashboard fonctionne toujours
# Vérifier que nouveau_travail.html est bien utilisé
```

### Étape 3: Phase 2 - Maintenance Templates
```bash
# Vérifier qu'aucune vue n'utilise ces templates
grep -r "interventions_list.html\|intervention_detail.html\|intervention_form.html" apps/

# Si aucun résultat, supprimer
rm templates/maintenance/interventions_list.html
rm templates/maintenance/intervention_detail.html
rm templates/maintenance/intervention_form.html

# Tester /maintenance/travaux/ et /maintenance/travaux/create/
```

### Étape 4: Phase 3 - Employee Task Templates
```bash
# Vérifier qu'aucune vue n'utilise ces templates
grep -r "task_form.html\|task_detail.html\|tasks.html\|tasks_management.html" apps/

# Si aucun résultat, supprimer
rm templates/employees/task_form.html
rm templates/employees/task_detail.html
rm templates/employees/tasks.html
rm templates/employees/tasks_management.html

# Tester /employees/ et navigation
```

### Étape 5: Phase 4 - Mobile Templates
```bash
# IMPORTANT: Vérifier existence des nouveaux templates mobiles AVANT
ls -la templates/employees/mobile/work*.html

# Vérifier qu'aucune vue mobile n'utilise les anciens templates
grep -r "intervention.*html\|task.*html" apps/employees/mobile_urls.py apps/employees/views.py

# Si sûr, supprimer
rm templates/employees/mobile/interventions_list.html
rm templates/employees/mobile/intervention_detail.html
rm templates/employees/mobile/tasks_list.html
rm templates/employees/mobile/task_detail.html
rm templates/employees/mobile/task_complete_form.html

# Tester interface mobile field agents
```

---

## 🧪 Tests après chaque phase

### Tests Dashboard
- [ ] Page dashboard accessible
- [ ] Bouton "Enregistrements" fonctionne
- [ ] Modal "Nouveau Travail" s'ouvre (pas nouvelle_intervention ni nouvelle_tache)

### Tests Maintenance
- [ ] `/maintenance/travaux/` affiche liste
- [ ] `/maintenance/travaux/create/` affiche formulaire
- [ ] `/maintenance/travaux/<id>/` affiche détail
- [ ] `/maintenance/travaux/<id>/edit/` affiche édition
- [ ] Aucune erreur TemplateDoesNotExist

### Tests Employés
- [ ] `/employees/` affiche liste employés
- [ ] Menu Employés dans sidebar fonctionne
- [ ] Aucune référence aux anciennes "Tâches"

### Tests Mobile
- [ ] Interface mobile field agents accessible
- [ ] Liste des travaux mobile fonctionne
- [ ] Détail travail mobile fonctionne
- [ ] Offline/PWA features fonctionnent

---

## 📊 Estimation impact

### Lignes de code supprimées
- **Dashboard**: ~210 lignes
- **Maintenance**: ~1824 lignes
- **Employees**: ~1273+ lignes (estimation conservative)
- **Mobile**: ~1043+ lignes (estimation conservative)

**TOTAL ESTIMÉ**: ~4350+ lignes de code supprimées

### Bénéfices
- ✅ Code base plus propre et maintenable
- ✅ Moins de confusion pour les développeurs
- ✅ Pas de logique dupliquée
- ✅ Architecture unifiée "Travaux"
- ✅ Templates plus faciles à trouver et maintenir

### Risques
- ⚠️ Si backup non fait: perte de code
- ⚠️ Si vérifications non faites: erreurs 404/TemplateDoesNotExist
- ⚠️ Si mobile non testé: field agents bloqués

---

## 📝 Checklist avant suppression

**OBLIGATOIRE avant toute suppression**:

- [ ] ✅ Backup créé dans `backup_old_templates_YYYYMMDD/`
- [ ] ✅ Vérifications grep effectuées (aucune référence)
- [ ] ✅ Vues mises à jour pour utiliser nouveaux templates
- [ ] ✅ URLs pointent vers nouvelles vues
- [ ] ✅ Tests manuels effectués sur environnement de dev
- [ ] ✅ Accès mobile field agents vérifié
- [ ] ✅ Git commit avant suppression (possibilité rollback)

---

## 🔄 Plan de rollback (en cas de problème)

### Si erreur après suppression Phase 1
```bash
cp backup_old_templates_*/nouvelle_intervention.html templates/dashboard/forms/
cp backup_old_templates_*/nouvelle_tache.html templates/dashboard/forms/
```

### Si erreur après suppression Phase 2
```bash
cp backup_old_templates_*/intervention*.html templates/maintenance/
```

### Si erreur après suppression Phase 3
```bash
cp backup_old_templates_*/task*.html templates/employees/
```

### Si erreur après suppression Phase 4
```bash
cp backup_old_templates_*/*intervention*.html templates/employees/mobile/
cp backup_old_templates_*/*task*.html templates/employees/mobile/
```

### Rollback complet (git)
```bash
git checkout HEAD -- templates/
```

---

## 📅 Calendrier recommandé

**Jour 1**: Vérifications et backup
- Exécuter toutes les vérifications grep
- Créer backup complet
- Tester système Travaux complet

**Jour 2**: Phase 1 (Dashboard)
- Supprimer dashboard forms
- Tester dashboard
- Commit git

**Jour 3**: Phase 2 (Maintenance)
- Supprimer maintenance templates
- Tester toutes URLs /maintenance/travaux/*
- Commit git

**Jour 4**: Phase 3 (Employees)
- Supprimer employee templates
- Tester portal employés
- Commit git

**Jour 5**: Phase 4 (Mobile) + Documentation
- Supprimer mobile templates (APRÈS tests approfondis)
- Tester interface mobile complète
- Mettre à jour documentation
- Commit final

---

## ✅ Critères de succès

**La suppression est réussie si**:

1. ✅ Aucune erreur TemplateDoesNotExist
2. ✅ Toutes les URLs fonctionnent
3. ✅ Interface mobile field agents fonctionne
4. ✅ Dashboard accessible et fonctionnel
5. ✅ Système Travaux 100% opérationnel
6. ✅ Tests manuels complets passent
7. ✅ Git history propre avec commits logiques

---

**Prêt à commencer le nettoyage?**
**Commençons par Phase 1 (Dashboard Forms) qui est la plus sûre!**

---

**Fin du plan**
Date: 25 Octobre 2025
