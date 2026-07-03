# Data migration: seed a starter tariff catalogue (medical + surgical) with
# rates effective 2026-01-01. Rates are versioned: to change a price, ADD a
# new TariffRate with a later effective_from — never edit an old row.
from datetime import date
from decimal import Decimal

from django.db import migrations

TARIFFS = [
    # (code, description, category, rate)
    ('0190', 'Consultation — surgery hours',                    'Medical',  Decimal('550.00')),
    ('0191', 'Consultation — after hours',                      'Medical',  Decimal('750.00')),
    ('0192', 'Consultation — home visit',                       'Medical',  Decimal('900.00')),
    ('0199', 'Follow-up / repeat consultation',                 'Medical',  Decimal('400.00')),
    ('0202', 'Chronic medication review',                       'Medical',  Decimal('350.00')),
    ('1206', 'ECG with interpretation',                         'Medical',  Decimal('450.00')),
    ('0221', 'Suturing of wound (small, < 5 cm)',               'Surgical', Decimal('650.00')),
    ('0223', 'Incision and drainage of abscess',                'Surgical', Decimal('700.00')),
    ('0228', 'Excision of skin lesion',                         'Surgical', Decimal('850.00')),
    ('0238', 'Removal of foreign body (skin / subcutaneous)',   'Surgical', Decimal('600.00')),
    ('2101', 'Circumcision',                                    'Surgical', Decimal('1500.00')),
]

EFFECTIVE = date(2026, 1, 1)


def seed(apps, schema_editor):
    TariffCode = apps.get_model('billing', 'TariffCode')
    TariffRate = apps.get_model('billing', 'TariffRate')
    for code, description, category, rate in TARIFFS:
        tariff, _ = TariffCode.objects.get_or_create(
            code=code, defaults={'description': description, 'category': category})
        TariffRate.objects.get_or_create(
            tariff=tariff, effective_from=EFFECTIVE, defaults={'amount': rate})


def unseed(apps, schema_editor):
    TariffCode = apps.get_model('billing', 'TariffCode')
    TariffCode.objects.filter(code__in=[t[0] for t in TARIFFS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0006_tariffcode_invoiceitem_category_invoiceitem_tariff_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
