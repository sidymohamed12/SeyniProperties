"""
Commande de génération automatique des cotisations syndic.
À exécuter selon la périodicité définie (trimestriel, mensuel, etc.)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.syndic.models import Copropriete, CotisationSyndic
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Génère les cotisations syndic pour la période spécifiée'

    def add_arguments(self, parser):
        parser.add_argument(
            '--annee',
            type=int,
            help='Année de génération (ex: 2025)',
        )
        parser.add_argument(
            '--periode',
            type=str,
            help='Période à générer (ex: Q1, Q2, M01, M02, etc.)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation sans créer de cotisations',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la génération même si des cotisations existent déjà',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        annee = options.get('annee')
        periode = options.get('periode')

        # Si pas d'année/période spécifiée, utiliser la période courante
        if not annee or not periode:
            annee, periode = self.get_current_period()
            self.stdout.write(
                self.style.WARNING(
                    f'Aucune période spécifiée, utilisation de la période courante: {annee}-{periode}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"[SIMULATION] " if dry_run else ""}Génération des cotisations syndic pour {annee}-{periode}'
            )
        )
        self.stdout.write('=' * 80)

        # Récupérer toutes les copropriétés actives
        coproprietes = Copropriete.objects.filter(is_active=True)

        if not coproprietes.exists():
            self.stdout.write(
                self.style.WARNING('Aucune copropriété active trouvée.')
            )
            return

        total_cotisations = 0
        total_montant = Decimal('0.00')
        errors = []

        for copropriete in coproprietes:
            # Vérifier si la copropriété doit avoir des cotisations pour cette période
            if not self.should_generate_for_period(copropriete, periode):
                self.stdout.write(
                    self.style.WARNING(
                        f'  Copropriété {copropriete.residence.nom}: '
                        f'pas de génération pour cette période ({copropriete.periode_cotisation})'
                    )
                )
                continue

            self.stdout.write(f'\n• Copropriété: {copropriete.residence.nom}')
            self.stdout.write(f'  Budget annuel: {copropriete.budget_annuel:,.0f} FCFA')
            self.stdout.write(f'  Périodicité: {copropriete.get_periode_cotisation_display()}')

            # Générer les cotisations pour chaque copropriétaire
            coproprietaires = copropriete.coproprietaires.filter(is_active=True)

            if not coproprietaires.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'  Aucun copropriétaire actif pour cette copropriété.'
                    )
                )
                continue

            for copro in coproprietaires:
                try:
                    # Vérifier si la cotisation existe déjà
                    existing = CotisationSyndic.objects.filter(
                        coproprietaire=copro,
                        periode=periode,
                        annee=annee
                    ).exists()

                    if existing and not force:
                        self.stdout.write(
                            self.style.WARNING(
                                f'    ⚠ {copro.tiers.nom_complet}: cotisation déjà existante (utiliser --force pour régénérer)'
                            )
                        )
                        continue

                    # Calculer le montant
                    montant = copro.cotisation_par_periode

                    # Déterminer les dates
                    date_emission = timezone.now().date()
                    date_echeance = self.get_date_echeance(annee, periode)

                    if not dry_run:
                        # Créer ou mettre à jour la cotisation
                        with transaction.atomic():
                            if existing:
                                cotisation = CotisationSyndic.objects.get(
                                    coproprietaire=copro,
                                    periode=periode,
                                    annee=annee
                                )
                                cotisation.montant_theorique = montant
                                cotisation.date_emission = date_emission
                                cotisation.date_echeance = date_echeance
                                cotisation.save()
                                action = '🔄 Mise à jour'
                            else:
                                cotisation = CotisationSyndic.objects.create(
                                    coproprietaire=copro,
                                    periode=periode,
                                    annee=annee,
                                    montant_theorique=montant,
                                    date_emission=date_emission,
                                    date_echeance=date_echeance,
                                    statut='en_cours'
                                )
                                action = '✓ Créée'

                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'    {action}: {copro.tiers.nom_complet} - '
                                    f'{montant:,.0f} FCFA ({copro.quote_part:.2f}%)'
                                )
                            )
                    else:
                        self.stdout.write(
                            f'    [SIMULATION] {copro.tiers.nom_complet} - '
                            f'{montant:,.0f} FCFA ({copro.quote_part:.2f}%)'
                        )

                    total_cotisations += 1
                    total_montant += montant

                except Exception as e:
                    error_msg = f'Erreur pour {copro.tiers.nom_complet}: {str(e)}'
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(f'    ✗ {error_msg}'))
                    logger.error(error_msg, exc_info=True)

        # Résumé
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"[SIMULATION] " if dry_run else ""}Résumé de la génération:'
            )
        )
        self.stdout.write(f'  Période: {annee}-{periode}')
        self.stdout.write(f'  Copropriétés traitées: {coproprietes.count()}')
        self.stdout.write(f'  Cotisations {"à créer" if dry_run else "créées"}: {total_cotisations}')
        self.stdout.write(f'  Montant total: {total_montant:,.0f} FCFA')

        if errors:
            self.stdout.write(self.style.ERROR(f'\n  ⚠ Erreurs: {len(errors)}'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'    - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n  ✓ Aucune erreur'))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n💡 Mode simulation actif. Utilisez sans --dry-run pour créer les cotisations.'
                )
            )

    def get_current_period(self):
        """Détermine la période courante selon le mois actuel."""
        now = timezone.now()
        annee = now.year
        mois = now.month

        # Déterminer le trimestre
        if mois <= 3:
            periode = 'Q1'
        elif mois <= 6:
            periode = 'Q2'
        elif mois <= 9:
            periode = 'Q3'
        else:
            periode = 'Q4'

        return annee, periode

    def should_generate_for_period(self, copropriete, periode):
        """Vérifie si la copropriété doit générer des cotisations pour cette période."""
        # Si mensuel, toujours générer
        if copropriete.periode_cotisation == 'mensuel':
            return True

        # Si trimestriel, vérifier que c'est un trimestre (Q1, Q2, Q3, Q4)
        if copropriete.periode_cotisation == 'trimestriel':
            return periode.startswith('Q')

        # Si semestriel, vérifier que c'est S1 ou S2
        if copropriete.periode_cotisation == 'semestriel':
            return periode in ['S1', 'S2']

        # Si annuel, vérifier que c'est A1
        if copropriete.periode_cotisation == 'annuel':
            return periode == 'A1'

        return True

    def get_date_echeance(self, annee, periode):
        """Calcule la date d'échéance selon la période."""
        import datetime

        # Pour les trimestres
        if periode == 'Q1':
            return datetime.date(annee, 3, 31)
        elif periode == 'Q2':
            return datetime.date(annee, 6, 30)
        elif periode == 'Q3':
            return datetime.date(annee, 9, 30)
        elif periode == 'Q4':
            return datetime.date(annee, 12, 31)

        # Pour les semestres
        elif periode == 'S1':
            return datetime.date(annee, 6, 30)
        elif periode == 'S2':
            return datetime.date(annee, 12, 31)

        # Pour l'année
        elif periode == 'A1':
            return datetime.date(annee, 12, 31)

        # Pour les mois (M01, M02, etc.)
        elif periode.startswith('M'):
            mois = int(periode[1:])
            # Dernier jour du mois
            if mois == 12:
                return datetime.date(annee, 12, 31)
            else:
                return datetime.date(annee, mois + 1, 1) - datetime.timedelta(days=1)

        # Par défaut, fin du trimestre courant
        return timezone.now().date() + datetime.timedelta(days=90)
