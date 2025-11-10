# Formulaire d'Enregistrement Tiers - Guide d'Utilisation

## 📋 Vue d'ensemble

Le fichier `nouveau_tiers.html` est le **formulaire unifié** pour l'enregistrement de tous les types de tiers dans le système Seyni Properties.

## 🎯 Objectif

Remplacer les anciens formulaires séparés (`nouveau_bailleur.html`, `nouveau_locataire.html`) par un seul formulaire dynamique compatible avec l'architecture Tiers.

## ✨ Fonctionnalités

### 1. Types de Tiers Supportés
- **Propriétaire** : Propriétaires de biens immobiliers
- **Locataire** : Locataires de biens
- **Prestataire** : Fournisseurs de services (plombiers, électriciens, etc.)
- **Partenaire** : Partenaires commerciaux
- **Investisseur** : Investisseurs immobiliers
- **Autre** : Autres types de tiers

### 2. Sections Dynamiques

Le formulaire affiche des sections conditionnelles selon le type de tiers sélectionné :

#### Pour les Propriétaires :
- Type de bailleur (Particulier/Entreprise/SCI)
- Nom de l'entreprise (si applicable)
- Numéro SIRET/NINEA
- Adresse fiscale

#### Pour les Locataires :
- Situation professionnelle
- Date d'entrée prévue
- Informations du garant

### 3. Champs Communs (Obligatoires)

- Nom *
- Email *
- Téléphone principal *
- Adresse complète *
- Ville *

### 4. Champs Optionnels

- Prénom
- Téléphone secondaire
- Quartier
- Code postal
- Numéro pièce d'identité
- Document d'identité (upload)
- Notes internes
- Document complémentaire

### 5. Création de Compte Utilisateur

Checkbox optionnelle pour créer automatiquement un compte utilisateur permettant au tiers d'accéder au portail.

## 🔧 Utilisation

### Intégration dans une page

```django
{% include 'dashboard/forms/nouveau_tiers.html' %}
```

### Pré-sélection du type

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const typeTiersSelect = document.getElementById('type-tiers-select');
    if (typeTiersSelect) {
        typeTiersSelect.value = 'proprietaire'; // ou 'locataire', etc.
        typeTiersSelect.dispatchEvent(new Event('change'));
    }
});
```

## 📝 Champs du Formulaire (Mapping avec le Modèle Tiers)

| Nom du champ | Type | Champ modèle | Obligatoire |
|-------------|------|--------------|-------------|
| `type_tiers` | select | `type_tiers` | Oui |
| `nom` | text | `nom` | Oui |
| `prenom` | text | `prenom` | Non |
| `email` | email | `email` | Oui |
| `telephone` | tel | `telephone` | Oui |
| `telephone_secondaire` | tel | `telephone_secondaire` | Non |
| `adresse` | textarea | `adresse` | Oui |
| `ville` | text | `ville` | Oui (défaut: Dakar) |
| `quartier` | text | `quartier` | Non |
| `code_postal` | text | `code_postal` | Non |
| `piece_identite_numero` | text | `piece_identite_numero` | Non |
| `piece_identite` | file | `piece_identite` | Non |
| `autre_document` | file | `autre_document` | Non |
| `type_bailleur` | select | `type_bailleur` | Non (si propriétaire) |
| `entreprise` | text | `entreprise` | Non |
| `numero_siret` | text | `numero_siret` | Non |
| `adresse_fiscale` | textarea | `adresse_fiscale` | Non |
| `situation_pro` | select | `situation_pro` | Non (si locataire) |
| `date_entree` | date | `date_entree` | Non (si locataire) |
| `garant_nom` | text | `garant_nom` | Non (si locataire) |
| `garant_tel` | tel | `garant_tel` | Non (si locataire) |
| `notes` | textarea | `notes` | Non |
| `creer_compte` | checkbox | N/A | Non (traitement backend) |

## 🎨 Personnalisation CSS

Le formulaire inclut des styles CSS inline pour :
- Inputs avec focus states
- Selects avec flèches personnalisées
- États disabled
- Responsive design

## ✅ Validation

### Côté Client (JavaScript)
- Vérification du type de tiers sélectionné
- Validation du format téléphone (regex)
- Validation des fichiers uploadés

### Côté Serveur (À Implémenter)
- Vérification email unique
- Validation téléphone format sénégalais
- Taille fichiers < 5MB
- Types de fichiers autorisés

## 🔄 Migration depuis Anciens Formulaires

Les anciens formulaires (`nouveau_bailleur.html`, `nouveau_locataire.html`) ont été mis à jour pour inclure automatiquement le nouveau formulaire unifié avec pré-sélection du type.

### Compatibilité
✅ Les liens existants vers les anciens formulaires continuent de fonctionner
✅ Le type de tiers est automatiquement pré-sélectionné selon le formulaire appelé

## 📊 Exemple de Traitement Backend (Vue Django)

```python
from apps.tiers.models import Tiers
from django.contrib.auth.models import User

def create_tiers(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        type_tiers = request.POST.get('type_tiers')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom', '')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        # ... autres champs

        # Créer le tiers
        tiers = Tiers.objects.create(
            type_tiers=type_tiers,
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            # ... autres champs
            cree_par=request.user
        )

        # Créer compte utilisateur si demandé
        if request.POST.get('creer_compte'):
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=prenom,
                last_name=nom
            )
            # Générer mot de passe temporaire
            temp_password = User.objects.make_random_password()
            user.set_password(temp_password)
            user.save()

            # Associer au tiers
            tiers.user = user
            tiers.save()

            # Envoyer email avec identifiants
            # ...

        return JsonResponse({'success': True, 'tiers_id': tiers.id})
```

## 🐛 Dépannage

### Le formulaire ne s'affiche pas correctement
- Vérifier que Font Awesome est chargé (pour les icônes)
- Vérifier la compatibilité du navigateur (ES6 requis)

### Les sections conditionnelles ne s'affichent pas
- Vérifier la console JavaScript pour les erreurs
- S'assurer que les IDs des éléments sont uniques dans la page

### Upload de fichiers ne fonctionne pas
- Vérifier que le form a `enctype="multipart/form-data"`
- Vérifier les permissions du dossier `media/tiers/`

## 📅 Historique des Versions

### v1.0 (2025-01-23)
- Création du formulaire unifié
- Support de 6 types de tiers
- Sections dynamiques
- Validation client
- Compatibilité avec anciens formulaires

## 🔮 Améliorations Futures

- [ ] Autocomplétion adresses (API Google Maps)
- [ ] Validation SIRET en temps réel
- [ ] Prévisualisation des fichiers uploadés
- [ ] Scan CNI automatique (OCR)
- [ ] Export/Import CSV pour création en masse
- [ ] Multi-langues (Français/Anglais/Wolof)

## 📞 Support

Pour toute question ou problème avec ce formulaire, contactez l'équipe de développement.
