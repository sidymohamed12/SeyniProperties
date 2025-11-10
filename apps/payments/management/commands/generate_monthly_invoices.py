# apps/payments/management/commands/generate_monthly_invoices.py
"""
Commande Django pour générer automatiquement les factures mensuelles
Usage: python manage.py generate_monthly_invoices
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from decimal import Decimal
import calendar

from apps.contracts.models import RentalContract
from apps.payments.models import Invoice
from apps.core.utils import generate_unique_reference


class Command(BaseCommand):
    help = 'Génère automatiquement les factures mensuelles pour les contrats actifs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            help='Mois pour lequel générer les factures (1-12). Par défaut: mois suivant'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Année pour laquelle générer les factures. Par défaut: année en cours'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler sans créer les factures'
        )

    def handle(self, *args, **options):
        # Déterminer la période
        today = timezone.now().date()
        
        if options['month'] and options['year']:
            month = options['month']
            year = options['year']
        else:
            # Mois suivant par défaut
            next_month = today.replace(day=1) + timedelta(days=32)
            month = next_month.month
            year = next_month.year

        self.stdout.write(
            self.style.SUCCESS(f'\n🔄 Génération des factures pour {month}/{year}\n')
        )

        # Récupérer tous les contrats actifs
        active_contracts = RentalContract.objects.filter(
            statut='actif',
            date_debut__lte=datetime(year, month, 1).date()
        ).select_related(
            'appartement__residence',
            'locataire__user'
        )

        self.stdout.write(f'📋 {active_contracts.count()} contrats actifs trouvés\n')

        # Statistiques
        stats = {
            'created': 0,
            'skipped': 0,
            'errors': 0
        }

        for contract in active_contracts:
            try:
                result = self.generate_invoice_for_contract(
                    contract, month, year, options['dry_run']
                )
                
                if result == 'created':
                    stats['created'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Facture créée pour {contract.locataire.user.get_full_name()} '
                            f'({contract.appartement.nom})'
                        )
                    )
                elif result == 'skipped':
                    stats['skipped'] += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⊘ Facture déjà existante pour {contract.locataire.user.get_full_name()}'
                        )
                    )
                    
            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Erreur pour contrat {contract.numero_contrat}: {str(e)}'
                    )
                )

        # Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n📊 RÉSUMÉ DE LA GÉNÉRATION'))
        self.stdout.write(f'  • Factures créées: {stats["created"]}')
        self.stdout.write(f'  • Déjà existantes: {stats["skipped"]}')
        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'  • Erreurs: {stats["errors"]}'))
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n⚠️  Mode DRY-RUN: Aucune facture n\'a été créée')
            )
        self.stdout.write('='*60 + '\n')

    def generate_invoice_for_contract(self, contract, month, year, dry_run=False):
        """
        Génère une facture pour un contrat donné
        Returns: 'created', 'skipped', or raises exception
        """
        # Calculer les dates de période
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date()

        # Vérifier si une facture existe déjà pour cette période
        existing_invoice = Invoice.objects.filter(
            contrat=contract,
            type_facture='loyer',
            periode_debut=first_day,
            periode_fin=last_day
        ).exists()

        if existing_invoice:
            return 'skipped'

        if dry_run:
            return 'created'  # Simuler la création

        # Calculer les montants
        loyer_mensuel = contract.loyer_mensuel
        charges_mensuelles = contract.charges_mensuelles or Decimal('0.00')
        
        # Montant HT (on considère que le loyer inclut la TVA de 18%)
        taux_tva = Decimal('18.00')
        montant_ht = loyer_mensuel / (1 + (taux_tva / 100))
        montant_ttc = loyer_mensuel

        # Date d'échéance : 5 du mois
        date_echeance = first_day.replace(day=5)

        # Créer la facture avec transaction atomique
        with transaction.atomic():
            invoice = Invoice.objects.create(
                numero_facture=generate_unique_reference('FAC'),
                contrat=contract,
                type_facture='loyer',
                periode_debut=first_day,
                periode_fin=last_day,
                date_emission=timezone.now().date(),
                date_echeance=date_echeance,
                montant_ht=montant_ht,
                taux_tva=taux_tva,
                montant_ttc=montant_ttc,
                statut='emise',
                description=f'Loyer du mois de {first_day.strftime("%B %Y")}'
            )

            # Si des charges existent, créer une facture séparée pour les charges
            if charges_mensuelles > 0:
                montant_ht_charges = charges_mensuelles / (1 + (taux_tva / 100))
                
                Invoice.objects.create(
                    numero_facture=generate_unique_reference('FAC'),
                    contrat=contract,
                    type_facture='charges',
                    periode_debut=first_day,
                    periode_fin=last_day,
                    date_emission=timezone.now().date(),
                    date_echeance=date_echeance,
                    montant_ht=montant_ht_charges,
                    taux_tva=taux_tva,
                    montant_ttc=charges_mensuelles,
                    statut='emise',
                    description=f'Charges du mois de {first_day.strftime("%B %Y")}'
                )

        return 'created'