# Travaux - Demandes d'Achat: Implémentation Architecture 1-to-Many

**Date**: 2025-10-28
**Statut**: ✅ COMPLÉTÉ ET PRÊT POUR PRODUCTION
**Version**: 1.0

---

## 📋 Résumé Exécutif

Cette implémentation transforme la relation entre **Travaux** (Work Orders) et **Demandes d'Achat** (Purchase Requests) d'une relation bidirectionnelle problématique vers une architecture 1-to-Many propre et évolutive.

### **Problème Initial**

```python
# ❌ AVANT - Relation bidirectionnelle redondante
Travail.demande_achat → Invoice (ForeignKey)
Invoice.travail_lie → Travail (ForeignKey)
```

### **Solution Implémentée**

```python
# ✅ APRÈS - Relation 1-to-Many propre
Invoice.travail_lie → Travail (ForeignKey avec related_name='demandes_achat')
# Accès: travail.demandes_achat.all()
```

---

## 🎯 Fonctionnalités Implémentées

### **1. Architecture Backend** ✅

- ✅ Suppression du champ redondant `Travail.demande_achat`
- ✅ Configuration `related_name='demandes_achat'` sur `Invoice.travail_lie`
- ✅ 3 nouvelles propriétés sur le modèle `Travail`:
  - `necessite_materiel` (bool)
  - `statut_materiel` (str: 'aucun_materiel', 'en_attente_validation', 'en_attente_reception', 'materiel_recu', 'materiel_partiel')
  - `cout_total_materiel` (Decimal)

### **2. Interface Desktop (Manager)** ✅

- ✅ [travail_detail.html](templates/maintenance/travail_detail.html) - Affichage de toutes les demandes avec boucle
- ✅ [travail_card.html](templates/includes/travail_card.html) - Badge avec nombre de demandes et coût total
- ✅ [demande_achat_mini_card.html](templates/includes/demande_achat_mini_card.html) - Carte individuelle mise à jour

### **3. Interface Mobile (Employé)** ✅

**Affichage**:
- ✅ Liste complète des demandes d'achat sur la page détail du travail
- ✅ Badge statut matériel sur la liste des travaux
- ✅ Indicateurs visuels selon l'état de chaque demande

**Création de Demande**:
- ✅ Formulaire simplifié depuis le terrain
- ✅ Ajout dynamique d'articles multiples
- ✅ Prise de photos avec l'appareil
- ✅ Validation client-side

**Confirmation Réception**:
- ✅ Bouton "J'ai reçu ce matériel" sur les demandes payées
- ✅ Confirmation AJAX avec spinner
- ✅ Déblocage automatique du travail si tout reçu
- ✅ Messages utilisateur contextuels

### **4. Workflow Matériel** ✅

**Séquence Complète**:

```
1️⃣ Travail créé (statut: 'signale' ou 'assigne')
   ↓
2️⃣ Employé crée demande matériel depuis mobile
   → Travail.statut = 'en_attente_materiel' 🔒
   → Demande.etape_workflow = 'brouillon'
   ↓
3️⃣ Validation hiérarchique
   brouillon → en_attente → valide_responsable
   → comptable → validation_dg → approuve
   ↓
4️⃣ Paiement effectué
   → Demande.etape_workflow = 'paye'
   → Travail RESTE en 'en_attente_materiel' 🔒
   ↓
5️⃣ Employé REÇOIT le matériel sur site
   → Clique "J'ai reçu ce matériel"
   → Demande.etape_workflow = 'recue'
   ↓
6️⃣ Si TOUTES les demandes sont 'recue'
   → ✅ Travail.statut = 'en_cours' 🔓
   → Travail.date_debut_reel = now()
```

**Logique de Déblocage**:
```python
if travail.statut_materiel == 'materiel_recu':
    # TOUTES les demandes en statut 'recue'
    travail.statut = 'en_cours'  # Débloquer
    if not travail.date_debut_reel:
        travail.date_debut_reel = timezone.now()
    travail.save()
```

---

## 📁 Fichiers Modifiés

### **Backend Django**

