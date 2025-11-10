# Affichage des Demandes d'Achat sur la Page Détail du Travail

**Date**: 25 octobre 2025
**Status**: ✅ Implémenté avec succès

---

## Contexte

L'utilisateur a demandé que lorsqu'une demande d'achat est liée à un travail, elle soit affichée sur la page de détail du travail.

---

## Changements Implémentés

### 1. ✅ Migration de la Vue Détail vers `Travail`

**Fichier**: [apps/maintenance/views.py:716-841](apps/maintenance/views.py#L716-L841)

La fonction `intervention_detail_view` a été complètement migrée de l'ancien modèle `Intervention` vers le nouveau modèle `Travail`.

#### A. Changement du Modèle

**Ligne 718**:
```python
# AVANT ❌
intervention = get_object_or_404(Intervention, id=intervention_id)

# APRÈS ✅
travail = get_object_or_404(Travail, id=intervention_id)
```

#### B. Récupération de la Demande d'Achat Liée

**Lignes 734-737** - AJOUT:
```python
# Récupérer la demande d'achat liée (si elle existe)
demande_achat = None
if hasattr(travail, 'demandes_achat_liees'):
    demande_achat = travail.demandes_achat_liees.first()  # Prendre la première demande liée
```

**Explication**:
- Le modèle `Invoice` a un ForeignKey `travail_lie` vers `Travail`
- Le `related_name` est `demandes_achat_liees`
- On récupère la première demande liée (un travail peut avoir plusieurs demandes, on affiche la première)

#### C. Médias Migrés vers `TravailMedia`

**Ligne 732**:
```python
# AVANT ❌
medias = InterventionMedia.objects.filter(intervention=intervention)

# APRÈS ✅
medias = TravailMedia.objects.filter(travail=travail)
```

#### D. Mise à Jour des Permissions

**Lignes 721-725**:
```python
# AVANT ❌
can_view = (
    request.user.user_type in ['manager', 'accountant'] or
    intervention.technicien == request.user or
    getattr(intervention, 'signale_par', None) == request.user
)

# APRÈS ✅
can_view = (
    request.user.user_type in ['manager', 'accountant'] or
    travail.assigne_a == request.user or  # ✅ Changé
    getattr(travail, 'signale_par', None) == request.user
)
```

#### E. Timeline Améliorée avec la Demande d'Achat

**Lignes 750-806** - Timeline complète:

```python
# 1. Signalement du travail
if travail.date_signalement:
    timeline.append({
        'action': 'Travail signalé',
        'user': signale_par_nom,
        'date': travail.date_signalement,
        'icon': 'fa-exclamation',
        'color': 'red'
    })

# 2. Assignation
if travail.date_assignation and travail.assigne_a:
    timeline.append({
        'action': f'Assigné à {travail.assigne_a.get_full_name()}',
        'user': 'Manager',
        'date': travail.date_assignation,
        'icon': 'fa-user-plus',
        'color': 'blue'
    })

# 3. Début du travail
if travail.date_debut:
    timeline.append({
        'action': 'Travail démarré',
        'user': travail.assigne_a.get_full_name() if travail.assigne_a else 'Employé',
        'date': travail.date_debut,
        'icon': 'fa-play',
        'color': 'orange'
    })

# 4. 🆕 Demande d'achat créée
if demande_achat and demande_achat.date_demande:
    timeline.append({
        'action': f'Demande d\'achat créée ({demande_achat.numero_facture})',
        'user': demande_achat.demandeur.get_full_name() if demande_achat.demandeur else 'Système',
        'date': demande_achat.date_demande,
        'icon': 'fa-shopping-cart',
        'color': 'purple'
    })

# 5. Fin du travail
if travail.date_fin:
    timeline.append({
        'action': 'Travail terminé',
        'user': travail.assigne_a.get_full_name() if travail.assigne_a else 'Employé',
        'date': travail.date_fin,
        'icon': 'fa-check',
        'color': 'green'
    })
```

**Nouveau**: L'événement de création de la demande d'achat apparaît maintenant dans la timeline chronologique !

#### F. Contexte Mis à Jour

**Lignes 825-839**:
```python
context = {
    'travail': travail,  # ✅ Changé de intervention
    'medias': medias,
    'timeline': timeline,
    'technicians': technicians,
    'demande_achat': demande_achat,  # 🆕 AJOUT
    'can_edit': request.user.user_type in ['manager', 'accountant'],
    'can_assign': request.user.user_type in ['manager', 'accountant'] and travail.statut == 'signale',
    'can_start': travail.statut == 'assigne' and travail.assigne_a == request.user,  # ✅ Changé
    'can_complete': travail.statut == 'en_cours' and travail.assigne_a == request.user,  # ✅ Changé
    'checklist_total': checklist_total,
    'checklist_completed': checklist_completed,
    'checklist_progress': checklist_progress,
}
```

---

### 2. ✅ Mise à Jour du Template

**Fichier**: [templates/maintenance/travail_detail.html](templates/maintenance/travail_detail.html)

#### A. Section Demande d'Achat - Affichage Quand Liée

**Lignes 280-344** - Remplacé `travail.demande_achat` par `demande_achat`:

```django
{% if demande_achat %}
<div class="bg-purple-50 border-l-4 border-purple-500 rounded-lg p-6">
    <div class="flex justify-between items-start mb-4">
        <div>
            <h2 class="text-xl font-semibold text-purple-900 flex items-center">
                <i class="fas fa-shopping-cart mr-2"></i>
                Demande d'Achat Liée
            </h2>
            <p class="text-sm text-purple-700 mt-1">Matériel commandé pour ce travail</p>
        </div>

        {# Badge de statut selon l'étape du workflow #}
        {% if demande_achat.etape_workflow == 'brouillon' %}
        <span class="...">Brouillon</span>
        {% elif demande_achat.etape_workflow == 'en_attente_responsable' %}
        <span class="...">En attente validation</span>
        {% elif demande_achat.etape_workflow == 'valide' %}
        <span class="...">Validé</span>
        {# ... autres statuts ... #}
        {% endif %}
    </div>

    <div class="bg-white rounded-lg p-4">
        <div class="grid grid-cols-2 gap-4 mb-3">
            <div>
                <p class="text-xs text-gray-600">Numéro</p>
                <p class="font-semibold text-gray-900">{{ demande_achat.numero_facture }}</p>
            </div>
            <div>
                <p class="text-xs text-gray-600">Montant</p>
                <p class="font-semibold text-purple-600 text-lg">{{ demande_achat.montant_ttc|floatformat:0 }} FCFA</p>
            </div>
            <div>
                <p class="text-xs text-gray-600">Demandeur</p>
                <p class="text-sm text-gray-900">{{ demande_achat.demandeur.get_full_name }}</p>
            </div>
            <div>
                <p class="text-xs text-gray-600">Date demande</p>
                <p class="text-sm text-gray-900">{{ demande_achat.date_demande|date:"d/m/Y" }}</p>
            </div>
        </div>

        <p class="text-sm text-gray-700 mb-3">
            <strong>Motif:</strong> {{ demande_achat.motif_principal|truncatewords:20 }}
        </p>

        <a href="{% url 'payments:demande_achat_detail' demande_achat.pk %}"
           class="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">
            <i class="fas fa-eye mr-2"></i>
            Voir détail complet
        </a>
    </div>
</div>
{% else %}
{# Section pour créer une demande si pas encore liée #}
...
{% endif %}
```

#### B. Mise à Jour des Statuts de Workflow

**Lignes 291-310** - Statuts alignés avec le workflow réel des demandes d'achat:

| Étape Workflow | Couleur | Libellé |
|----------------|---------|---------|
| `brouillon` | Gris | Brouillon |
| `en_attente_responsable` | Jaune | En attente validation |
| `approuve_responsable` | Bleu | Approuvé responsable |
| `en_attente_dg` | Orange | En attente DG |
| `valide` | Vert | Validé |
| `commande_passee` | Indigo | Commandé |
| `receptionne` | Teal | Réceptionné |
| `refuse` | Rouge | Refusé |

#### C. Bouton "Créer demande achat" dans Actions

**Ligne 488**:
```django
{# AVANT #}
{% if not travail.demande_achat and travail.statut != 'termine' %}

{# APRÈS #}
{% if not demande_achat and travail.statut != 'termine' %}
```

Le bouton "Créer demande achat" n'apparaît que si:
- ✅ Aucune demande n'est déjà liée
- ✅ Le travail n'est pas terminé

---

## Résultat Visuel

### Quand une demande d'achat EST liée au travail

```
┌─────────────────────────────────────────────────────────┐
│ 🛒 Demande d'Achat Liée              [Badge Statut]    │
│ Matériel commandé pour ce travail                      │
├─────────────────────────────────────────────────────────┤
│ Numéro: INV-2025-001234    Montant: 150 000 FCFA      │
│ Demandeur: Jean Dupont     Date: 25/10/2025           │
│                                                         │
│ Motif: Achat de matériel électrique pour...           │
│                                                         │
│ [Voir détail complet]                                  │
└─────────────────────────────────────────────────────────┘
```

### Quand AUCUNE demande n'est liée

```
┌─────────────────────────────────────────────────────────┐
│ 🛒 Besoin de matériel ?                                │
│                                                         │
│ Si ce travail nécessite l'achat de matériel, créez    │
│ une demande d'achat liée.                              │
│                                                         │
│ [+ Créer demande d'achat]                              │
└─────────────────────────────────────────────────────────┘
```

---

## Timeline Enrichie

La timeline du travail affiche maintenant **chronologiquement** tous les événements, y compris la création de la demande d'achat :

```
⚫ Travail signalé
   Par: Jean Dupont - 20/10/2025 09:00

⚫ Assigné à Mohamed Diop
   Par: Manager - 20/10/2025 10:30

⚫ Travail démarré
   Par: Mohamed Diop - 20/10/2025 14:00

🛒 Demande d'achat créée (INV-2025-001234)  ← NOUVEAU
   Par: Jean Dupont - 21/10/2025 09:15

✓ Travail terminé
   Par: Mohamed Diop - 22/10/2025 16:00
```

---

## Tests Recommandés

### Test 1: Travail sans demande d'achat
1. ✅ Aller sur la page détail d'un travail sans demande liée
2. ✅ Vérifier que la section "Besoin de matériel ?" s'affiche
3. ✅ Cliquer sur "Créer demande d'achat"
4. ✅ Vérifier que `?travail_id=X` est dans l'URL
5. ✅ Créer la demande

### Test 2: Travail avec demande d'achat liée
1. ✅ Retourner sur la page détail du travail
2. ✅ Vérifier que la section "Demande d'Achat Liée" s'affiche
3. ✅ Vérifier que le numéro, montant, demandeur et date sont affichés
4. ✅ Vérifier que le badge de statut est correct
5. ✅ Cliquer sur "Voir détail complet"
6. ✅ Vérifier la redirection vers la page détail de la demande

### Test 3: Timeline
1. ✅ Vérifier que l'événement "Demande d'achat créée (INV-XXX)" apparaît
2. ✅ Vérifier que l'icône est un caddie (fa-shopping-cart)
3. ✅ Vérifier que la couleur est violette
4. ✅ Vérifier que les événements sont dans l'ordre chronologique

---

## Modèle de Données

### Relation `Invoice` ↔ `Travail`

```python
# apps/payments/models.py
class Invoice(BaseModel):
    travail_lie = models.ForeignKey(
        'maintenance.Travail',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='demandes_achat_liees',  # ← Nom de la relation inverse
        verbose_name="Travail lié"
    )
```

**Accès**:
- Depuis `Invoice` → `Travail` : `invoice.travail_lie`
- Depuis `Travail` → `Invoice` : `travail.demandes_achat_liees.all()`

**Vue utilise**:
```python
demande_achat = travail.demandes_achat_liees.first()
```

---

## Fichiers Modifiés

| Fichier | Lignes | Description |
|---------|--------|-------------|
| [apps/maintenance/views.py](apps/maintenance/views.py) | 716-841 | Migration complète vers `Travail` + ajout demande |
| [templates/maintenance/travail_detail.html](templates/maintenance/travail_detail.html) | 281-344 | Section demande d'achat |
| [templates/maintenance/travail_detail.html](templates/maintenance/travail_detail.html) | 488 | Bouton créer demande |

---

## Documentation Liée

- [TRAVAUX_MIGRATION_COMPLETE.md](TRAVAUX_MIGRATION_COMPLETE.md) - Migration initiale Intervention → Travail
- [TRAVAUX_LIST_VIEW_FIX.md](TRAVAUX_LIST_VIEW_FIX.md) - Correction de la page de liste
- [TRAVAUX_MIGRATION_FIXES.md](TRAVAUX_MIGRATION_FIXES.md) - Corrections post-migration

---

## Prochaines Étapes Suggérées

1. **Afficher toutes les demandes liées** (actuellement seule la première est affichée)
2. **Permettre de délier une demande** d'un travail
3. **Afficher le statut du travail sur la page détail de la demande**
4. **Calculer automatiquement le montant estimé** du travail basé sur les demandes liées
