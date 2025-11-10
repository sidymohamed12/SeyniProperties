# Module Gestion des Tiers

## Description

Module de gestion des tiers pour Seyni Properties, permettant aux commerciaux de gérer les informations relatives aux clients, propriétaires, partenaires et prestataires dans le processus immobilier.

## Fonctionnalités

### 1. Gestion des Tiers

- **Ajouter un tiers**: Créer un nouveau tiers avec toutes ses informations
- **Modifier un tiers**: Mettre à jour les informations d'un tiers existant
- **Supprimer un tiers**: Supprimer un tiers (uniquement s'il n'a pas de biens liés)
- **Consulter un tiers**: Voir tous les détails d'un tiers et ses biens liés

### 2. Types de Tiers

- Propriétaire
- Locataire
- Prestataire
- Partenaire
- Investisseur
- Autre

### 3. Liaison Tiers-Bien

- Lier un tiers à un appartement ou une résidence
- Définir le type de contrat (Location, Vente, Gestion)
- Définir le type de mandat (Exclusif, Non exclusif, Sans mandat)
- Gérer les commissions
- Joindre les documents contractuels

### 4. Recherche et Filtres

- Recherche textuelle (nom, prénom, email, téléphone, référence)
- Filtrage par type de tiers
- Filtrage par statut
- Filtrage par ville

### 5. Statistiques

- Répartition par type de tiers
- Répartition par statut
- Répartition par type de contrat
- Top 10 des tiers avec le plus de biens liés

## Installation et Configuration

### 1. Création des migrations

```bash
python manage.py makemigrations tiers
python manage.py migrate tiers
```

### 2. Accès au module

Le module est accessible via:
- **URL**: `/tiers/`
- **Admin Django**: `/admin/tiers/`

### 3. URLs disponibles

```python
/tiers/                          # Liste des tiers
/tiers/ajouter/                  # Ajouter un tiers
/tiers/<id>/                     # Détail d'un tiers
/tiers/<id>/modifier/            # Modifier un tiers
/tiers/<id>/supprimer/           # Supprimer un tiers
/tiers/statistiques/             # Statistiques des tiers
/tiers/bien/ajouter/             # Lier un tiers à un bien
/tiers/bien/ajouter/<tiers_id>/  # Lier un tiers spécifique à un bien
/tiers/bien/<id>/modifier/       # Modifier une liaison
/tiers/bien/<id>/supprimer/      # Supprimer une liaison
/tiers/search-api/               # API de recherche (AJAX)
```

## Modèles de Données

### Modèle Tiers

```python
- reference (auto-généré: TIER-2025-XXXXXX)
- nom, prenom
- type_tiers (proprietaire, locataire, prestataire, etc.)
- telephone, telephone_secondaire, email
- adresse, ville, quartier, code_postal
- statut (actif, inactif, en_attente, archive)
- piece_identite, autre_document
- notes
- cree_par, modifie_par
- created_at, updated_at
```

### Modèle TiersBien

```python
- tiers (ForeignKey)
- appartement (ForeignKey, optionnel)
- residence (ForeignKey, optionnel)
- type_contrat (location, vente, gestion)
- type_mandat (exclusif, non_exclusif, sans_mandat)
- date_debut, date_fin
- statut (en_cours, termine, suspendu, annule)
- montant_commission, pourcentage_commission
- contrat_signe, mandat_document
- notes
```

## Utilisation

### Ajouter un nouveau tiers

1. Accéder à `/tiers/`
2. Cliquer sur "Ajouter un Tiers"
3. Remplir le formulaire:
   - Informations générales (nom, prénom, type)
   - Coordonnées (téléphone, email, adresse)
   - Documents (pièce d'identité, autres)
   - Notes
4. Cliquer sur:
   - "Ajouter" pour enregistrer et voir le détail
   - "Enregistrer et ajouter un autre" pour créer un autre tiers
   - "Enregistrer et lier à un bien" pour créer une liaison immédiatement

### Lier un tiers à un bien

1. Depuis la page de détail d'un tiers, cliquer sur "Lier à un bien"
2. Remplir le formulaire:
   - Sélectionner l'appartement OU la résidence
   - Définir le type de contrat
   - Définir le type de mandat
   - Dates de début et fin
   - Commission (montant ou pourcentage)
   - Documents contractuels
3. Enregistrer

### Rechercher un tiers

1. Utiliser la barre de recherche sur la page liste
2. Filtrer par type, statut ou ville
3. Cliquer sur "Rechercher"

### Consulter les statistiques

1. Accéder à `/tiers/statistiques/`
2. Consulter:
   - Répartition par type
   - Répartition par statut
   - Répartition par type de contrat
   - Top 10 des tiers

## Permissions et Sécurité

- Toutes les vues nécessitent une authentification (`@login_required`)
- La suppression d'un tiers est bloquée s'il a des biens liés
- Les dates sont validées (date_fin >= date_debut)
- L'email doit être unique
- Au moins un bien (appartement ou résidence) doit être lié

## Intégration avec le Dashboard

Pour intégrer le module dans le dashboard commercial, ajouter dans le menu de navigation:

```html
<a href="{% url 'tiers:tiers_liste' %}" class="nav-link">
    <i class="fas fa-users"></i>
    <span>Gestion des Tiers</span>
</a>
```

## API de Recherche

Une API de recherche AJAX est disponible pour l'autocomplétion:

```javascript
// Exemple d'utilisation avec Select2
$('#tiers-select').select2({
    ajax: {
        url: '/tiers/search-api/',
        dataType: 'json',
        delay: 250,
        data: function (params) {
            return {
                q: params.term
            };
        },
        processResults: function (data) {
            return {
                results: data.results
            };
        }
    }
});
```

## Personnalisation

### Ajouter un nouveau type de tiers

Dans `models.py`:

```python
TYPE_TIERS_CHOICES = [
    ('proprietaire', 'Propriétaire'),
    ('locataire', 'Locataire'),
    # ...
    ('nouveau_type', 'Nouveau Type'),  # Ajouter ici
]
```

Puis créer une migration:

```bash
python manage.py makemigrations tiers
python manage.py migrate tiers
```

### Modifier les champs du formulaire

Éditer `forms.py` pour ajouter/retirer des champs dans `TiersForm` ou `TiersBienForm`.

## Support

Pour toute question ou problème:
- Consulter la documentation Django: https://docs.djangoproject.com/
- Vérifier les logs dans la console de développement
- Contacter l'équipe de développement

## Roadmap

- [ ] Export Excel/PDF de la liste des tiers
- [ ] Importation en masse (CSV)
- [ ] Historique des modifications
- [ ] Notifications automatiques (anniversaires, renouvellements)
- [ ] Rapports avancés
- [ ] Intégration avec le module CRM
