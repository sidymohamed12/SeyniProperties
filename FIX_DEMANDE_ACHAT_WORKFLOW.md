# Corrections - Demande d'Achat: Articles & Workflow

**Date**: 25 Octobre 2025
**Statut**: ✅ COMPLET

---

## 🎯 Objectifs

1. Afficher les articles (lignes) dans le détail d'une facture de demande d'achat
2. Mettre à jour automatiquement le workflow de la demande quand un paiement est effectué

---

## 📋 Problèmes identifiés

### Problème 1: Articles non affichés

**Constat**: Dans la page détail d'une facture de demande d'achat (`/payments/factures/5/`), les articles commandés n'étaient pas affichés.

**Cause**:
- Le modèle `LigneDemandeAchat` existe et contient les articles
- La vue `invoice_detail_view` ne chargeait pas les lignes
- Le template ne prévoyait pas de section pour afficher les articles

### Problème 2: Workflow bloqué après paiement

**Constat**: Quand une demande d'achat est au statut "Chez comptable" (`etape_workflow='comptable'`) et qu'un paiement est effectué, le statut reste bloqué à "Chez comptable".

**Cause**: Le signal `workflow_facture_payee` gérait uniquement le workflow PMO (contrats) mais pas le workflow des demandes d'achat.

---

## ✅ Solutions implémentées

### 1. Affichage des articles

#### Modification de la vue

**Fichier**: [apps/payments/views.py](apps/payments/views.py:391-420)

**Changements**:
1. Ajout de `prefetch_related('lignes_achat')` pour optimiser la requête
2. Ajout conditionnel des permissions pour factures sans contrat
3. Ajout de `lignes_achat` au contexte

```python
def invoice_detail_view(request, pk):
    """
    Vue détail d'une facture
    """
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'contrat__appartement__residence',
            'contrat__locataire__user'
        ).prefetch_related('paiements', 'lignes_achat'),  # ✅ Ajout lignes_achat
        pk=pk
    )

    # Vérification des permissions
    if not request.user.is_staff:
        if hasattr(request.user, 'locataire'):
            if invoice.contrat and invoice.contrat.locataire.user != request.user:  # ✅ Ajout condition
                raise Http404("Facture non trouvée")
        elif hasattr(request.user, 'proprietaire'):
            if invoice.contrat and invoice.contrat.appartement.residence.proprietaire.user != request.user:  # ✅ Ajout condition
                raise Http404("Facture non trouvée")
        else:
            raise Http404("Facture non trouvée")

    context = {
        'invoice': invoice,
        'payments': invoice.paiements.all().order_by('-date_paiement'),
        'lignes_achat': invoice.lignes_achat.all() if invoice.type_facture == 'demande_achat' else None,  # ✅ Ajout
    }

    return render(request, 'payments/invoice_detail.html', context)
```

