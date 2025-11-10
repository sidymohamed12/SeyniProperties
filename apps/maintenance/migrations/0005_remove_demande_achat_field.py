# Generated migration for removing demande_achat field from Travail
# Architecture change: Travail 1-to-Many with Invoice (demande_achat)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0004_alter_intervention_technicien_and_more'),
        ('payments', '0003_invoice_banque_cheque_invoice_beneficiaire_cheque_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='travail',
            name='demande_achat',
        ),
    ]
