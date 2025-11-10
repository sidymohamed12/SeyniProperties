# Generated migration for Employee model - mot_de_passe_temporaire field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='mot_de_passe_temporaire',
            field=models.CharField(
                blank=True,
                help_text="Mot de passe temporaire généré lors de la création du compte (sera effacé après première connexion)",
                max_length=50,
                verbose_name='Mot de passe temporaire'
            ),
        ),
    ]
