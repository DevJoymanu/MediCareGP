import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_payment_claimsubmission'),
        ('consultations', '0007_alter_consultation_icd10_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='consultation',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoices',
                to='consultations.consultation',
                verbose_name='Linked consultation',
            ),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='icd10_code',
            field=models.TextField(blank=True, null=True, verbose_name='ICD-10 code(s)'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='line_type',
            field=models.CharField(
                choices=[
                    ('Procedure',  'Procedure'),
                    ('Modifier',   'Modifier'),
                    ('Medicine',   'Medicine'),
                    ('Consumable', 'Consumable'),
                ],
                default='Procedure',
                max_length=20,
                verbose_name='Line type',
            ),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='nappi_code',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='NAPPI code'),
        ),
    ]
