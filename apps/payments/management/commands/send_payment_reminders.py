# apps/payments/management/commands/send_payment_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.payments.models.invoice import Invoice


class Command(BaseCommand):
    help = 'Envoie des rappels de paiement pour les factures à venir et en retard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=3,
            help='Nombre de jours avant échéance pour envoyer un rappel'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler sans envoyer les notifications'
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        dry_run = options['dry_run']
        today = timezone.now().date()
        reminder_date = today + timedelta(days=days_before)

        # Factures à venir (rappel préventif)
        upcoming_invoices = Invoice.objects.filter(
            statut='impaye',
            date_echeance=reminder_date
        ).select_related('locataire', 'appartement')

        # Factures en retard (rappel urgent)
        overdue_invoices = Invoice.objects.filter(
            statut='impaye',
            date_echeance__lt=today
        ).select_related('locataire', 'appartement')

        sent_count = 0

        # Rappels préventifs
        for invoice in upcoming_invoices:
            if invoice.locataire:
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[DRY-RUN] Rappel pour facture {invoice.reference} '
                            f'(échéance dans {days_before} jours) - {invoice.locataire.nom_complet if hasattr(invoice.locataire, "nom_complet") else "Locataire"}'
                        )
                    )
                    sent_count += 1
                else:
                    try:
                        # TODO: Implémenter l'envoi réel via TwilioService ou email
                        # from apps.notifications.models import Notification
                        # Notification.objects.create(...)
                        self.stdout.write(
                            self.style.WARNING(
                                f'Rappel à envoyer pour facture {invoice.reference} '
                                f'(échéance dans {days_before} jours) - Non implémenté'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Erreur rappel {invoice.reference}: {str(e)}'
                            )
                        )

        # Rappels urgents
        for invoice in overdue_invoices:
            if invoice.locataire:
                days_overdue = (today - invoice.date_echeance).days
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[DRY-RUN] Rappel URGENT pour facture {invoice.reference} '
                            f'(en retard de {days_overdue} jours) - {invoice.locataire.nom_complet if hasattr(invoice.locataire, "nom_complet") else "Locataire"}'
                        )
                    )
                    sent_count += 1
                else:
                    try:
                        # TODO: Implémenter l'envoi réel via TwilioService ou email
                        self.stdout.write(
                            self.style.WARNING(
                                f'Rappel URGENT à envoyer pour facture {invoice.reference} '
                                f'(en retard de {days_overdue} jours) - Non implémenté'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Erreur rappel urgent {invoice.reference}: {str(e)}'
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal: {sent_count if dry_run else 0} rappels {"simulés" if dry_run else "à implémenter"} '
                f'({upcoming_invoices.count()} préventifs, {overdue_invoices.count()} urgents)'
            )
        )
