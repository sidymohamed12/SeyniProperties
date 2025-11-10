# Architecture Travaux ↔ Demandes d'Achat

## 📋 Vue d'ensemble

Ce document détaille l'architecture de liaison entre les **Travaux** (maintenance) et les **Demandes d'Achat** (achats de matériel) dans le système Seyni Properties.

**Date de mise en œuvre**: 2025-10-28
**Type de relation**: **1-to-Many** (Un travail → Plusieurs demandes d'achat)

---

## 🏗️ Architecture Implémentée

### Relation 1-to-Many

```
┌─────────────────────────┐
│      Travail (1)        │
│  - numero_travail       │
│  - titre                │
│  - statut               │
│  - cout_estime          │
│  - cout_reel            │
└────────────┬────────────┘
             │
             │ travail_lie (FK)
             │
             ▼
┌────────────────────────────┐
│   Invoice (Many)           │
│   type_facture='demande_   │
│   achat'                   │
│  - numero_facture          │
│  - montant_ttc             │
│  - etape_workflow          │
│  - travail_lie (FK)        │
└─────────────┬──────────────┘
              │
              │ demande (FK)
              │
              ▼
┌─────────────────────────────┐
│  LigneDemandeAchat (Many)   │
│  - designation              │
│  - quantite                 │
│  - prix_unitaire            │
│  - fournisseur              │
└─────────────────────────────┘
```

### Modèles Modifiés

#### 1. **Travail** ([apps/maintenance/models.py](apps/maintenance/models.py))

**Champ supprimé** :
```python
# ❌ ANCIEN - Redondant
demande_achat = models.ForeignKey('payments.Invoice', ...)
```

**Accès aux demandes d'achat** :
```python
# ✅ NOUVEAU - Via reverse relation
travail.demandes_achat.all()  # QuerySet de toutes les demandes
```

**Nouvelles propriétés** :

```python
@property
def necessite_materiel(self):
    """Vérifie si le travail nécessite du matériel"""
    return self.demandes_achat.exists()

@property
def statut_materiel(self):
    """
    Retourne: 'aucun_materiel', 'en_attente_validation',
              'en_attente_reception', 'materiel_recu', 'materiel_partiel'
    """
    # Logique basée sur les étapes workflow de toutes les demandes

@property
def cout_total_materiel(self):
    """Calcule le coût total du matériel (demandes reçues/payées)"""
    demandes = self.demandes_achat.filter(etape_workflow__in=['recue', 'paye'])
    return sum(d.montant_ttc for d in demandes) or Decimal('0.00')
```

#### 2. **Invoice** ([apps/payments/models.py](apps/payments/models.py))

**Champ modifié** :
```python
# ✅ related_name mis à jour
travail_lie = models.ForeignKey(
    'maintenance.Travail',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='demandes_achat',  # 🆕 Pluriel pour relation 1-to-Many
    verbose_name="Travail lié",
    help_text="Travail pour lequel cette demande d'achat a été créée"
)
```

---

## 🔄 Workflow Complet

### 1. Création d'un Travail

```python
travail = Travail.objects.create(
    titre="Réparation plomberie App 12",
    nature='reactif',
    type_travail='plomberie',
    priorite='haute',
    appartement=appartement,
    statut='signale',
    assigne_a=technicien
)
```

### 2. Identification du Besoin Matériel

Le technicien identifie qu'il a besoin de matériel :

```python
# Créer une demande d'achat
demande = travail.creer_demande_achat(
    demandeur=request.user,
    service_fonction="Maintenance Technique",
    motif_principal="Remplacement tuyauterie endommagée suite fuite",
    articles=[
        {
            'designation': 'Tuyau PVC 50mm',
            'quantite': 10,
            'unite': 'mètre',
            'prix_unitaire': 2500,
            'fournisseur': 'Quincaillerie du Nord',
            'motif': 'Remplacement section endommagée'
        },
        {
            'designation': 'Coude PVC 50mm',
            'quantite': 4,
            'unite': 'unité',
            'prix_unitaire': 1500,
            'fournisseur': 'Quincaillerie du Nord',
            'motif': 'Raccordement nouveau tuyau'
        }
    ]
)

# ✅ Le travail passe automatiquement en statut 'en_attente_materiel'
print(travail.statut)  # 'en_attente_materiel'
```

### 3. Suivi du Statut Matériel

```python
# Vérifier l'état du matériel
print(travail.statut_materiel)
# Output: 'en_attente_validation'

# Vérifier si matériel nécessaire
if travail.necessite_materiel:
    print(f"Nombre de demandes: {travail.demandes_achat.count()}")

# Afficher toutes les demandes
for demande in travail.demandes_achat.all():
    print(f"{demande.numero_facture}: {demande.etape_workflow}")
```

### 4. Ajout de Matériel Supplémentaire

Un travail peut avoir **plusieurs demandes d'achat** :

```python
# Besoin additionnel découvert en cours de travail
demande2 = travail.creer_demande_achat(
    demandeur=technicien,
    service_fonction="Maintenance Technique",
    motif_principal="Matériel supplémentaire suite inspection",
    articles=[
        {
            'designation': 'Joint silicone',
            'quantite': 2,
            'unite': 'tube',
            'prix_unitaire': 3000,
            'fournisseur': 'Quincaillerie du Nord',
            'motif': 'Étanchéité raccords'
        }
    ]
)

# ✅ Maintenant 2 demandes liées au même travail
print(travail.demandes_achat.count())  # 2
```

### 5. Validation et Réception

Workflow des demandes d'achat :

```
brouillon → en_attente → valide_responsable → comptable
→ validation_dg → approuve → en_cours_achat → recue → paye
```

Lorsque tout le matériel est reçu :

```python
# Toutes les demandes reçues
if travail.statut_materiel == 'materiel_recu':
    # Technicien peut commencer
    travail.statut = 'en_cours'
    travail.date_debut = timezone.now()
    travail.save()
```

### 6. Finalisation du Travail

```python
# Terminer le travail
travail.marquer_complete(commentaire="Réparation terminée avec succès")

# Calculer le coût total (main d'œuvre + matériel)
cout_materiel = travail.cout_total_materiel
cout_total = cout_materiel + travail.cout_reel

print(f"Coût matériel: {cout_materiel} FCFA")
print(f"Coût main d'œuvre: {travail.cout_reel} FCFA")
print(f"Coût total: {cout_total} FCFA")
```

---

## 📊 Requêtes Courantes

### Obtenir tous les travaux avec matériel en attente

```python
from django.db.models import Exists, OuterRef

travaux_en_attente = Travail.objects.filter(
    statut='en_attente_materiel'
).prefetch_related(
    'demandes_achat'
)

for travail in travaux_en_attente:
    print(f"{travail.numero_travail}: {travail.demandes_achat.count()} demande(s)")
```

### Statistiques par travail

```python
from django.db.models import Count, Sum

stats = Travail.objects.filter(
    nature='reactif'
).annotate(
    nb_demandes=Count('demandes_achat'),
    total_materiel=Sum('demandes_achat__montant_ttc')
).values('numero_travail', 'titre', 'nb_demandes', 'total_materiel')
```

### Demandes d'achat par statut

```python
# Toutes les demandes d'un travail groupées par étape
from django.db.models import Count

demandes_par_etape = travail.demandes_achat.values(
    'etape_workflow'
).annotate(
    count=Count('id')
)

for etape in demandes_par_etape:
    print(f"{etape['etape_workflow']}: {etape['count']}")
```

---

## 🎨 Affichage dans les Templates

### Liste des demandes d'un travail

```django
{% comment %} templates/maintenance/travail_detail.html {% endcomment %}

<h3>Demandes d'Achat Liées</h3>

{% if travail.necessite_materiel %}
    <div class="demandes-achat">
        <p>Statut matériel: <strong>{{ travail.statut_materiel }}</strong></p>
        <p>Coût total matériel: <strong>{{ travail.cout_total_materiel|floatformat:0 }} FCFA</strong></p>

        <table>
            <thead>
                <tr>
                    <th>Numéro</th>
                    <th>Montant</th>
                    <th>Étape</th>
                    <th>Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for demande in travail.demandes_achat.all %}
                <tr>
                    <td>{{ demande.numero_facture }}</td>
                    <td>{{ demande.montant_ttc|floatformat:0 }} FCFA</td>
                    <td>
                        <span class="badge badge-{{ demande.etape_workflow }}">
                            {{ demande.get_etape_workflow_display }}
                        </span>
                    </td>
                    <td>{{ demande.date_demande|date:"d/m/Y" }}</td>
                    <td>
                        <a href="{% url 'demande_achat_detail' demande.id %}">
                            Voir détails
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
{% else %}
    <p class="text-muted">Aucun matériel nécessaire pour ce travail</p>
{% endif %}

<a href="{% url 'demande_achat_create' %}?travail={{ travail.id }}"
   class="btn btn-primary">
    + Ajouter une demande d'achat
</a>
```

### Badge de statut matériel

```django
{% comment %} Inclusion dans travail_card.html {% endcomment %}

{% if travail.necessite_materiel %}
    {% if travail.statut_materiel == 'materiel_recu' %}
        <span class="badge bg-success">✓ Matériel reçu</span>
    {% elif travail.statut_materiel == 'en_attente_reception' %}
        <span class="badge bg-warning">⏳ En attente réception</span>
    {% elif travail.statut_materiel == 'en_attente_validation' %}
        <span class="badge bg-info">📝 En attente validation</span>
    {% elif travail.statut_materiel == 'materiel_partiel' %}
        <span class="badge bg-warning">⚠️ Réception partielle</span>
    {% endif %}
{% endif %}
```

---

## 🛠️ Migration

### Commande à exécuter

```bash
# Générer la migration
python manage.py makemigrations maintenance

# Appliquer la migration
python manage.py migrate maintenance
```

### Fichier de migration créé

[apps/maintenance/migrations/0005_remove_demande_achat_field.py](apps/maintenance/migrations/0005_remove_demande_achat_field.py)

**Opérations** :
1. Suppression du champ `Travail.demande_achat`
2. Le `related_name='demandes_achat'` dans `Invoice.travail_lie` fournit l'accès inverse

---

## ✅ Avantages de cette Architecture

### 1. **Flexibilité**
- Un travail peut avoir **plusieurs demandes** pour différents fournisseurs
- Ajout de matériel supplémentaire en cours de travail
- Séparation logique des achats

### 2. **Traçabilité**
- Historique complet de chaque demande via `HistoriqueValidation`
- Suivi précis du coût par type de matériel
- Audit trail complet

### 3. **Workflow Clair**
```
Travail créé
    ↓
Besoin matériel identifié → Demande(s) d'achat créée(s)
    ↓
Validation workflow
    ↓
Matériel reçu → Travail peut commencer
    ↓
Travail terminé → Coût total calculé
```

### 4. **Statistiques Précises**
- Coût matériel vs main d'œuvre
- Délais d'approvisionnement
- Fournisseurs les plus utilisés
- Budget prévisionnel vs réel

---

## 🔍 Points d'Attention

### 1. Gestion des Statuts

Le statut du travail doit être cohérent avec les demandes d'achat :

```python
# ⚠️ Vérifier avant de commencer un travail
if travail.statut == 'en_attente_materiel':
    if travail.statut_materiel == 'materiel_recu':
        # ✅ OK pour commencer
        travail.statut = 'en_cours'
    else:
        # ❌ Matériel pas encore reçu
        raise ValueError("Impossible de commencer: matériel non reçu")
```

### 2. Calcul du Coût Réel

```python
# Inclure le coût du matériel dans le coût total
def calculer_cout_total(travail):
    cout_materiel = travail.cout_total_materiel
    cout_main_oeuvre = travail.cout_reel or Decimal('0.00')
    return cout_materiel + cout_main_oeuvre
```

### 3. Notifications

```python
# Notifier le technicien quand matériel reçu
from apps.notifications.utils import send_notification

for demande in travail.demandes_achat.filter(etape_workflow='recue'):
    if demande.receptionne_par:
        send_notification(
            user=travail.assigne_a,
            title=f"Matériel reçu pour {travail.numero_travail}",
            message=f"La demande {demande.numero_facture} a été réceptionnée",
            type='info'
        )
```

---

## 📚 Ressources

### Fichiers Modifiés

1. [apps/maintenance/models.py](apps/maintenance/models.py) - Modèle `Travail`
2. [apps/payments/models.py](apps/payments/models.py) - Modèle `Invoice`
3. [apps/maintenance/migrations/0005_remove_demande_achat_field.py](apps/maintenance/migrations/0005_remove_demande_achat_field.py)

### Documentation Connexe

- [CLAUDE.md](CLAUDE.md) - Vue d'ensemble du projet
- Workflow des demandes d'achat (Module 4)
- Système de gestion des travaux (Module maintenance)

---

## 🚀 Prochaines Étapes

### À implémenter

1. **Dashboard Matériel**
   - Vue globale des demandes par travail
   - Alertes pour matériel en retard
   - Budget vs réalisé

2. **Rapports**
   - Coût moyen matériel par type de travail
   - Délais moyens d'approvisionnement
   - Top fournisseurs

3. **Automatisation**
   - Changement auto du statut travail quand matériel reçu
   - Suggestions de matériel basées sur le type de travail
   - Détection des ruptures de stock

---

**Documentation créée le**: 2025-10-28
**Version**: 1.0
**Auteur**: Architecture Seyni Properties
