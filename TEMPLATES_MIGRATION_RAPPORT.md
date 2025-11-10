# Rapport de Migration des Templates - Architecture Travaux ↔ Demandes d'Achat

**Date**: 2025-10-28
**Type**: Migration Architecture 1-to-Many
**Impact**: Templates et Vues Python

---

## 📋 Résumé des Modifications

### Changement Architectural

**AVANT** (Relation 1-to-1 redondante):
```python
# Travail
demande_achat = ForeignKey(Invoice)  # ❌ Supprimé

# Invoice
travail_lie = ForeignKey(Travail, related_name='demandes_achat_liees')  # ❌ Ancien
```

**APRÈS** (Relation 1-to-Many propre):
```python
# Travail
# Plus de champ demande_achat - Accès via reverse relation

# Invoice
travail_lie = ForeignKey(Travail, related_name='demandes_achat')  # ✅ Nouveau
```

**Accès dans le code**:
```python
# ❌ AVANT
travail.demande_achat  # Une seule demande

# ✅ APRÈS
travail.demandes_achat.all()  # Plusieurs demandes possibles
travail.necessite_materiel  # Property boolean
travail.statut_materiel  # 'aucun_materiel', 'en_attente_validation', etc.
travail.cout_total_materiel  # Decimal - somme de toutes les demandes
```

---

## 🎨 Templates Modifiés

### 1. **travail_detail.html** ✅

**Fichier**: [templates/maintenance/travail_detail.html](templates/maintenance/travail_detail.html)

**Modifications** (2 endroits):

#### A. Section Demandes d'Achat (Ligne 280-413)

**AVANT**:
```django
{% if demande_achat %}
    <div class="bg-purple-50">
        <!-- Affichage d'UNE SEULE demande -->
        <p>{{ demande_achat.numero_facture }}</p>
    </div>
{% else %}
    <!-- Proposition créer demande -->
{% endif %}
```

**APRÈS**:
```django
{% if travail.demandes_achat.exists %}
    <div class="bg-purple-50">
        <h2>Demandes d'Achat Liées</h2>
        <p>{{ travail.demandes_achat.count }} demande(s) -
           Coût total: {{ travail.cout_total_materiel|floatformat:0 }} FCFA</p>

        <!-- Badge statut matériel global -->
        {% if travail.statut_materiel == 'materiel_recu' %}
            <span class="badge bg-green">Matériel reçu</span>
        {% elif travail.statut_materiel == 'en_attente_reception' %}
            <span class="badge bg-orange">En attente réception</span>
        {% endif %}

        <!-- Liste TOUTES les demandes -->
        {% for demande_achat in travail.demandes_achat.all %}
            <div class="demande-card">
                <p>{{ demande_achat.numero_facture }}</p>
                <span class="badge">{{ demande_achat.get_etape_workflow_display }}</span>
                <a href="{% url 'payments:demande_achat_detail' demande_achat.pk %}">
                    Voir détails
                </a>
            </div>
        {% endfor %}

        <!-- Bouton ajouter AUTRE demande -->
        <a href="{% url 'payments:demande_achat_create' %}?travail_id={{ travail.id }}">
            + Ajouter une demande d'achat
        </a>
    </div>
{% else %}
    <!-- Proposition créer PREMIÈRE demande -->
{% endif %}
```

**Avantages**:
- ✅ Affiche TOUTES les demandes liées
- ✅ Affiche le coût total matériel
- ✅ Badge statut matériel global
- ✅ Permet d'ajouter plusieurs demandes

#### B. Bouton Actions Sidebar (Ligne 534-544)

**AVANT**:
```django
{% if not demande_achat and travail.statut != 'termine' %}
    <a href="...">Créer demande achat</a>
{% endif %}
```

**APRÈS**:
```django
{% if travail.statut != 'complete' and travail.statut != 'annule' %}
    <a href="...">
        {% if travail.necessite_materiel %}
            Ajouter demande achat
        {% else %}
            Créer demande achat
        {% endif %}
    </a>
{% endif %}
```

**Avantages**:
- ✅ Bouton toujours visible (pas seulement si aucune demande)
- ✅ Texte adapté selon le contexte

---

### 2. **travail_card.html** ✅

**Fichier**: [templates/includes/travail_card.html](templates/includes/travail_card.html)

**Modification** (Ligne 78-105):

**AVANT**:
```django
{% if travail.demande_achat %}
    <div class="bg-purple-50">
        <i class="fas fa-shopping-cart"></i>
        <span>{{ travail.demande_achat.numero_facture }}</span>
        <span>{{ travail.demande_achat.montant_ttc|floatformat:0 }} F</span>
    </div>
{% endif %}
```