**Optimisations**:
- ✅ `prefetch_related('lignes_achat')` évite les requêtes N+1
- ✅ Chargement conditionnel (seulement pour demandes d'achat)
- ✅ Permissions corrigées pour factures sans contrat

#### Ajout de la section dans le template

**Fichier**: [templates/payments/invoice_detail.html](templates/payments/invoice_detail.html:190-266)

**Section ajoutée**: "Articles demandés"

```django
<!-- Articles de la demande d'achat -->
{% if lignes_achat %}
<div class="info-card">
    <h2 class="section-header text-xl font-semibold text-gray-900">
        <i class="fas fa-shopping-cart text-orange-600 mr-2"></i>
        Articles demandés ({{ lignes_achat.count }})
    </h2>

    <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th>Désignation</th>
                    <th>Quantité</th>
                    <th>P.U.</th>
                    <th>Total</th>
                    <th>Fournisseur</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for ligne in lignes_achat %}
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3">
                        <div class="text-sm font-medium text-gray-900">{{ ligne.designation }}</div>
                        {% if ligne.motif %}
                        <div class="text-xs text-gray-500 mt-1">{{ ligne.motif|truncatewords:15 }}</div>
                        {% endif %}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-900">
                        {{ ligne.quantite|floatformat:0 }} {{ ligne.unite }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-900">
                        {{ ligne.prix_unitaire|floatformat:0 }} FCFA
                    </td>
                    <td class="px-4 py-3 text-sm font-semibold text-gray-900">
                        {{ ligne.prix_total|floatformat:0 }} FCFA
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">
                        {{ ligne.fournisseur|default:"Non spécifié" }}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
            <tfoot class="bg-gray-50">
                <tr>
                    <td colspan="3" class="px-4 py-3 text-right text-sm font-semibold text-gray-900">
                        Total estimé:
                    </td>
                    <td colspan="2" class="px-4 py-3 text-sm font-bold text-blue-600">
                        {{ invoice.montant_ttc|floatformat:0 }} FCFA
                    </td>
                </tr>
            </tfoot>
        </table>
    </div>

    <!-- Motif principal de la demande -->
    {% if invoice.motif_principal %}
    <div class="mt-4 p-4 bg-blue-50 rounded-lg">
        <p class="text-sm font-medium text-blue-900 mb-1">
            <i class="fas fa-info-circle mr-2"></i>Motif principal de la demande
        </p>
        <p class="text-sm text-blue-700">{{ invoice.motif_principal }}</p>
    </div>
    {% endif %}
</div>
{% endif %}
```

**Affichage**:
- ✅ Tableau responsive avec colonnes: Désignation, Quantité, Prix unitaire, Total, Fournisseur
- ✅ Affichage du motif de chaque article (tronqué à 15 mots)
- ✅ Total estimé en pied de tableau
- ✅ Motif principal de la demande dans un encadré bleu
- ✅ Design cohérent avec le reste de l'application

---

### 2. Mise à jour automatique du workflow

#### Modification du signal Payment

**Fichier**: [apps/payments/signals.py](apps/payments/signals.py:75-96)

**Ajout**: Section 4 - Workflow Demande d'Achat

```python
# ============================================
# 4. METTRE À JOUR LE WORKFLOW DEMANDE D'ACHAT
# ============================================
if facture.type_facture == 'demande_achat' and hasattr(facture, 'etape_workflow'):
    if facture.statut == 'payee':
        # Si la demande était "chez comptable", passer à "payé"
        if facture.etape_workflow == 'comptable':
            facture.etape_workflow = 'paye'
            facture.save(update_fields=['etape_workflow'])
            print(f"✅ Demande d'achat {facture.numero_facture} - Workflow: comptable → payé")

            # Créer une entrée dans l'historique
            try:
                from apps.payments.models_extensions import HistoriqueValidation
                HistoriqueValidation.objects.create(
                    demande=facture,
                    action='paiement',
                    effectue_par=instance.valide_par,
                    commentaire=f"Paiement {instance.numero_paiement} validé - Montant: {instance.montant} FCFA"
                )
            except Exception as e:
                print(f"⚠️ Erreur création historique: {e}")
```

**Logique**:
1. ✅ Vérifie que c'est une facture de demande d'achat
2. ✅ Vérifie que le champ `etape_workflow` existe
3. ✅ Vérifie que la facture est complètement payée
4. ✅ Si l'étape actuelle est "comptable", passe à "payé"
5. ✅ Crée une entrée dans l'historique des validations
6. ✅ Log console pour traçabilité

---

## 🔄 Workflow de demande d'achat complet

### Étapes du workflow (`etape_workflow`)

```
1. brouillon          → Création de la demande
2. en_attente         → Soumission pour validation
3. valide_responsable → Validation par responsable
4. comptable          → En traitement comptable (génération facture)
5. validation_dg      → En attente validation DG (si montant élevé)
6. approuve           → Approuvé - En attente achat
7. en_cours_achat     → Achat en cours
8. recue              → Marchandise reçue
9. paye               → ✅ PAYÉ (nouvelle correction)
10. refuse            → Refusé
11. annule            → Annulé
```

### Flux normal

```
Demande créée (brouillon)
    ↓
Soumission (en_attente)
    ↓
Validation responsable (valide_responsable)
    ↓
Traitement comptable (comptable)
    ↓
Génération facture
    ↓
Paiement effectué ✅ NOUVEAU
    ↓
Signal déclenché → Workflow: comptable → paye ✅
    ↓
Demande marquée comme payée
```

### Avant la correction

```
Traitement comptable (comptable)
    ↓
Génération facture
    ↓
Paiement effectué
    ↓
❌ Workflow reste à "comptable"  # PROBLÈME
```

### Après la correction

```
Traitement comptable (comptable)
    ↓
Génération facture
    ↓
Paiement effectué et validé
    ↓
✅ Signal déclenche automatiquement
    ↓
Workflow: comptable → paye
    ↓
Historique créé
```

---

## 📊 Modèles impliqués

### Invoice (Facture/Demande)

```python
class Invoice(BaseModel):
    # ... champs de base ...

    # Pour demandes d'achat
    type_facture = 'demande_achat'
    etape_workflow = 'comptable'  # Mise à jour par signal
    motif_principal = "Achat matériel construction"
    demandeur = User
    # ...
```

### LigneDemandeAchat (Article)

```python
class LigneDemandeAchat(BaseModel):
    demande = ForeignKey(Invoice, related_name='lignes_achat')
    designation = "Ciment Portland 50kg"
    quantite = Decimal('100')
    unite = "sac"
    fournisseur = "SOCOCIM"
    prix_unitaire = Decimal('4500')
    prix_total = Decimal('450000')  # Auto-calculé
    motif = "Construction mur enceinte"
```

### Payment (Paiement)

```python
class Payment(BaseModel):
    facture = ForeignKey(Invoice)
    montant = Decimal('450000')
    statut = 'valide'  # Déclenche le signal
    valide_par = User  # Utilisé dans historique
```

### HistoriqueValidation (Traçabilité)

```python
class HistoriqueValidation(BaseModel):
    demande = ForeignKey(Invoice)
    action = 'paiement'
    effectue_par = User
    commentaire = "Paiement PAY-2025-001 validé - Montant: 450000 FCFA"
    date_action = auto_now_add=True
```

---

## 🧪 Tests à effectuer

### Test 1: Affichage des articles

```
1. Créer une demande d'achat avec plusieurs articles:
   - Article 1: Ciment Portland 50kg × 100 sacs @ 4500 FCFA
   - Article 2: Fer à béton 10mm × 50 barres @ 12000 FCFA
   - Article 3: Sable fin × 10 m³ @ 15000 FCFA

2. Générer la facture depuis le comptable

3. Accéder à /payments/factures/<id>/

4. ✅ Vérifier l'affichage de la section "Articles demandés"
5. ✅ Vérifier le tableau avec 3 lignes
6. ✅ Vérifier les colonnes: Désignation, Quantité, P.U., Total, Fournisseur
7. ✅ Vérifier le motif de chaque article (tronqué)
8. ✅ Vérifier le total en pied: 1 100 000 FCFA
9. ✅ Vérifier l'affichage du motif principal
```

### Test 2: Workflow automatique

```
Conditions initiales:
- Demande d'achat existante avec etape_workflow='comptable'
- Facture générée, statut='emise'
- Montant total: 450 000 FCFA

Étapes:
1. Aller sur /payments/factures/<id>/
2. Cliquer sur "Enregistrer un paiement"
3. Remplir le formulaire:
   - Montant: 450 000 FCFA
   - Date: Aujourd'hui
   - Moyen: Virement bancaire
   - Référence: VIR-2025-001
4. Valider le paiement

Résultats attendus:
✅ Paiement créé avec statut 'valide'
✅ Facture.statut passe à 'payee'
✅ Invoice.etape_workflow passe de 'comptable' à 'paye'
✅ Entrée créée dans HistoriqueValidation avec action='paiement'
✅ Message console: "Demande d'achat INV-2025-001 - Workflow: comptable → payé"

Vérifications:
5. Recharger la page de la demande
6. ✅ Statut affiché: "Payé"
7. Vérifier la console/logs
8. ✅ Message de workflow visible
9. Accéder à l'historique de la demande
10. ✅ Nouvelle entrée "Paiement - [Date] - [Utilisateur]"
```

### Test 3: Cas limites

#### 3.1 Paiement partiel
```
- Montant facture: 450 000 FCFA
- Paiement 1: 200 000 FCFA

✅ Workflow ne change PAS (facture non complètement payée)
```

#### 3.2 Multiples paiements
```
- Montant facture: 450 000 FCFA
- Paiement 1: 200 000 FCFA → Workflow reste 'comptable'
- Paiement 2: 250 000 FCFA → Workflow passe à 'paye'
```

#### 3.3 Demande à une autre étape
```
- etape_workflow='validation_dg'
- Paiement effectué

✅ Workflow ne change PAS (pas à l'étape 'comptable')
```

---

## 📊 Résumé des modifications

### Fichiers modifiés

| Fichier | Lignes modifiées | Type |
|---------|------------------|------|
| [apps/payments/views.py](apps/payments/views.py:391-420) | ~30 lignes | Vue |
| [templates/payments/invoice_detail.html](templates/payments/invoice_detail.html:190-266) | ~77 lignes | Template |
| [apps/payments/signals.py](apps/payments/signals.py:75-96) | ~22 lignes | Signal |
| **Total** | **~129 lignes** | - |

### Nouveaux fichiers

| Fichier | Lignes | Description |
|---------|--------|-------------|
| [FIX_DEMANDE_ACHAT_WORKFLOW.md](FIX_DEMANDE_ACHAT_WORKFLOW.md) | ~500 lignes | Ce rapport |

---

## ✨ Résultat final

### Avant

❌ Articles de la demande d'achat invisibles
❌ Workflow bloqué à "Chez comptable" après paiement
❌ Pas de traçabilité du paiement dans l'historique

### Après

✅ Tableau complet des articles avec:
  - Désignation et motif de chaque article
  - Quantité, prix unitaire, total
  - Fournisseur
  - Total général
  - Motif principal de la demande

✅ Workflow automatique:
  - Détection du paiement validé
  - Mise à jour automatique: comptable → paye
  - Création d'entrée dans l'historique
  - Logs console pour debug

✅ Traçabilité complète:
  - Qui a payé
  - Quand
  - Combien
  - Référence du paiement

---

## 🔜 Améliorations futures possibles

### Court terme

1. **Notification automatique**: Envoyer un email au demandeur quand le paiement est effectué
2. **Affichage du workflow**: Badge visuel sur la page montrant l'étape actuelle
3. **Historique complet**: Afficher l'historique des validations sur la page détail

### Moyen terme

1. **Gestion de réception**: Permettre de marquer les articles comme reçus
2. **Écarts prix/quantité**: Signaler si prix réel ≠ prix estimé
3. **Export articles**: Bouton pour exporter la liste des articles en PDF/Excel
4. **Statistiques**: Dashboard des demandes par statut/montant

### Long terme

1. **Workflow configurable**: Permettre de personnaliser les étapes
2. **Règles automatiques**: Validation auto si montant < seuil
3. **Intégration ERP**: Synchronisation avec logiciel comptable externe
4. **Scan factures**: OCR pour extraire automatiquement les lignes

---

**Fin du rapport**
**Date**: 25 Octobre 2025
**Statut**: ✅ COMPLET
