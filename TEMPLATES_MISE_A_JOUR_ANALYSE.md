# ANALYSE - TEMPLATES À METTRE À JOUR

**Date**: 25 octobre 2025
**Contexte**: Module 4 (Travail Unifié + Demandes d'Achat + Employés Unifiés)
**Objectif**: Identifier et planifier les mises à jour nécessaires des templates existants

---

## 🎯 Nouvelles Fonctionnalités à Intégrer

### 1. **Modèle Travail Unifié**
- ✅ Remplace `Intervention` + `Tache` par un seul modèle `Travail`
- ✅ Champ `nature` distingue: réactif, planifié, préventif, projet
- ✅ Peut créer une demande d'achat liée via `demande_achat` FK
- ✅ Nouveau statut: `en_attente_materiel`

### 2. **Système Demandes d'Achat**
- ✅ Workflow complet de validation
- ✅ Lien bidirectionnel avec Travail
- ✅ 9 templates déjà créés

### 3. **Employés Unifiés**
- ✅ User type unique: `employe` (au lieu de field_agent/technician)
- ✅ Profil `Employe` pour spécialisation
- ✅ Champs: specialite, competences, niveau_experience

---

## 📂 TEMPLATES À CRÉER (Nouveaux)

### A. Module Maintenance - Travail Unifié

#### 1. **templates/maintenance/travail_form.html** ⭐ PRIORITÉ 1
**Remplace**: `intervention_form.html` + `task_form.html`
**Fonction**: Formulaire création/édition Travail

**Champs à inclure**:
```
Section Générale:
- nature (radio: réactif/planifié/préventif/projet)
- type_travail (dropdown)
- titre
- description
- priorite (urgent/haute/normale/basse)

Section Localisation:
- appartement (dropdown avec résidence)
- OU residence seule
- lieu_precis

Section Planification:
- statut
- date_prevue
- date_limite
- assigne_a (employé - dropdown)

Section Coûts:
- cout_estime
- cout_reel
- notes_cout

Section Avancée:
- besoin_materiel (checkbox)
- → Si coché: bouton "Créer demande d'achat"
```

**Boutons d'action**:
- Enregistrer brouillon
- Enregistrer et assigner
- Créer + Demande achat (si besoin_materiel)

---

#### 2. **templates/maintenance/travail_list.html** ⭐ PRIORITÉ 1
**Remplace**: `interventions_list.html` + vue tâches
**Fonction**: Liste unifiée de tous les travaux

**Filtres**:
- Nature (réactif/planifié/préventif/projet)
- Type de travail
- Statut
- Priorité
- Assigné à (employé)
- A une demande d'achat liée (oui/non)
- Dates (plage)

**Colonnes table**:
1. Numéro + Nature (badge)
2. Titre + Type
3. Localisation
4. Assigné à
5. Priorité (badge coloré)
6. Statut (badge coloré)
7. Date prévue
8. Coût estimé
9. Actions

**Vues spéciales**:
- Vue Kanban (par statut)
- Vue Calendrier
- Vue par employé

---

#### 3. **templates/maintenance/travail_detail.html** ⭐ PRIORITÉ 1
**Remplace**: `intervention_detail.html` + `task_detail.html`
**Fonction**: Détail complet d'un travail

**Sections**:
```html
1. En-tête avec badges (nature, priorité, statut)

2. Informations principales
   - Titre, description
   - Type, localisation
   - Dates (prévue, limite, création)
   - Assigné à (avec photo + spécialité)

3. Progression
   - Barre de progression
   - Temps estimé vs réel
   - Checklist (si applicable)

4. Demande d'achat liée (si existe)
   - Card avec résumé
   - Lien vers détail demande
   - Statut demande
   - Montant

5. Médias
   - Photos avant/pendant/après
   - Documents

6. Coûts
   - Estimé vs Réel
   - Détail si demande achat

7. Historique
   - Timeline des changements
   - Qui a fait quoi et quand

8. Actions
   - Modifier
   - Changer statut
   - Assigner/Réassigner
   - Créer demande achat (si pas encore)
   - Marquer terminé
   - Ajouter média
```

---

### B. Module Dashboard

#### 4. **templates/dashboard/forms/nouveau_travail.html** ⭐ PRIORITÉ 2
**Remplace**: `nouvelle_intervention.html` + `nouvelle_tache.html`
**Fonction**: Modal création rapide depuis dashboard

**Version simplifiée du formulaire**:
- Nature (sélection visuelle avec icons)
- Type + Titre
- Appartement
- Priorité
- Assigné à
- Date prévue
- Description courte

**Bouton**: "Créer et voir détail" ou "Créer et créer demande achat"

---

### C. Module Employees - Mobile

#### 5. **templates/employees/mobile/travaux_list.html** ⭐ PRIORITÉ 3
**Remplace**: `work_list.html`
**Fonction**: Liste travaux mobile (unifié)

**Optimisations mobile**:
- Cards au lieu de table
- Swipe actions (terminer, signaler problème)
- Filtres simplifiés
- Pull-to-refresh

---

#### 6. **templates/employees/mobile/travail_detail.html** ⭐ PRIORITÉ 3
**Remplace**: `intervention_detail.html` + `task_detail.html` mobile
**Fonction**: Détail mobile optimisé

**Actions mobiles**:
- Changer statut (dropdown rapide)
- Prendre photo
- Commencer timer
- Signaler besoin matériel → Créer demande
- Marquer terminé

---

## 📝 TEMPLATES À METTRE À JOUR (Existants)

### D. Dashboard Principal

#### 7. **templates/dashboard/index.html** ⭐ PRIORITÉ 2
**Modifications**:
```django
<!-- AVANT -->
<button>Nouvelle Intervention</button>
<button>Nouvelle Tâche</button>

<!-- APRÈS -->
<button>Nouveau Travail</button>

<!-- Widgets stats -->
Stats interventions urgentes → Stats travaux urgents
Stats tâches en retard → Stats travaux en retard
```

**Nouveau widget à ajouter**:
```html
<!-- Widget Demandes d'Achat -->
<div class="stat-card">
    <h3>Demandes d'Achat</h3>
    <p>{{ demandes_en_attente }} en attente validation</p>
    <a href="{% url 'payments:demandes_achat_dashboard' %}">Voir →</a>
</div>
```

---

#### 8. **templates/dashboard/enregistrements.html** ⭐ PRIORITÉ 2
**Modifications**:
```django
<!-- AVANT -->
Tab "Interventions" + Tab "Tâches"

<!-- APRÈS -->
Tab unique "Travaux" avec sous-filtres nature
```

**Boutons modaux**:
- Remplacer 2 boutons par 1 seul: "Nouveau Travail"
- Ajouter bouton: "Nouvelle Demande d'Achat"

---

#### 9. **templates/dashboard/forms/nouvel_employe.html** ⭐ PRIORITÉ 3
**Modifications**:
```django
<!-- AVANT -->
<select name="user_type">
    <option value="field_agent">Agent de terrain</option>
    <option value="technician">Technicien</option>
</select>

<!-- APRÈS -->
<input type="hidden" name="user_type" value="employe">

<!-- Nouveaux champs -->
<select name="specialite">
    <option value="plomberie">Plomberie</option>
    <option value="electricite">Électricité</option>
    <option value="peinture">Peinture</option>
    <option value="menuiserie">Menuiserie</option>
    <option value="climatisation">Climatisation</option>
    <option value="jardinage">Jardinage</option>
    <option value="nettoyage">Nettoyage</option>
    <option value="general">Général</option>
</select>

<select name="niveau_experience">
    <option value="junior">Junior (< 2 ans)</option>
    <option value="intermediaire">Intermédiaire (2-5 ans)</option>
    <option value="senior">Senior (5-10 ans)</option>
    <option value="expert">Expert (> 10 ans)</option>
</select>

<textarea name="competences" placeholder="Compétences spécifiques..."></textarea>
```

---

### E. Templates Employés (Bureau)

#### 10. **templates/employees/tasks_management.html** → RENOMMER
**Nouveau nom**: `templates/employees/travaux_management.html`
**Modifications**:
- Titre: "Gestion des Tâches" → "Gestion des Travaux"
- Ajouter colonne "Nature"
- Ajouter filtre par nature
- Afficher icône si demande achat liée

---

#### 11. **templates/employees/tasks.html** → RENOMMER
**Nouveau nom**: `templates/employees/travaux.html`
**Modifications similaires**

---

### F. Templates Portails

#### 12. **templates/portals/employee/dashboard.html** ⭐ PRIORITÉ 3
**Modifications**:
```django
<!-- Section "Mes Interventions" + "Mes Tâches" -->
<!-- DEVIENT -->
<!-- Section "Mes Travaux" -->

<!-- Nouveau widget -->
<div class="widget">
    <h3>Demandes Matériel en Cours</h3>
    <p>{{ mes_demandes_materiel }} demandes liées à mes travaux</p>
</div>
```

---

#### 13. **templates/portals/employee/interventions.html** → RENOMMER
**Nouveau nom**: `templates/portals/employee/travaux.html`

---

## 🔗 TEMPLATES NÉCESSITANT LIENS VERS DEMANDES ACHAT

### G. Ajout de Liens

#### 14. **templates/dashboard/financial_overview.html**
**Ajout**:
```html
<section class="demandes-achat">
    <h2>Demandes d'Achat Récentes</h2>
    <table>
        <!-- 5 dernières demandes -->
    </table>
    <a href="{% url 'payments:demande_achat_list' %}">Voir toutes</a>
</section>
```

---

#### 15. **templates/dashboard/stats_cards.html** ou **widgets/stats_cards.html**
**Ajout nouvelle card**:
```html
<div class="stat-card bg-purple-50">
    <i class="fas fa-shopping-cart text-purple-600"></i>
    <h3>Demandes d'Achat</h3>
    <div class="stat-number">{{ stats.demandes_achat_mois }}</div>
    <p class="stat-label">Ce mois</p>
    <div class="stat-footer">
        <span>{{ stats.demandes_en_attente }} en attente</span>
    </div>
</div>
```

---

## 📊 RÉSUMÉ PAR PRIORITÉ

### ⭐ PRIORITÉ 1 - CRITIQUE (À créer immédiatement)
1. ✅ **travail_form.html** - Formulaire création/édition
2. ✅ **travail_list.html** - Liste unifiée
3. ✅ **travail_detail.html** - Détail complet

**Raison**: Ce sont les templates de base sans lesquels le système Travail ne peut pas fonctionner.

---

### ⭐ PRIORITÉ 2 - IMPORTANTE (Semaine 1)
4. ✅ **nouveau_travail.html** - Modal dashboard
5. ✅ **dashboard/index.html** - Mise à jour widgets
6. ✅ **dashboard/enregistrements.html** - Unification tabs
7. ✅ **dashboard stats/financial** - Liens demandes achat

**Raison**: Améliore l'expérience utilisateur et intègre les demandes d'achat au dashboard.

---

### ⭐ PRIORITÉ 3 - UTILE (Semaine 2)
8. ✅ **nouvel_employe.html** - Nouveau formulaire employé
9. ✅ **travaux_management.html** - Renommage + adaptations
10. ✅ **Mobile templates** - Adaptations mobile
11. ✅ **Portails employés** - Mise à jour portails

**Raison**: Fonctionnalités secondaires qui peuvent attendre.

---

## 🗂️ TEMPLATES À DÉPRÉCIER (Ne pas supprimer immédiatement)

### À Garder pour Compatibilité (migration progressive)
```
templates/maintenance/intervention_form.html       → Rediriger vers travail_form
templates/maintenance/intervention_detail.html     → Rediriger vers travail_detail
templates/maintenance/interventions_list.html      → Rediriger vers travail_list

templates/dashboard/forms/nouvelle_intervention.html → Rediriger vers nouveau_travail
templates/dashboard/forms/nouvelle_tache.html        → Rediriger vers nouveau_travail

templates/employees/task_form.html                 → Rediriger vers travail_form
templates/employees/task_detail.html               → Rediriger vers travail_detail
```

**Stratégie**:
1. Créer les nouveaux templates
2. Ajouter redirections dans les anciens
3. Afficher message de dépréciation
4. Après 1 mois, supprimer les anciens

---

## 🎨 COMPOSANTS RÉUTILISABLES À CRÉER

### 1. **includes/travail_card.html**
Card Travail réutilisable pour listes et dashboards
```django
{% load static %}
<div class="travail-card" data-id="{{ travail.id }}">
    <div class="card-header">
        <span class="badge badge-{{ travail.nature }}">{{ travail.get_nature_display }}</span>
        <span class="badge badge-{{ travail.priorite }}">{{ travail.get_priorite_display }}</span>
    </div>
    <h3>{{ travail.titre }}</h3>
    <p>{{ travail.description|truncatewords:15 }}</p>

    {% if travail.demande_achat %}
    <div class="demande-badge">
        <i class="fas fa-shopping-cart"></i>
        Demande achat: {{ travail.demande_achat.numero_facture }}
    </div>
    {% endif %}

    <div class="card-footer">
        <span>{{ travail.assigne_a.get_full_name }}</span>
        <span>{{ travail.date_prevue|date:"d/m/Y" }}</span>
    </div>
</div>
```

---

### 2. **includes/travail_status_badge.html**
Badge statut réutilisable
```django
{% if statut == 'signale' %}
    <span class="badge bg-yellow-100 text-yellow-800">Signalé</span>
{% elif statut == 'planifie' %}
    <span class="badge bg-blue-100 text-blue-800">Planifié</span>
{% elif statut == 'assigne' %}
    <span class="badge bg-indigo-100 text-indigo-800">Assigné</span>
{% elif statut == 'en_cours' %}
    <span class="badge bg-purple-100 text-purple-800">En cours</span>
{% elif statut == 'en_attente_materiel' %}
    <span class="badge bg-orange-100 text-orange-800">
        <i class="fas fa-shopping-cart mr-1"></i>Attente matériel
    </span>
{% elif statut == 'en_pause' %}
    <span class="badge bg-gray-100 text-gray-800">En pause</span>
{% elif statut == 'termine' %}
    <span class="badge bg-green-100 text-green-800">Terminé</span>
{% elif statut == 'annule' %}
    <span class="badge bg-red-100 text-red-800">Annulé</span>
{% endif %}
```

---

### 3. **includes/demande_achat_mini_card.html**
Mini-card demande achat (pour afficher dans détail travail)
```django
{% if demande %}
<div class="demande-mini-card bg-purple-50 border-l-4 border-purple-500 p-4">
    <div class="flex justify-between items-start">
        <div>
            <h4 class="font-semibold text-purple-900">
                <i class="fas fa-shopping-cart mr-2"></i>
                Demande d'Achat #{{ demande.numero_facture }}
            </h4>
            <p class="text-sm text-purple-700 mt-1">{{ demande.motif_principal|truncatewords:10 }}</p>
        </div>
        <span class="badge-{{ demande.etape_workflow }}">
            {{ demande.get_etape_workflow_display }}
        </span>
    </div>

    <div class="mt-3 flex justify-between items-center">
        <span class="text-lg font-bold text-purple-600">
            {{ demande.montant_ttc|floatformat:0 }} FCFA
        </span>
        <a href="{% url 'payments:demande_achat_detail' demande.pk %}"
           class="text-purple-600 hover:text-purple-800 text-sm">
            Voir détail →
        </a>
    </div>
</div>
{% endif %}
```

---

## 📋 CHECKLIST FINALE

### Phase 1: Création Templates Critiques
- [ ] Créer `travail_form.html`
- [ ] Créer `travail_list.html`
- [ ] Créer `travail_detail.html`
- [ ] Créer composants réutilisables (cards, badges)

### Phase 2: Intégration Dashboard
- [ ] Créer `nouveau_travail.html` modal
- [ ] Mettre à jour `dashboard/index.html`
- [ ] Mettre à jour `dashboard/enregistrements.html`
- [ ] Ajouter widgets demandes achat

### Phase 3: Adaptation Employés
- [ ] Mettre à jour `nouvel_employe.html`
- [ ] Renommer/adapter templates gestion travaux
- [ ] Mettre à jour templates mobile

### Phase 4: Nettoyage
- [ ] Ajouter redirections dans anciens templates
- [ ] Tester toutes les fonctionnalités
- [ ] Documentation finale
- [ ] Supprimer anciens templates (après période transition)

---

## 🎯 ESTIMATION TEMPS

| Phase | Temps Estimé | Priorité |
|-------|--------------|----------|
| **Phase 1** | 4-6 heures | ⭐⭐⭐ Critique |
| **Phase 2** | 3-4 heures | ⭐⭐ Important |
| **Phase 3** | 2-3 heures | ⭐ Utile |
| **Phase 4** | 1-2 heures | Nettoyage |
| **TOTAL** | **10-15 heures** | |

---

## ✅ PROCHAINES ÉTAPES

1. **Commencer par Phase 1** (templates critiques)
2. Tester chaque template individuellement
3. Créer vues Django correspondantes si manquantes
4. Passer à Phase 2 (dashboard)
5. Finaliser avec adaptations employés et mobile

---

**Auteur**: Claude Code
**Date**: 25 octobre 2025
**Version**: 1.0