**APRÈS**:
```django
{% if travail.necessite_materiel %}
    <div class="bg-purple-50">
        <i class="fas fa-shopping-cart"></i>
        <span>{{ travail.demandes_achat.count }} demande(s)</span>
        <span>{{ travail.cout_total_materiel|floatformat:0 }} F</span>

        <!-- Badge statut matériel -->
        {% if travail.statut_materiel == 'materiel_recu' %}
            <span class="badge"><i class="fas fa-check"></i></span>
        {% elif travail.statut_materiel == 'en_attente_reception' %}
            <span class="badge"><i class="fas fa-clock"></i></span>
        {% elif travail.statut_materiel == 'en_attente_validation' %}
            <span class="badge"><i class="fas fa-hourglass-half"></i></span>
        {% endif %}
    </div>
{% endif %}
```

**Avantages**:
- ✅ Affiche le NOMBRE de demandes
- ✅ Affiche le COÛT TOTAL
- ✅ Badge visuel pour le statut matériel

---

### 3. **demande_achat_mini_card.html** ✅

**Fichier**: [templates/includes/demande_achat_mini_card.html](templates/includes/demande_achat_mini_card.html)

**Modification** (Ligne 1-4):

**AVANT**:
```django
{# Usage: {% include 'includes/demande_achat_mini_card.html' with demande=travail.demande_achat %} #}
```

**APRÈS**:
```django
{# Usage (Une seule demande): {% include 'includes/demande_achat_mini_card.html' with demande=demande %} #}
{# Usage (Depuis travail - première demande): {% include 'includes/demande_achat_mini_card.html' with demande=travail.demandes_achat.first %} #}
```

**Note**: Composant inchangé, mais documentation d'usage mise à jour

---

### 4. **demande_achat_detail.html** ✅

**Fichier**: [templates/payments/demande_achat_detail.html](templates/payments/demande_achat_detail.html)

**Statut**: ✅ **Déjà correct** - Aucune modification nécessaire

Le template utilise déjà `demande.travail_lie` qui est la FK côté Invoice. Aucun changement requis.

```django
{% if demande.travail_lie %}
    <a href="{% url 'maintenance:travail_detail' demande.travail_lie.pk %}">
        {{ demande.travail_lie.numero_travail }} - {{ demande.travail_lie.titre }}
    </a>
{% endif %}
```

---

## 🐍 Vues Python Modifiées

### 1. **apps/maintenance/views.py** ✅

**Fonction**: `travail_detail_view()`

**Modifications**:

#### A. Suppression de la récupération manuelle (Ligne 587-590)

**AVANT**:
```python
# Récupérer la demande d'achat liée (si elle existe)
demande_achat = None
if hasattr(travail, 'demandes_achat_liees'):
    demande_achat = travail.demandes_achat_liees.first()
```

**APRÈS**:
```python
# ✅ ARCHITECTURE 1-to-Many: Les demandes d'achat sont accessibles via travail.demandes_achat.all()
# Plus besoin de passer demande_achat au contexte, le template y accède directement
```

#### B. Timeline - Afficher toutes les demandes (Ligne 638-647)

**AVANT**:
```python
# 4. Demande d'achat créée (si elle existe)
if demande_achat and demande_achat.date_demande:
    timeline.append({
        'action': f'Demande d\'achat créée ({demande_achat.numero_facture})',
        'user': demande_achat.demandeur.get_full_name(),
        'date': demande_achat.date_demande,
        'icon': 'fa-shopping-cart',
        'color': 'purple'
    })
```

**APRÈS**:
```python
# 4. Demandes d'achat créées (si elles existent) - Architecture 1-to-Many
for demande in travail.demandes_achat.all():
    if demande.date_demande:
        timeline.append({
            'action': f'Demande d\'achat créée ({demande.numero_facture})',
            'user': demande.demandeur.get_full_name() if demande.demandeur else 'Système',
            'date': demande.date_demande,
            'icon': 'fa-shopping-cart',
            'color': 'purple'
        })
```

#### C. Contexte - Suppression de demande_achat (Ligne 695-700)

**AVANT**:
```python
context = {
    'travail': travail,
    'medias': medias,
    'timeline': timeline,
    'technicians': technicians,
    'demande_achat': demande_achat,  # ❌ À supprimer
    ...
}
```

**APRÈS**:
```python
context = {
    'travail': travail,
    'medias': medias,
    'timeline': timeline,
    'technicians': technicians,
    # ✅ SUPPRIMÉ: 'demande_achat' - Accessible via travail.demandes_achat.all()
    ...
}
```

---

### 2. **apps/payments/views_demandes_achat.py** ✅

**Fonction**: `demande_achat_create_view()`

**Modification** (Ligne 74-78):

**AVANT**:
```python
# Si lié à un travail, mettre à jour le statut du travail
if demande.travail_lie:
    demande.travail_lie.demande_achat = demande  # ❌ Champ supprimé
    demande.travail_lie.statut = 'en_attente_materiel'
    demande.travail_lie.save()
```

**APRÈS**:
```python
# ✅ Si lié à un travail, mettre à jour le statut du travail
# Architecture 1-to-Many: Plus besoin d'assigner demande_achat, la relation existe via travail_lie
if demande.travail_lie and demande.travail_lie.statut not in ['en_attente_materiel', 'en_cours', 'complete']:
    demande.travail_lie.statut = 'en_attente_materiel'
    demande.travail_lie.save()
```

