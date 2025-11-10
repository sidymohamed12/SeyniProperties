# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Seyni Properties** is a Django-based property management platform (Logiciel de Gestion Locative) for the Senegalese real estate market. It manages rental properties, tenants, landlords, contracts, payments, maintenance, and accounting operations.

- **Tech Stack**: Django 4.2.7, PostgreSQL, HTMX, Alpine.js, Tailwind CSS
- **Language**: Python 3.11+, French for business logic
- **Deployment**: Railway.app with automated cron jobs
- **User Types**: manager, accountant, field_agent, technician, tenant, landlord

## Critical Architecture Concepts

### 1. Tiers System (NEW - Migration in Progress)

**IMPORTANT**: The project is undergoing a major architectural refactoring from separate `Bailleur`/`Locataire` models to a unified `Tiers` model.

**Key Principles**:
- **Single source of truth**: `apps.tiers.Tiers` replaces old `accounts.Bailleur` and `accounts.Locataire` models
- **Optional user accounts**: `Tiers.user` is nullable - not all tiers need system access
- **Direct data access**: Use `tiers.nom_complet` instead of `tiers.user.get_full_name()`
- **Multi-role support**: One person can have multiple `type_tiers` (proprietaire, locataire, prestataire, etc.)

**Legacy Code**:
- Apps `landlords` and `tenants` still exist but are deprecated
- DO NOT add new features to these apps
- When working with properties/contracts, always use `tiers.Tiers`

**Template Patterns**:
```django
{# ❌ OLD - Don't use #}
{{ bailleur.user.get_full_name }}
{{ locataire.user.email }}

{# ✅ NEW - Use this #}
{{ proprietaire.nom_complet }}
{{ locataire.email }}
```

### 2. Property Hierarchy

**3-tier structure**: `Tiers` (proprietaire) → `Residence` → `Appartement`

- **Residence**: Building/complex (e.g., "Résidence Les Palmiers")
- **Appartement**: Individual rental unit within a residence
- **Access pattern**: `appartement.residence.proprietaire` to get owner

**Why this matters**:
- Contracts link to `Appartement`, not `Residence`
- Invoices are per apartment, not per building
- Owner relationships are defined at the Residence level

### 3. Reference Generation System

All entities use auto-generated unique references via `apps.core.utils.generate_unique_reference()`:

- `TIER-2025-001234` (Tiers)
- `RES-001` (Residence)
- `APP-001` (Appartement)
- `CTR-2025-001` (RentalContract)
- `INV-2025-001234` (Invoice)

**Never manually set** the `reference` field - it's auto-populated on save.

### 4. Invoice Type System

The `Invoice` model has been extended beyond just rent (`loyer`) to support:
- `loyer`: Monthly rent
- `syndic`: Co-ownership fees
- `demande_achat`: Purchase requests
- `prestataire`: Service provider invoices
- `charges`, `penalites`, `autres`

When working with invoices, check the `type_facture` field to determine context.

## Development Commands

### Setup & Running

```bash
# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixtures (optional)
python manage.py loaddata scripts/fixtures/message_templates.json

# Run development server
python manage.py runserver
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.tiers
python manage.py test apps.contracts

# Run specific test file
python manage.py test tests.test_models.test_properties
```

**NOTE**: Test coverage is currently minimal - most test files are empty stubs.

### Custom Management Commands

```bash
# Generate monthly invoices (runs automatically via cron on 25th at 2 AM)
python manage.py generate_monthly_invoices

# Check overdue invoices (runs daily at 9 AM)
python manage.py check_overdue_invoices

# Send payment reminders (runs weekly on Mondays at 8 AM)
python manage.py send_payment_reminders

# Setup mobile interface for employees
python manage.py setup_mobile

# Generate syndic cotisations (for co-ownership management)
python manage.py generate_syndic_cotisations
python manage.py generate_syndic_cotisations --annee 2025 --periode Q1
python manage.py generate_syndic_cotisations --dry-run  # Simulation mode
```

### Migration Tools

For the Tiers architecture migration:

```bash
# Analyze templates for compatibility
python analyze_templates.py

# Auto-fix template issues
python fix_templates.py

# Validate Tiers architecture
python test_tiers_architecture.py
```

## Code Patterns & Conventions

### Model Queries - Select/Prefetch Related

**CRITICAL**: Always optimize queries with `select_related()` and `prefetch_related()` to avoid N+1 problems.

```python
# ❌ BAD - Causes N+1 queries
contrats = RentalContract.objects.all()

# ✅ GOOD - Optimized
contrats = RentalContract.objects.select_related(
    'appartement',
    'locataire',
    'appartement__residence',
    'appartement__residence__proprietaire'
).prefetch_related('factures')
```

### Naming Conventions

- **French** for business domain: `locataire`, `proprietaire`, `loyer_mensuel`
- **English** for technical Django concepts: `created_at`, `updated_at`, `is_active`
- **Dual fields** exist during migration: both `loyer_base` and `base_rent` may be present

### Environment Variables

**SECURITY**: Never hardcode credentials. Required environment variables:

```bash
# Required in production
SECRET_KEY=...
DATABASE_URL=postgresql://...
RAILWAY_ENVIRONMENT=production

# Email (if using SMTP)
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Notifications
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
```

Local development uses SQLite by default; PostgreSQL is auto-configured if `DATABASE_URL` is set.

### File Upload Paths

Media files are organized by entity type:
- `tiers/pieces_identite/` - ID documents
- `tiers/contrats/` - Signed contracts
- `properties/photos/` - Property images
- `maintenance/photos/` - Maintenance work photos