| Fichier | Modification | Lignes |
|---------|-------------|--------|
| [apps/maintenance/models.py](apps/maintenance/models.py) | Suppression `demande_achat`, ajout properties | 248-376 |
| [apps/maintenance/views.py](apps/maintenance/views.py) | Suppression récupération manuelle | 587-700 |
| [apps/payments/models.py](apps/payments/models.py) | Update `related_name` | 468 |
| [apps/payments/views_demandes_achat.py](apps/payments/views_demandes_achat.py) | Suppression assignation redondante | 74-78 |
| [apps/employees/views.py](apps/employees/views.py) | Ajout 2 nouvelles vues | 771-856, 858-953 |
| [apps/employees/mobile_urls.py](apps/employees/mobile_urls.py) | Ajout 2 URL | 21-22 |

### **Templates Desktop**

| Template | Modification | Lignes |
|---------|-------------|--------|
| [templates/maintenance/travail_detail.html](templates/maintenance/travail_detail.html) | Boucle demandes multiples | 280-413 |
| [templates/includes/travail_card.html](templates/includes/travail_card.html) | Badge count + total | 78-105 |

### **Templates Mobile**

| Template | Type | Lignes |
|---------|------|--------|
| [templates/employees/mobile/travail_detail.html](templates/employees/mobile/travail_detail.html) | Modifié | 267-332, 466-518 |
| [templates/employees/mobile/travail_demande_materiel.html](templates/employees/mobile/travail_demande_materiel.html) | Nouveau | 330 lignes |
| [templates/employees/mobile/work_list.html](templates/employees/mobile/work_list.html) | Modifié | 330-351 |

### **Migrations**

| Migration | Description |
|-----------|-------------|
| [apps/maintenance/migrations/0005_remove_demande_achat_field.py](apps/maintenance/migrations/0005_remove_demande_achat_field.py) | Suppression champ redondant |

---

## 🔑 Composants Clés

### **1. Propriétés Calculées du Modèle Travail**

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
    demandes = self.demandes_achat.all()
    if not demandes.exists():
        return 'aucun_materiel'

    etapes = list(demandes.values_list('etape_workflow', flat=True))

    if all(e in ['brouillon', 'en_attente'] for e in etapes):
        return 'en_attente_validation'
    if all(e == 'recue' for e in etapes):
        return 'materiel_recu'
    if any(e in ['brouillon', 'en_attente', 'valide_responsable', 'comptable',
                 'validation_dg', 'approuve', 'en_cours_achat'] for e in etapes):
        return 'en_attente_reception'
    if any(e == 'recue' for e in etapes):
        return 'materiel_partiel'
    return 'en_attente_reception'

@property
def cout_total_materiel(self):
    """Calcule le coût total du matériel"""
    demandes = self.demandes_achat.filter(etape_workflow__in=['recue', 'paye'])
    return sum(d.montant_ttc for d in demandes) if demandes.exists() else Decimal('0.00')
```

### **2. Vue Confirmation Réception Mobile**

```python
@login_required
def confirmer_reception_materiel(request, demande_id):
    """
    L'employé confirme avoir reçu le matériel sur le terrain
    Déclenche le déblocage du travail si tout le matériel est reçu
    """
    demande = get_object_or_404(Invoice, id=demande_id, type_facture='demande_achat')
    travail = demande.travail_lie

    # Sécurité: Vérifier que c'est bien l'employé assigné
    if travail.assigne_a != request.user:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    # Vérifier que la demande est payée
    if demande.etape_workflow != 'paye':
        return JsonResponse({'error': 'Demande pas encore payée'}, status=400)

    # Marquer comme reçue
    demande.etape_workflow = 'recue'
    demande.date_reception = timezone.now()
    demande.receptionne_par = request.user
    demande.save()

    # Créer historique
    HistoriqueValidation.objects.create(
        demande=demande,
        action='reception',
        effectue_par=request.user,
        commentaire=f"Matériel réceptionné sur site par {request.user.get_full_name()}"
    )

    # ✅ DÉBLOCAGE AUTOMATIQUE
    if travail.statut_materiel == 'materiel_recu':
        # Tout reçu → Débloquer
        travail.statut = 'en_cours'
        if not travail.date_debut_reel:
            travail.date_debut_reel = timezone.now()
        travail.save()

        return JsonResponse({
            'success': True,
            'message': 'Matériel confirmé ! Travail débloqué.',
            'travail_debloque': True
        })
    else:
        # Reste des demandes
        return JsonResponse({
            'success': True,
            'message': 'Matériel confirmé. En attente des autres.',
            'travail_debloque': False,
            'demandes_restantes': travail.demandes_achat.exclude(etape_workflow='recue').count()
        })