**Changements**:
- ✅ Suppression de l'assignation `demande_achat = demande`
- ✅ Vérification du statut avant modification (évite de régresser un travail en cours)

---

## 📊 Récapitulatif des Fichiers Modifiés

| Fichier | Type | Lignes Modifiées | Statut |
|---------|------|------------------|--------|
| `templates/maintenance/travail_detail.html` | Template | 280-413, 534-544 | ✅ Modifié |
| `templates/includes/travail_card.html` | Template | 78-105 | ✅ Modifié |
| `templates/includes/demande_achat_mini_card.html` | Template | 1-4 (docs) | ✅ Documenté |
| `templates/payments/demande_achat_detail.html` | Template | - | ✅ Déjà correct |
| `apps/maintenance/views.py` | Vue Python | 587-590, 638-647, 695-700 | ✅ Modifié |
| `apps/payments/views_demandes_achat.py` | Vue Python | 74-78 | ✅ Modifié |
| `apps/maintenance/models.py` | Modèle | 248-257 (supprimé) | ✅ Modifié |
| `apps/payments/models.py` | Modèle | 468 (related_name) | ✅ Modifié |

**Total**: 8 fichiers modifiés

---

## ✅ Tests à Effectuer

### 1. Page Détail Travail

- [ ] Vérifier l'affichage quand **aucune demande** liée
- [ ] Vérifier l'affichage avec **1 demande** liée
- [ ] Vérifier l'affichage avec **plusieurs demandes** liées
- [ ] Vérifier le badge de statut matériel
- [ ] Vérifier le bouton "Créer/Ajouter demande d'achat"
- [ ] Vérifier que la timeline affiche toutes les demandes

### 2. Card Travail (Liste)

- [ ] Vérifier badge matériel pour travail sans demande
- [ ] Vérifier badge matériel pour travail avec 1 demande
- [ ] Vérifier badge matériel pour travail avec plusieurs demandes
- [ ] Vérifier l'affichage du coût total

### 3. Création Demande d'Achat

- [ ] Créer une demande pour un travail sans demande existante
- [ ] Créer une 2ème demande pour le même travail
- [ ] Vérifier que le statut du travail passe bien à 'en_attente_materiel'
- [ ] Vérifier qu'on peut ajouter une 3ème demande

### 4. Page Détail Demande d'Achat

- [ ] Vérifier le lien vers le travail lié
- [ ] Vérifier l'affichage des informations

### 5. Propriétés du Modèle

```python
travail = Travail.objects.get(id=1)

# Tester
print(travail.necessite_materiel)  # True/False
print(travail.statut_materiel)  # 'aucun_materiel', etc.
print(travail.cout_total_materiel)  # Decimal
print(travail.demandes_achat.count())  # Nombre
```

---

## 🚨 Points d'Attention

### 1. Migration de la Base de Données

**Important**: Avant de tester, exécuter :

```bash
python manage.py makemigrations maintenance
python manage.py migrate maintenance
```

La migration `0005_remove_demande_achat_field.py` supprimera le champ `Travail.demande_achat`.

### 2. Données Existantes

Si des travaux existants ont déjà une `demande_achat` assignée :

1. **Avant migration**: Les données sont en 1-to-1
2. **Après migration**: Le champ est supprimé, mais les demandes restent via `travail_lie`
3. **Impact**: Aucune perte de données car la FK `Invoice.travail_lie` existe toujours

### 3. Templates Personnalisés

Si d'autres templates utilisent `travail.demande_achat`, ils devront être mis à jour :

```bash
# Rechercher les usages restants
grep -r "travail.demande_achat" templates/
```

---

## 📈 Améliorations Apportées

### Avant (Relation 1-to-1)

❌ **Limitations**:
- Un travail ne pouvait avoir qu'UNE SEULE demande
- Impossible d'acheter du matériel supplémentaire en cours de travail
- Pas de vision du coût total matériel
- Relation redondante (2 FK pointant l'une vers l'autre)

### Après (Relation 1-to-Many)

✅ **Avantages**:
- **Flexibilité**: Plusieurs demandes par travail
- **Traçabilité**: Historique complet de tous les achats
- **Analytics**: Coût total matériel calculé automatiquement
- **UX**: Badge de statut matériel global
- **Architecture**: Relation propre et unidirectionnelle

---

## 📚 Documentation Associée

- [ARCHITECTURE_TRAVAUX_DEMANDES_ACHAT.md](ARCHITECTURE_TRAVAUX_DEMANDES_ACHAT.md) - Documentation complète de l'architecture
- [apps/maintenance/models.py](apps/maintenance/models.py) - Modèle Travail avec nouvelles properties
- [apps/payments/models.py](apps/payments/models.py) - Modèle Invoice avec related_name mis à jour

---

**Migration effectuée par**: Claude Code
**Date**: 2025-10-28
**Version**: 1.0
**Statut**: ✅ Complète et prête pour tests
