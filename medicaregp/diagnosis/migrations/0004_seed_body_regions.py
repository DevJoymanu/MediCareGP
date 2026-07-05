"""Assign body-map regions to the seeded symptoms.

Anything not in the map (including future admin-added symptoms) keeps the
'general' default. Reverse is a no-op — the field default covers it.
"""
from django.db import migrations

REGION_MAP = {
    'head': [
        'Headache', 'Band-like head pressure', 'Unilateral throbbing headache',
        'Facial pain', 'Photophobia', 'Visual aura', 'Visual disturbance',
        'Blurred vision', 'Red eye', 'Itchy eyes', 'Eye discharge',
        'Ear pain', 'Ear discharge', 'Reduced hearing',
        'Runny nose', 'Nasal congestion', 'Sneezing',
        'Dizziness', 'Confusion', 'Blackout / loss of consciousness', 'Seizure',
    ],
    'throat': [
        'Sore throat', 'Difficulty swallowing', 'Neck pain', 'Neck stiffness',
        'Swollen lymph nodes',
    ],
    'chest': [
        'Chest pain', 'Chest tightness', 'Crushing chest pain',
        'Exertional chest pain', 'Pain radiating to arm / jaw', 'Palpitations',
        'Shortness of breath', 'Orthopnoea', 'Cough', 'Productive cough',
        'Chronic cough (>2 weeks)', 'Night-time cough', 'Coughing up blood',
        'Wheeze',
    ],
    'abdomen': [
        'Abdominal pain', 'Epigastric pain', 'Right lower abdominal pain',
        'Bloating', 'Nausea', 'Vomiting', 'Diarrhoea', 'Constipation',
        'Blood in stool', 'Heartburn', 'Regurgitation',
        'Loss of appetite', 'Appetite change',
    ],
    'pelvis': [
        'Dysuria', 'Urinary frequency', 'Urinary urgency', 'Frequent urination',
        'Blood in urine', 'Suprapubic pain', 'Pelvic pain', 'Flank pain',
        'Painful periods', 'Pain during intercourse',
        'Vaginal discharge', 'Vaginal itching',
    ],
    'limbs': [
        'Joint pain', 'Joint stiffness', 'Joint swelling', 'Joint redness',
        'Big toe pain', 'Calf pain', 'Calf swelling', 'Leg swelling',
        'Leg redness', 'Low back pain', 'Muscle aches', 'Tremor',
    ],
    'skin': [
        'Rash', 'Itching', 'Itching worse at night', 'Household contacts itching',
        'Dry skin', 'Wheals / hives', 'Skin redness', 'Skin swelling',
        'Skin warmth / tenderness', 'Pallor',
    ],
    'mental': [
        'Low mood', 'Loss of interest', 'Anxiety / excessive worry',
        'Poor sleep', 'Poor concentration',
    ],
    # everything else stays 'general' (Fever, Fatigue, Night sweats, Weight
    # loss/gain, Chills, Sweating, thirst, intolerances, BP reading, travel…)
}


def apply_regions(apps, schema_editor):
    Symptom = apps.get_model('diagnosis', 'Symptom')
    for region, names in REGION_MAP.items():
        Symptom.objects.filter(name__in=names).update(body_region=region)


class Migration(migrations.Migration):

    dependencies = [
        ('diagnosis', '0003_differentialresult_confirmed_at_and_more'),
    ]

    operations = [
        migrations.RunPython(apply_regions, migrations.RunPython.noop),
    ]
