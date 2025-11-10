# Seyni Properties - Logiciel de Gestion Locative

## 📋 Description

Plateforme de gestion locative complète pour Seyni Properties (Filiale Imani), permettant la gestion intégrée des biens immobiliers, locataires, bailleurs, paiements, équipes d'intervention et maintenance.

## 🏗️ Architecture

- **Backend**: Django 4.2.7 + Django REST Framework
- **Base de données**: PostgreSQL (SQLite pour développement)
- **Frontend**: Django Templates + HTMX + Alpine.js + Tailwind CSS
- **Authentification**: JWT + Django Allauth
- **Notifications**: Twilio (SMS/WhatsApp)
- **Paiements**: Orange Money, Wave API

## 🚀 Fonctionnalités

### 🏠 Gestion Immobilière
- **Biens immobiliers**: Studios, appartements, villas, locaux commerciaux
- **Médias**: Photos, documents, plans
- **Statuts**: Libre, occupé, maintenance, réservé
- **Géolocalisation**: Dakar et environs

### 👥 Gestion Utilisateurs
- **Locataires**: Profils, contrats, historique paiements
- **Bailleurs**: Particuliers/entreprises, relevés automatiques
- **Employés**: Techniciens, agents terrain, managers, comptables
- **Portails dédiés** pour chaque type d'utilisateur

### 📄 Contrats & Paiements
- **Contrats**: Création, renouvellement, résiliation
- **Factures**: Génération automatique, relances
- **Paiements**: Multi-canaux (espèces, mobile money, virement)
- **Rappels**: SMS/WhatsApp automatiques

### 🔧 Maintenance & Interventions
- **Signalements**: Via portail locataire ou interne
- **Assignation**: Automatique aux techniciens
- **Suivi**: Photos avant/après, satisfaction client
- **Maintenance préventive**: Programmation récurrente

### 📊 Comptabilité & Reporting
- **Relevés bailleurs**: Calculs automatiques des commissions
- **Dépenses**: Tracking et validation
- **Rapports**: Financiers, occupation, maintenance
- **Exports**: PDF, Excel

### 🔔 Notifications
- **Multi-canal**: SMS, WhatsApp, Email
- **Templates personnalisables**: Français/Wolof
- **Automatisation**: Paiements, contrats, interventions

## 📱 Modules

```
seyni_properties/
├── apps/
│   ├── accounts/      # Gestion utilisateurs
│   ├── properties/    # Biens immobiliers
│   ├── contracts/     # Contrats de location
│   ├── payments/      # Paiements et factures
│   ├── maintenance/   # Interventions
│   ├── accounting/    # Comptabilité
│   ├── notifications/ # Système de notifications
│   ├── portals/       # Portails utilisateurs
│   ├── dashboard/     # Tableaux de bord
│   └── core/          # Utilitaires communs
```

## ⚡ Installation

### Prérequis
- Python 3.11+
- PostgreSQL
- Git

### Installation locale

```bash
# 1. Cloner le projet
git clone https://github.com/InsaDiouf/SeyniProperties.git
cd SeyniProperties

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configuration environnement
cp .env.example .env
# Modifier .env avec vos paramètres

# 5. Base de données
python manage.py makemigrations
python manage.py migrate

# 6. Créer un superuser
python manage.py createsuperuser

# 7. Charger les données de test (optionnel)
python manage.py loaddata scripts/fixtures/message_templates.json

# 8. Lancer le serveur
python manage.py runserver
```

### Variables d'environnement (.env)

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/seyni_properties

# Twilio (SMS/WhatsApp)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 🎯 Accès aux interfaces

- **Admin Django**: `http://localhost:8000/admin/`
- **API REST**: `http://localhost:8000/api/v1/`
- **Portail Locataire**: `http://localhost:8000/tenant/`
- **Portail Bailleur**: `http://localhost:8000/landlord/`
- **Dashboard Manager**: `http://localhost:8000/dashboard/`

## 🛠️ Développement

### Structure des rôles
- **Manager**: Supervision globale, tous accès
- **Comptable**: Paiements, factures, relevés
- **Agent terrain**: Tâches, interventions
- **Technicien**: Maintenance, réparations
- **Locataire**: Portail dédié, paiements
- **Bailleur**: Relevés, propriétés

### Workflow Git
```bash
# Développement
git checkout develop
git pull origin develop
git checkout -b feature/nouvelle-fonctionnalite

# Après développement
git add .
git commit -m "feat: description de la fonctionnalité"
git push origin feature/nouvelle-fonctionnalite

# Pull Request vers develop
```

## 🚀 Déploiement

### VPS Hostinger (Production)
```bash
# Script de déploiement
chmod +x scripts/deploy_hostinger.sh
./scripts/deploy_hostinger.sh
```

### Configuration serveur
- **Serveur web**: Nginx + Gunicorn
- **Base de données**: PostgreSQL
- **SSL**: Certbot/Let's Encrypt
- **Backup**: Scripts automatisés

## 📈 Roadmap

### Phase 1 (Actuelle)
- ✅ Gestion des biens et utilisateurs
- ✅ Contrats et paiements de base
- ✅ Interface admin complète
- 🔄 Portails utilisateurs

### Phase 2
- 📱 Application mobile
- 🏪 Marketplace locatif
- 🤖 IA pour matching locataire/bien
- 📊 Analytics avancés

### Phase 3
- 🌍 Multi-villes (Thiès, Saint-Louis)
- 💳 Paiements internationaux
- 🏢 Version SaaS multi-agences

## 🤝 Contribution

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📞 Support

- **Email**: support@seyniproperties.sn
- **Téléphone**: +221 XX XXX XX XX
- **GitHub Issues**: [Issues](https://github.com/InsaDiouf/SeyniProperties/issues)

## 📄 Licence

Propriétaire - Seyni Properties © 2025

---

**Développé avec ❤️ pour la transformation digitale de l'immobilier au Sénégal**