from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('consultations', '0006_conditionprescriptionlink'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consultation',
            name='icd10_code',
            field=models.TextField(blank=True, null=True, verbose_name='ICD-10 code(s)'),
        ),
    ]
