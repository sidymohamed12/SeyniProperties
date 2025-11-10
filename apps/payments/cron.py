# apps/payments/cron.py
from django_cron import CronJobBase, Schedule

class GenerateMonthlyInvoicesCronJob(CronJobBase):
    RUN_EVERY_MINS = 43200  # 30 jours
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'payments.generate_monthly_invoices'
    
    def do(self):
        from django.core.management import call_command
        call_command('generate_monthly_invoices')