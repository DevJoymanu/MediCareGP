from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_appointment_visit_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[
                    ('Scheduled',  'Scheduled'),
                    ('Checked In', 'Checked In'),
                    ('Completed',  'Completed'),
                    ('Cancelled',  'Cancelled'),
                    ('No-Show',    'No-Show'),
                ],
                default='Scheduled',
                max_length=20,
            ),
        ),
    ]
