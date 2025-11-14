# apps/payments/management/commands/check_overdue_invoices.py
"""
Vérifie les factures en retard et met à jour leur statut
Usage: python manage.py check_overdue_invoices
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.payments.models.invoice import Invoice


class Command(BaseCommand):
    help = 'Vérifie et met à jour le statut des factures en retard'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Récupérer les factures émises dont la date d'échéance est dépassée
        overdue_invoices = Invoice.objects.filter(
            statut='emise',
            date_echeance__lt=today
        )
        
        count = overdue_invoices.count()
        
        if count > 0:
            # Mettre à jour le statut
            overdue_invoices.update(statut='en_retard')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {count} facture(s) marquée(s) comme en retard'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ Aucune facture en retard')
            )
        
        return f'{count} factures en retard'