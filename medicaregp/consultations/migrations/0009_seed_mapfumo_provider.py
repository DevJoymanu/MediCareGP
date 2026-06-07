from django.db import migrations


def seed_provider(apps, schema_editor):
    Provider = apps.get_model('consultations', 'Provider')
    Provider.objects.get_or_create(
        name='Dr. Mapfumo & Partners Inc.',
        defaults={
            'kind':        'radiology',
            'practice_no': '0605530',
            'email':       'eastrandis@gmail.com',
            'phone':       '011 732 1022',
            'address':     ('No. 4590 Malandela / Sotho Street, Tsakane | '
                            '4 Cloverdene Road, Van Ryn Street, Benoni, 1513 | '
                            'Room 22A Shaguma Complex, 86 Whisken Avenue, Crowthorne, Midrand'),
            'is_active':   True,
        },
    )


def unseed_provider(apps, schema_editor):
    Provider = apps.get_model('consultations', 'Provider')
    Provider.objects.filter(name='Dr. Mapfumo & Partners Inc.').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('consultations', '0008_provider_investigationrequest'),
    ]

    operations = [
        migrations.RunPython(seed_provider, unseed_provider),
    ]
