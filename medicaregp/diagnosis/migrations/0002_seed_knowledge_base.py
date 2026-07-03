# Data migration: seed the starter symptom→condition knowledge base from
# diagnosis/seed_data.py. Idempotent (get_or_create throughout); fully
# admin-editable afterwards.
from django.db import migrations


def seed(apps, schema_editor):
    from diagnosis.seed_data import CONDITIONS, SIGNS, SYNONYMS

    Condition = apps.get_model('diagnosis', 'Condition')
    Symptom = apps.get_model('diagnosis', 'Symptom')
    Link = apps.get_model('diagnosis', 'SymptomConditionLink')
    Rule = apps.get_model('diagnosis', 'HistoryModifierRule')

    for name, icd10, symptom_weights, history_rules in CONDITIONS:
        condition, _ = Condition.objects.get_or_create(
            name=name, defaults={'icd10_code': icd10})
        for symptom_name, weight in symptom_weights:
            symptom, _ = Symptom.objects.get_or_create(
                name=symptom_name,
                defaults={
                    'kind': 'sign' if symptom_name in SIGNS else 'symptom',
                    'synonyms': SYNONYMS.get(symptom_name, ''),
                })
            Link.objects.get_or_create(
                symptom=symptom, condition=condition, defaults={'weight': weight})
        for factor, match_value, delta, note in history_rules:
            Rule.objects.get_or_create(
                condition=condition, factor=factor, match_value=match_value,
                defaults={'delta': delta, 'note': note})


def unseed(apps, schema_editor):
    for model in ['HistoryModifierRule', 'SymptomConditionLink', 'Condition', 'Symptom']:
        apps.get_model('diagnosis', model).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