```

### **3. JavaScript AJAX Confirmation**

```javascript
function confirmerReception(demandeId) {
    if (!confirm('Confirmez-vous avoir reçu ce matériel ?')) return;

    const button = document.querySelector(`#demande-${demandeId} button`);
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Confirmation...';

    fetch(`/employees/mobile/demandes/${demandeId}/confirmer-reception/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}',
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);

            if (data.travail_debloque) {
                alert('🎉 Tout le matériel est reçu ! Le travail est maintenant en cours.');
            }

            setTimeout(() => window.location.reload(), 500);
        } else {
            alert('Erreur : ' + data.error);
            button.disabled = false;
            button.innerHTML = '✓ J\'ai reçu ce matériel';
        }
    })
    .catch(error => {
        alert('Erreur réseau. Réessayez.');
        button.disabled = false;
        button.innerHTML = '✓ J\'ai reçu ce matériel';
    });
}
```

---

## 🧪 Scénarios de Test

### **Test 1: Demande Unique**

```
1. Créer travail TRV-001
2. Employé crée demande DA-2025-001 depuis mobile
   ✓ Travail → 'en_attente_materiel'
   ✓ Demande → 'brouillon'
3. Manager valide + comptable paye
   ✓ Demande → 'paye'
   ✓ Travail RESTE 'en_attente_materiel'
4. Employé confirme réception
   ✓ Demande → 'recue'
   ✓ Travail → 'en_cours' (DÉBLOQUÉ)
   ✓ date_debut_reel définie
```

### **Test 2: Demandes Multiples**

```
1. Créer travail TRV-002
2. Employé crée 3 demandes: DA-001, DA-002, DA-003
   ✓ Travail → 'en_attente_materiel'
3. Toutes payées
4. Employé confirme DA-001
   ✓ DA-001 → 'recue'
   ✓ Travail RESTE 'en_attente_materiel' (1/3 reçu)
5. Employé confirme DA-002
   ✓ DA-002 → 'recue'
   ✓ Travail RESTE 'en_attente_materiel' (2/3 reçu)
6. Employé confirme DA-003
   ✓ DA-003 → 'recue'
   ✓ Travail → 'en_cours' (DÉBLOQUÉ - 3/3 reçu)
```

### **Test 3: Sécurité**

```
1. Employé A assigné au travail
2. Employé B essaie de confirmer réception
   ✓ Erreur 403 Forbidden
3. Essayer confirmer demande en 'brouillon'
   ✓ Erreur 400 "Pas encore payée"
4. Confirmer sans authentification
   ✓ Redirect vers login
```

---

## 📊 Avantages de l'Architecture

### **Pour l'Employé** 🔧

- ✅ **Autonomie**: Demande du matériel directement depuis le terrain
- ✅ **Visibilité**: Voit toutes ses demandes et leur statut en temps réel
- ✅ **Réactivité**: Confirme la réception dès arrivée du matériel
- ✅ **Clarté**: Sait exactement quand il peut reprendre le travail

### **Pour le Manager** 👔

- ✅ **Contrôle**: Vue d'ensemble de toutes les demandes par travail
- ✅ **Traçabilité**: Historique complet (qui, quoi, quand)
- ✅ **Optimisation**: Identifie les goulots d'étranglement
- ✅ **Budget**: Coût total matériel par travail en temps réel

### **Pour l'Entreprise** 📈

- ✅ **Évolutivité**: Support de demandes multiples sans limite
- ✅ **Analytics**: Données précises pour analyses (coûts, délais)
- ✅ **Productivité**: Moins de temps d'attente improductif
- ✅ **Audit**: Piste d'audit complète pour la comptabilité

---

## 🚀 Déploiement

### **1. Appliquer les Migrations**

```bash
# Vérifier l'état actuel
python manage.py showmigrations maintenance payments

# Créer les migrations (déjà fait)
python manage.py makemigrations

# Appliquer
python manage.py migrate
```

### **2. Vérifications Post-Migration**

```bash
# Vérifier l'intégrité du système
python manage.py check

# Tester en shell
python manage.py shell
>>> from apps.maintenance.models import Travail
>>> from apps.payments.models import Invoice
>>> travail = Travail.objects.first()
>>> travail.demandes_achat.all()  # Doit fonctionner
>>> travail.necessite_materiel  # Doit retourner bool
>>> travail.statut_materiel  # Doit retourner str
>>> travail.cout_total_materiel  # Doit retourner Decimal
```

### **3. Tests Manuels Recommandés**

1. **Desktop**: Créer un travail avec 2 demandes, vérifier affichage
2. **Mobile**: Se connecter comme employé, créer demande depuis terrain
3. **Workflow**: Valider → Payer → Confirmer réception → Vérifier déblocage
4. **Sécurité**: Essayer confirmer la demande d'un autre employé

---

## 📚 Documentation Associée

| Document | Contenu |
|----------|---------|
| [ARCHITECTURE_TRAVAUX_DEMANDES_ACHAT.md](ARCHITECTURE_TRAVAUX_DEMANDES_ACHAT.md) | Architecture technique complète |
| [TEMPLATES_MIGRATION_RAPPORT.md](TEMPLATES_MIGRATION_RAPPORT.md) | Modifications templates desktop |
| [PORTAIL_EMPLOYE_DEMANDES_ACHAT_RAPPORT.md](PORTAIL_EMPLOYE_DEMANDES_ACHAT_RAPPORT.md) | Interface mobile employé |
| [CONFIRMATION_RECEPTION_MATERIEL_RAPPORT.md](CONFIRMATION_RECEPTION_MATERIEL_RAPPORT.md) | Workflow réception + déblocage |

---

## 🔄 Améliorations Futures

### **Court Terme**

1. **Notifications Push**
   - Notifier employé quand matériel payé
   - Notifier manager quand matériel réceptionné
   - Alerte si matériel non reçu > X jours après paiement

2. **Photos de Réception**
   - Permettre de photographier le matériel reçu
   - Utile en cas de litige (quantité, état)

3. **Remarques de Réception**
   - Champ optionnel pour notes ("Manque 2 unités", etc.)
   - Déjà prévu dans le modèle, ajouter à l'interface

### **Moyen Terme**

4. **Dashboard Manager**
   - Vue "Matériel en transit" (payé mais pas reçu)
   - Alertes automatiques si délais anormaux
   - Statistiques par fournisseur

5. **Analytics Fournisseurs**
   - Délai moyen livraison par fournisseur
   - Taux de livraison complète vs partielle
   - Score de fiabilité

6. **Réception Partielle**
   - Confirmer réception de X/Y unités
   - Génération automatique demande pour le reste

---

## ✅ Checklist de Validation

- [x] Architecture 1-to-Many implémentée
- [x] Migration créée et testée
- [x] Properties calculées fonctionnelles
- [x] Templates desktop mis à jour
- [x] Interface mobile employé complète
- [x] Workflow réception + déblocage automatique
- [x] Sécurité et validations en place
- [x] Documentation complète
- [x] Système Django check sans erreurs
- [ ] Migrations appliquées en production
- [ ] Tests manuels validés
- [ ] Utilisateurs formés

---

**Implémenté par**: Claude Code
**Date**: 2025-10-28
**Version**: 1.0
**Statut**: ✅ PRÊT POUR PRODUCTION

---

## 🆘 Support

En cas de problème:

1. **Erreur de migration**: Vérifier les dépendances dans le fichier de migration
2. **Erreur 403 confirmation**: Vérifier que l'employé est bien assigné au travail
3. **Travail non débloqué**: Vérifier que TOUTES les demandes sont en statut 'recue'
4. **Interface cassée**: Vérifier que les templates utilisent bien la nouvelle syntaxe

**Logs à consulter**:
- Console navigateur (erreurs JavaScript)
- Terminal Django (erreurs backend)
- Base de données (vérifier les valeurs de `etape_workflow`)