## Common Workflows

### Adding a New Property

1. Create or identify a `Tiers` with `type_tiers='proprietaire'`
2. Create a `Residence` linked to that proprietaire
3. Create `Appartement` instances within the residence
4. Optionally upload `AppartementMedia` (photos, documents)

### Creating a Rental Contract

1. Ensure `Tiers` exists with `type_tiers='locataire'`
2. Select available `Appartement` (status='libre')
3. Create `RentalContract` linking locataire + appartement
4. Contract status progresses: `brouillon` → `actif` → `expire`/`resilie`

### Invoice Generation Flow

1. Automated: Cron job runs `generate_monthly_invoices` on 25th of each month
2. Creates invoices for all active contracts
3. Triggers notifications via `apps.notifications`
4. Payment tracking via `Payment` model linked to `Invoice`

## App-Specific Notes

### apps.tiers
- **Central registry** for all third parties (proprietaires, locataires, coproprietaires, prestataires)
- Use `TiersBien` model to link tiers to properties with contract details
- Check `tiers.has_user_account` before assuming user login exists
- Supports `type_tiers='coproprietaire'` for co-ownership management (syndic module)

### apps.properties
- Two main models: `Residence` and `Appartement`
- Legacy `Property` model exists but is deprecated
- Use `Appartement.statut` to track availability: 'libre', 'occupé', 'maintenance', 'réservé'
- `Residence.type_gestion` determines if it's rental management ('location'), co-ownership syndic ('syndic'), or both ('mixte')

### apps.contracts
- `RentalContract` is the core rental agreement model
- Auto-generates `numero_contrat` via `generate_unique_reference()`
- Financial fields: `loyer_mensuel`, `charges_mensuelles`, `depot_garantie`, `frais_agence`

### apps.payments
- `Invoice` and `Payment` models handle billing
- Invoice types determine processing logic

### apps.syndic (NEW)
- **Completely separate** from rental management (gestion locative)
- Manages co-ownerships where Imany acts as syndic (property manager for common areas)
- Key models: `Copropriete`, `Coproprietaire`, `CotisationSyndic`, `BudgetPrevisionnel`
- Uses tantièmes (ownership shares) to calculate quarterly contributions
- Automated cotisation generation via management command
- See [apps/syndic/README.md](apps/syndic/README.md) for detailed documentation

**Key differences from rental management:**
| Aspect | Rental Management | Syndic |
|--------|------------------|--------|
| Entity | Appartement (rental unit) | Copropriété (co-ownership) |
| Relationship | Owner → Tenant | Syndic → Co-owners |
| Payment | Monthly rent | Quarterly contributions |
| Calculation | Fixed amount per unit | Share-based (tantièmes) |
| Document | Rental contract | Annual budget |
- Payment methods: 'cash', 'orange_money', 'wave', 'virement', 'cheque'

### apps.notifications
- Multi-channel: SMS (Twilio), WhatsApp, Email, in-app
- Template system with French/Wolof support
- Automatic triggers for payments, contracts, maintenance

### apps.portals
- Separate portal views for tenants (`/tenant/`) and landlords (`/landlord/`)
- Authenticated access with role-based permissions
- Dashboard shows relevant data per user type

## Database Considerations

### Indexes
Key models have composite indexes for performance:
- `Tiers`: `(type_tiers, statut)`, `(nom, prenom)`
- `RentalContract`: `(statut, date_fin)`
- `Invoice`: `(statut, date_echeance)`

### Cascade Behavior
- Most foreign keys use `CASCADE` - deleting a residence deletes its apartments
- Financial records use `SET_NULL` or `PROTECT` to prevent data loss
- User deletion sets `SET_NULL` on `created_by`/`modified_by` tracking fields

## Deployment & Production

### Railway Configuration
- Auto-deploys from git push
- Health check: `/health/`
- Start command: `gunicorn seyni_properties.wsgi:application`
- Cron jobs defined in `railway.json`

### Static Files
- Collected via WhiteNoise (no separate CDN)
- Run `python manage.py collectstatic` before deploy
- Static files served from `/static/`, media from `/media/`

### Migrations in Production
Railway runs migrations automatically via `start.sh` script on deploy.

## Known Issues & Warnings

1. **Tiers Migration Incomplete**: Legacy `landlords`/`tenants` apps still installed but should not be used
2. **Empty Tests**: Test files exist but most have no actual test cases
3. **Security Config**: `settings.py` has development defaults (DEBUG=True, ALLOWED_HOSTS=['*']) - override with env vars in production
4. **Hard-coded Credentials**: Email settings have placeholder values - must set via environment variables

## When Modifying Code

### Before Adding Features
- Check if it affects Tiers architecture - ensure compatibility
- Verify you're not using deprecated `Bailleur`/`Locataire` models
- Add database indexes for new frequently-queried fields

### Template Changes
- Run `python analyze_templates.py` after modifying templates
- Ensure you're using `tiers.nom_complet` not `user.get_full_name()`
- Test with users who have no associated user account

### Model Changes
- Always inherit from `TimestampedModel` or `BaseModel` for audit trails
- Use `generate_unique_reference()` for entity references
- Add appropriate `related_name` to foreign keys
- Include `help_text` for business-critical fields

### Adding Management Commands
- Place in `apps/<app_name>/management/commands/`
- Update `railway.json` if it should run on a schedule
- Handle both development (SQLite) and production (PostgreSQL) databases
