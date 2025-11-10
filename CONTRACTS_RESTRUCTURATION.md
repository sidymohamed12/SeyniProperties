# 📋 Plan de Restructuration du Module Contracts

## 🎯 Objectif
Restructurer le module `apps/contracts/` pour qu'il soit **cohérent, moderne et bien intégré** avec l'architecture Tiers.

---

## 📊 État Actuel (Diagnostic)

### ✅ Points Positifs
- ✓ Utilise déjà `tiers.Tiers` pour le locataire
- ✓ Utilise `properties.Appartement` (pas l'ancien Property)
- ✓ Séparation views.py / views_pmo.py
- ✓ Templates PMO dans dossier séparé
- ✓ 4 modèles bien définis (RentalContract, ContractWorkflow, DocumentContrat, HistoriqueWorkflow)

### ❌ Problèmes Identifiés

#### 1. **Fichiers Vides / Non Utilisés**
```
apps/contracts/
├── managers.py         (3 octets - VIDE)
├── serializers.py      (3 octets - VIDE)
├── signals.py          (3 octets - VIDE)
├── permissions.py      (3 octets - VIDE)
├── decorators.py       (3 octets - VIDE)
├── filters.py          (3 octets - VIDE)
└── customForm.py       (3 octets - VIDE)
```

#### 2. **Incohérences de Nommage**
- Fichier `customForm.py` au lieu de `custom_forms.py` (convention Django)
- Mélange de français/anglais dans les noms de champs
- `numero_contrat` vs `contract_number` (incohérent)

#### 3. **Organisation des Vues**
- `views.py` : 32K - TROP GROS (800+ lignes)
- `views_pmo.py` : 15K - Bien mais pourrait être mieux organisé
- Pas de séparation par responsabilité (API, CRUD, Reports)

#### 4. **Templates Dispersés**
```
templates/
├── contracts/          # Templates de contrats
│   ├── create.html
│   ├── detail.html
│   ├── list.html
│   ├── print.html
│   ├── expiring.html
│   └── confirm_delete.html
└── pmo/               # Templates PMO
    ├── dashboard.html
    └── workflow_detail.html
```

#### 5. **Modèles Non Optimisés**
- Pas de `Meta` ordering
- Pas de `get_absolute_url()`
- Pas d'index sur les champs fréquemment recherchés
- Pas de custom managers pour les querysets courants

#### 6. **Formulaires Trop Nombreux**
- `forms.py` : 20K (500+ lignes)
- 11 classes de formulaires dans un seul fichier
- Mélange forms contrats et forms PMO

---

## 🏗️ Architecture Cible

### Structure des Fichiers

```
apps/contracts/
├── models/
│   ├── __init__.py              # Expose tous les modèles
│   ├── contract.py              # RentalContract
│   ├── workflow.py              # ContractWorkflow
│   ├── document.py              # DocumentContrat
│   └── history.py               # HistoriqueWorkflow
│
├── views/
│   ├── __init__.py              # Expose toutes les vues
│   ├── contract_views.py        # CRUD contrats
│   ├── contract_api.py          # APIs contrats
│   ├── contract_reports.py      # Rapports et exports
│   ├── pmo_views.py             # Vues PMO workflow
│   └── pmo_api.py               # APIs PMO
│
├── forms/
│   ├── __init__.py              # Expose tous les forms
│   ├── contract_forms.py        # Formulaires contrats
│   └── pmo_forms.py             # Formulaires PMO
│
├── managers.py                   # Custom QuerySet managers
├── signals.py                    # Django signals
├── permissions.py                # Permission checks
├── serializers.py                # DRF serializers
├── utils.py                      # Fonctions utilitaires
├── admin.py                      # Django admin
├── urls.py                       # Routes
├── apps.py                       # Config app
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    ├── test_forms.py
    └── test_workflow.py
```

### Structure des Templates

```
templates/contracts/
├── base_contract.html            # Template de base pour contracts
├── contracts/
│   ├── list.html                # Liste des contrats
│   ├── detail.html              # Détail contrat
│   ├── form.html                # Création/édition
│   ├── confirm_delete.html      # Confirmation suppression
│   ├── print.html               # Version imprimable
│   └── reports/
│       ├── expiring.html        # Contrats expirant
│       └── revenue.html         # Revenus
│
└── pmo/
    ├── base_pmo.html            # Template de base pour PMO
    ├── dashboard.html           # Dashboard PMO
    ├── workflow_detail.html     # Détail workflow
    ├── workflow_timeline.html   # Timeline étapes
    ├── document_upload.html     # Upload documents
    ├── visite_form.html         # Planification visite
    └── remise_cles_form.html    # Remise des clés
```

---

## 🔧 Plan d'Action Détaillé

### Phase 1 : Nettoyage et Préparation
**Durée estimée : 30 min**

#### 1.1 Supprimer les fichiers vides
- [ ] Supprimer `customForm.py`
- [ ] Garder mais implémenter : `managers.py`, `signals.py`, `permissions.py`, `serializers.py`
- [ ] Supprimer `decorators.py` et `filters.py` (non essentiels)

#### 1.2 Créer la nouvelle structure de dossiers
```bash
mkdir apps/contracts/models
mkdir apps/contracts/views
mkdir apps/contracts/forms
mkdir apps/contracts/tests
```

### Phase 2 : Restructuration des Modèles
**Durée estimée : 1h**

#### 2.1 Séparer models.py en 4 fichiers

**models/contract.py** :
```python
# apps/contracts/models/contract.py
from django.db import models
from apps.core.models import TimestampedModel
from ..managers import ContractQuerySet

class RentalContract(TimestampedModel):
    """Contrat de location"""

    objects = ContractQuerySet.as_manager()

    class Meta:
        verbose_name = "Contrat de location"
        verbose_name_plural = "Contrats de location"
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['locataire']),
            models.Index(fields=['appartement']),
        ]

    def get_absolute_url(self):
        return reverse('contracts:detail', kwargs={'pk': self.pk})
```

**models/workflow.py** :
```python
# apps/contracts/models/workflow.py
from django.db import models
from ..managers import WorkflowQuerySet

class ContractWorkflow(TimestampedModel):
    """Workflow PMO pour gestion du cycle de vie du contrat"""

    objects = WorkflowQuerySet.as_manager()

    class Meta:
        verbose_name = "Workflow PMO"
        verbose_name_plural = "Workflows PMO"
        ordering = ['-created_at']
```

**models/document.py** + **models/history.py** : Idem

**models/__init__.py** :
```python
from .contract import RentalContract
from .workflow import ContractWorkflow
from .document import DocumentContrat
from .history import HistoriqueWorkflow

__all__ = [
    'RentalContract',
    'ContractWorkflow',
    'DocumentContrat',
    'HistoriqueWorkflow',
]
```

#### 2.2 Implémenter managers.py

```python
# apps/contracts/managers.py
from django.db import models
from django.utils import timezone

class ContractQuerySet(models.QuerySet):
    """QuerySet personnalisé pour RentalContract"""

    def actifs(self):
        """Retourne les contrats actifs"""
        return self.filter(statut='actif')

    def expires_bientot(self, jours=30):
        """Retourne les contrats expirant dans X jours"""
        date_limite = timezone.now().date() + timezone.timedelta(days=jours)
        return self.filter(
            statut='actif',
            date_fin__lte=date_limite,
            date_fin__gte=timezone.now().date()
        )

    def par_locataire(self, locataire):
        """Filtre par locataire"""
        return self.filter(locataire=locataire)

    def par_appartement(self, appartement):
        """Filtre par appartement"""
        return self.filter(appartement=appartement)


class WorkflowQuerySet(models.QuerySet):
    """QuerySet personnalisé pour ContractWorkflow"""

    def en_cours(self):
        """Workflows non terminés"""
        return self.exclude(etape_actuelle='termine')

    def en_attente_facture(self):
        """Workflows en attente de facture"""
        return self.filter(etape_actuelle='attente_facture')

    def par_etape(self, etape):
        """Filtre par étape"""
        return self.filter(etape_actuelle=etape)

    def par_responsable(self, responsable):
        """Filtre par responsable PMO"""
        return self.filter(responsable_pmo=responsable)
```

### Phase 3 : Restructuration des Vues
**Durée estimée : 1h30**

#### 3.1 Séparer views.py en 5 fichiers

**views/contract_views.py** :
- CRUD : list, detail, create, edit, delete
- Actions : renew, terminate, print

**views/contract_api.py** :
- get_appartement_info
- get_locataire_info
- validate_dates
- contract_stats_api

**views/contract_reports.py** :
- statistics
- expiring_report
- revenue_report
- export_csv

**views/pmo_views.py** :
- PMODashboardView
- WorkflowDetailView
- Document management
- Workflow actions

**views/pmo_api.py** :
- workflow_stats_api
- Document APIs

**views/__init__.py** :
```python
from .contract_views import *
from .contract_api import *
from .contract_reports import *
from .pmo_views import *
from .pmo_api import *
```

### Phase 4 : Restructuration des Formulaires
**Durée estimée : 45 min**

#### 4.1 Séparer forms.py en 2 fichiers

**forms/contract_forms.py** :
- RentalContractForm
- ContractFilterForm
- ContractRenewalForm
- AppartementSelectionForm

**forms/pmo_forms.py** :
- DocumentUploadForm
- VisitePlanificationForm
- RemiseClesForm
- WorkflowFilterForm

### Phase 5 : Implémenter Signals
**Durée estimée : 30 min**

```python
# apps/contracts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import RentalContract, ContractWorkflow

@receiver(post_save, sender=RentalContract)
def create_workflow_on_contract_creation(sender, instance, created, **kwargs):
    """Crée automatiquement un workflow PMO lors de la création d'un contrat"""
    if created and instance.statut == 'brouillon':
        ContractWorkflow.objects.create(
            contrat=instance,
            etape_actuelle='verification_dossier',
            statut_dossier='en_cours'
        )

@receiver(pre_save, sender=RentalContract)
def update_appartement_status(sender, instance, **kwargs):
    """Met à jour le statut de l'appartement selon le statut du contrat"""
    if instance.statut == 'actif':
        instance.appartement.statut_occupation = 'occupe'
        instance.appartement.save()
    elif instance.statut in ['expire', 'resilie']:
        instance.appartement.statut_occupation = 'libre'
        instance.appartement.save()
```

### Phase 6 : Permissions et Sécurité
**Durée estimée : 20 min**

```python
# apps/contracts/permissions.py
from django.core.exceptions import PermissionDenied

def can_manage_contracts(user):
    """Vérifie si l'utilisateur peut gérer les contrats"""
    return user.user_type in ['manager', 'accountant']

def can_manage_pmo(user):
    """Vérifie si l'utilisateur peut gérer le PMO"""
    return user.user_type in ['manager', 'pmo_manager']

def require_contract_permission(view_func):
    """Décorateur pour vérifier les permissions contrats"""
    def wrapper(request, *args, **kwargs):
        if not can_manage_contracts(request.user):
            raise PermissionDenied("Vous n'avez pas l'autorisation de gérer les contrats")
        return view_func(request, *args, **kwargs)
    return wrapper
```

### Phase 7 : Serializers (API REST)
**Durée estimée : 30 min**

```python
# apps/contracts/serializers.py
from rest_framework import serializers
from .models import RentalContract, ContractWorkflow

class RentalContractSerializer(serializers.ModelSerializer):
    locataire_nom = serializers.CharField(source='locataire.nom_complet', read_only=True)
    appartement_nom = serializers.CharField(source='appartement.nom', read_only=True)
    montant_total = serializers.DecimalField(
        source='montant_total_mensuel',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = RentalContract
        fields = '__all__'

class WorkflowSerializer(serializers.ModelSerializer):
    progression = serializers.IntegerField(
        source='progression_pourcentage',
        read_only=True
    )

    class Meta:
        model = ContractWorkflow
        fields = '__all__'
```

### Phase 8 : Tests
**Durée estimée : 1h**

```python
# apps/contracts/tests/test_models.py
from django.test import TestCase
from apps.contracts.models import RentalContract
from apps.tiers.models import Tiers
from apps.properties.models import Appartement

class RentalContractTestCase(TestCase):
    def setUp(self):
        # Créer données de test
        pass

    def test_contract_creation(self):
        # Test création contrat
        pass

    def test_contract_renewal(self):
        # Test renouvellement
        pass
```

### Phase 9 : Documentation
**Durée estimée : 30 min**

Créer `apps/contracts/README.md` :
```markdown
# Module Contracts

## Vue d'ensemble
Module de gestion des contrats de location avec workflow PMO intégré.

## Modèles
- RentalContract : Contrat de location
- ContractWorkflow : Workflow PMO (7 étapes)
- DocumentContrat : Documents requis
- HistoriqueWorkflow : Historique des transitions

## Workflow PMO
1. verification_dossier
2. attente_facture
3. facture_validee
4. redaction_contrat
5. visite_entree
6. remise_cles
7. termine

## Utilisation
[...]
```

---

## 📝 Checklist de Migration

### Fichiers à Créer
- [ ] `models/__init__.py`
- [ ] `models/contract.py`
- [ ] `models/workflow.py`
- [ ] `models/document.py`
- [ ] `models/history.py`
- [ ] `views/__init__.py`
- [ ] `views/contract_views.py`
- [ ] `views/contract_api.py`
- [ ] `views/contract_reports.py`
- [ ] `views/pmo_views.py`
- [ ] `views/pmo_api.py`
- [ ] `forms/__init__.py`
- [ ] `forms/contract_forms.py`
- [ ] `forms/pmo_forms.py`
- [ ] `tests/__init__.py`
- [ ] `tests/test_models.py`
- [ ] `tests/test_views.py`
- [ ] `README.md`

### Fichiers à Modifier
- [ ] `managers.py` (implémenter QuerySets)
- [ ] `signals.py` (implémenter signals)
- [ ] `permissions.py` (implémenter checks)
- [ ] `serializers.py` (implémenter DRF)
- [ ] `urls.py` (mettre à jour imports)
- [ ] `admin.py` (mettre à jour imports)

### Fichiers à Supprimer
- [ ] `models.py` (après migration)
- [ ] `views.py` (après migration)
- [ ] `views_pmo.py` (après migration)
- [ ] `forms.py` (après migration)
- [ ] `customForm.py`
- [ ] `decorators.py`
- [ ] `filters.py`

### Migrations Django
- [ ] `python manage.py makemigrations contracts`
- [ ] Vérifier la migration générée
- [ ] `python manage.py migrate contracts`

### Tests
- [ ] `python manage.py test apps.contracts`
- [ ] Tester création contrat
- [ ] Tester workflow PMO
- [ ] Tester APIs
- [ ] Tester permissions

### Documentation
- [ ] Mettre à jour `CLAUDE.md`
- [ ] Créer `apps/contracts/README.md`
- [ ] Documenter les APIs

---

## 🎯 Bénéfices Attendus

### Code Quality
- ✅ Meilleure organisation (fichiers < 300 lignes chacun)
- ✅ Séparation des responsabilités (SRP)
- ✅ Code plus lisible et maintenable
- ✅ Réutilisabilité accrue

### Performance
- ✅ Index sur les champs fréquents
- ✅ QuerySets optimisés avec managers
- ✅ Moins de requêtes N+1

### Développement
- ✅ Tests unitaires complets
- ✅ Signals automatiques
- ✅ API REST prête
- ✅ Documentation complète

### Sécurité
- ✅ Permissions centralisées
- ✅ Validations renforcées
- ✅ Audit trail complet

---

## 🚀 Prochaines Étapes

1. **Valider ce plan avec l'utilisateur**
2. **Commencer la Phase 1 (nettoyage)**
3. **Exécuter phase par phase**
4. **Tester après chaque phase**
5. **Documenter au fur et à mesure**

---

**Dernière mise à jour** : 2025-10-23
**Statut** : 📝 Plan en attente de validation
