from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0002_appointment_authorization_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='visit_type',
            field=models.CharField(
                choices=[('Scheduled', 'Scheduled'), ('Walk-In', 'Walk-In')],
                default='Scheduled',
                max_length=20,
            ),
        ),
    ]
