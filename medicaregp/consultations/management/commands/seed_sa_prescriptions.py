"""
Management command: seed_sa_prescriptions

Populates ConditionPrescriptionLink with evidence-based South African
Standard Treatment Guidelines (STGs, 8th Edition 2024) data.

Run once:  python manage.py seed_sa_prescriptions
Re-run safe: skips entries that already exist.
"""

from django.core.management.base import BaseCommand
from consultations.models import ConditionPrescriptionLink


# ── SA STG seed data ──────────────────────────────────────────────────────────
# Format: (condition, [(prescription_string, starting_count), ...])
# Starting count = 20 gives the guideline data meaningful weight.
# Doctor's real prescriptions (each +1) will overtake a seed after ~20
# consultations with a different preference — the system adapts naturally.

SEED = [

    # ── RESPIRATORY ───────────────────────────────────────────────────────────

    ('URTI', [
        ('Amoxicillin 500mg — 1 three times daily × 5/7',          20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Cetirizine 10mg — 1 daily',                               12),
    ]),

    ('Pharyngitis', [
        ('Amoxicillin 500mg — 1 three times daily × 5/7',          20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     14),
    ]),

    ('Tonsillitis', [
        ('Amoxicillin 500mg — 1 three times daily × 10/7',         20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     14),
    ]),

    ('Acute bronchitis', [
        ('Azithromycin 500mg — 1 daily × 3/7',                     20),
        ('Prednisone 20mg — 1 daily × 5/7',                        18),
        ('Benylin Chesty Coughs — 10ml three times daily',          16),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        14),
        ('Ventolin inhaler — 2 puffs every 4–6 hours PRN',         12),
    ]),

    ('Sinusitis', [
        ('Augmentin 875/125mg — 1 twice daily × 7/7',              20),
        ('Amoxicillin 500mg — 1 three times daily × 7/7',          16),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        14),
        ('Beconase nasal spray — 2 sprays each nostril twice daily', 14),
        ('Cetirizine 10mg — 1 daily',                               10),
    ]),

    ('Allergic rhinitis', [
        ('Cetirizine 10mg — 1 daily',                               20),
        ('Loratadine 10mg — 1 daily',                               18),
        ('Beconase nasal spray — 2 sprays each nostril twice daily', 16),
    ]),

    ('Pneumonia', [
        ('Amoxicillin 500mg — 1 three times daily × 7/7',          20),
        ('Azithromycin 500mg — 1 daily × 5/7',                     18),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        14),
    ]),

    ('Asthma exacerbation', [
        ('Ventolin inhaler — 2 puffs every 4–6 hours PRN',         20),
        ('Prednisone 20mg — 1 daily × 5/7',                        20),
        ('Atrovent inhaler — 2 puffs three times daily',           12),
    ]),

    ('COPD exacerbation', [
        ('Prednisone 20mg — 1 daily × 5/7',                        20),
        ('Amoxicillin 500mg — 1 three times daily × 5/7',          18),
        ('Ventolin inhaler — 2 puffs every 4–6 hours PRN',         18),
        ('Atrovent inhaler — 2 puffs three times daily',           16),
    ]),

    # ── CARDIOVASCULAR ────────────────────────────────────────────────────────

    ('Hypertension', [
        ('Amlodipine 5mg — 1 daily',                                20),
        ('Hydrochlorothiazide 25mg — 1 daily',                      18),
        ('Enalapril 5mg — 1 daily',                                 16),
        ('Amlodipine 10mg — 1 daily',                               14),
        ('Enalapril 10mg — 1 daily',                                12),
    ]),

    ('Hypertensive urgency', [
        ('Amlodipine 10mg — 1 daily',                               20),
        ('Enalapril 10mg — 1 daily',                                18),
        ('Hydrochlorothiazide 25mg — 1 daily',                      16),
    ]),

    ('Heart failure', [
        ('Enalapril 2.5mg — 1 twice daily (titrate to 10mg BD)',    20),
        ('Furosemide 40mg — 1 daily',                               20),
        ('Atorvastatin 20mg — 1 at night',                          14),
    ]),

    # ── ENDOCRINE ─────────────────────────────────────────────────────────────

    ('Type 2 Diabetes mellitus', [
        ('Metformin 500mg — 1 twice daily with meals',              20),
        ('Metformin 850mg — 1 twice daily with meals',              16),
        ('Metformin 1000mg — 1 twice daily with meals',             12),
    ]),

    ('Hypothyroidism', [
        ('Levothyroxine 50mcg — 1 daily on empty stomach',          20),
        ('Levothyroxine 100mcg — 1 daily on empty stomach',         16),
        ('Levothyroxine 25mcg — 1 daily on empty stomach',          12),
    ]),

    ('Hyperthyroidism', [
        ('Refer to endocrinology',                                   20),
        ('Propranolol 40mg — 1 twice daily (symptom control)',      16),
    ]),

    # ── INFECTIONS ────────────────────────────────────────────────────────────

    ('UTI', [
        ('Ciprofloxacin 500mg — 1 twice daily × 5/7',              20),
        ('Nitrofurantoin 100mg — 1 twice daily × 5/7',             18),
        ('Amoxicillin-clavulanate 875/125mg — 1 twice daily × 3/7', 14),
    ]),

    ('Skin infection / Cellulitis', [
        ('Cephalexin 500mg — 1 four times daily × 7/7',            20),
        ('Amoxicillin-clavulanate 875/125mg — 1 twice daily × 7/7', 16),
        ('Flucloxacillin 500mg — 1 four times daily × 7/7',        14),
    ]),

    ('Impetigo', [
        ('Cephalexin 250mg — 1 four times daily × 5/7',            20),
        ('Mupirocin 2% ointment — apply three times daily × 5/7',  16),
    ]),

    ('Conjunctivitis', [
        ('Chloramphenicol 1% eye ointment — apply every 6 hours × 7/7', 20),
        ('Sodium chloride 0.9% — irrigate eye as needed',           14),
    ]),

    ('Otitis media', [
        ('Amoxicillin 500mg — 1 three times daily × 5/7',          20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     14),
    ]),

    ('Gonorrhea', [
        ('Ceftriaxone 500mg IM — single dose',                      20),
        ('Azithromycin 1g — single dose',                           20),
    ]),

    ('Chlamydia', [
        ('Azithromycin 1g — single dose',                           20),
        ('Doxycycline 100mg — 1 twice daily × 7/7',                18),
    ]),

    ('Trichomoniasis', [
        ('Metronidazole 2g — single oral dose',                     20),
        ('Tinidazole 2g — single oral dose',                        16),
    ]),

    ('Vaginal candidiasis', [
        ('Fluconazole 150mg — single oral dose',                    20),
        ('Clotrimazole pessary 500mg — single dose intravaginally', 16),
    ]),

    # ── GASTROINTESTINAL ──────────────────────────────────────────────────────

    ('GERD', [
        ('Omeprazole 20mg — 1 daily before breakfast',              20),
        ('Lansoprazole 30mg — 1 daily before breakfast',            16),
        ('Gaviscon — 10–20ml after meals and at bedtime',           14),
    ]),

    ('Peptic ulcer disease', [
        ('Omeprazole 40mg — 1 daily before breakfast',              20),
        ('Amoxicillin 1g — 1 twice daily × 7/7 (H. pylori triple therapy)', 16),
        ('Clarithromycin 500mg — 1 twice daily × 7/7 (H. pylori triple therapy)', 16),
    ]),

    ('Acute gastroenteritis', [
        ('Oral rehydration solution — as directed for rehydration', 20),
        ('Loperamide 2mg — 2 initially then 1 after each loose stool (max 8/day)', 16),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        14),
        ('Metronidazole 400mg — 1 three times daily × 5/7',        12),
    ]),

    ('Constipation', [
        ('Lactulose 10–20ml — once daily, increase to twice daily if needed', 20),
        ('Movicol — 1 sachet in 125ml water once to twice daily',  16),
    ]),

    ('Irritable bowel syndrome', [
        ('Buscopan 10mg — 1–2 three times daily PRN',               20),
        ('Lactulose 10ml — once daily',                              14),
        ('Mebeverine 135mg — 1 three times daily before meals',     14),
    ]),

    # ── MENTAL HEALTH ─────────────────────────────────────────────────────────

    ('Depression', [
        ('Fluoxetine 20mg — 1 daily in the morning',                20),
        ('Sertraline 50mg — 1 daily',                               18),
        ('Escitalopram 10mg — 1 daily',                             14),
    ]),

    ('Anxiety disorder', [
        ('Fluoxetine 20mg — 1 daily in the morning',                20),
        ('Sertraline 50mg — 1 daily',                               18),
        ('Escitalopram 10mg — 1 daily',                             16),
    ]),

    ('Insomnia', [
        ('Diazepam 5mg — 1 at bedtime (max 2 weeks)',               20),
        ('Promethazine 25mg — 1 at night PRN',                      16),
    ]),

    ('Stress reaction', [
        ('Fluoxetine 20mg — 1 daily in the morning',                16),
        ('Diazepam 5mg — 1 at night PRN (short-term only)',         14),
    ]),

    # ── MUSCULOSKELETAL ───────────────────────────────────────────────────────

    ('Acute lower back pain', [
        ('Ibuprofen 400mg — 1 three times daily with food',         20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Voltaren 50mg — 1 twice daily with food',                 16),
        ('Diazepam 5mg — 1 at night (muscle spasm, max 5 days)',    10),
    ]),

    ('Osteoarthritis', [
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Voltaren gel — apply to affected area three times daily',  14),
        ('Omeprazole 20mg — 1 daily (gastric protection with NSAID)', 12),
    ]),

    ('Gout', [
        ('Indomethacin 50mg — 1 three times daily with food × 3/7', 20),
        ('Colchicine 500mcg — 1 twice daily until relief (max 6mg per course)', 18),
        ('Allopurinol 100mg — 1 daily (start after acute attack settles)', 16),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     14),
    ]),

    ('Muscle strain', [
        ('Ibuprofen 400mg — 1 three times daily with food × 5/7',  20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        18),
        ('Voltaren gel — apply to affected area three times daily',  14),
    ]),

    ('Migraine', [
        ('Sumatriptan 50mg — 1 at onset, repeat after 2h if needed (max 200mg/day)', 20),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     18),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        16),
        ('Metoclopramide 10mg — 1 three times daily (nausea)',      14),
    ]),

    # ── DERMATOLOGY ───────────────────────────────────────────────────────────

    ('Eczema', [
        ('Hydrocortisone 1% cream — apply twice daily until improved', 20),
        ('Betamethasone 0.1% cream — apply twice daily',            16),
        ('Cetirizine 10mg — 1 daily (itch)',                        14),
        ('Chlorphenamine 4mg — 1 at night (night itch, max 2 weeks)', 12),
        ('Aqueous cream — apply as moisturiser liberally',          12),
    ]),

    ('Fungal skin infection', [
        ('Clotrimazole 1% cream — apply twice daily × 4 weeks',    20),
        ('Fluconazole 150mg — once weekly × 4–6 weeks (systemic)',  16),
        ('Terbinafine 1% cream — apply once daily × 2 weeks',      14),
    ]),

    ('Acne', [
        ('Doxycycline 100mg — 1 daily × minimum 2 months',         20),
        ('Erythromycin 500mg — 1 twice daily × minimum 2 months',  16),
        ('Benzoyl peroxide 5% gel — apply once daily',             14),
        ('Tretinoin 0.025% cream — apply at night',                 12),
    ]),

    ('Urticaria', [
        ('Cetirizine 10mg — 1 daily',                               20),
        ('Loratadine 10mg — 1 daily',                               18),
        ('Chlorphenamine 4mg — 1 every 6 hours PRN',                14),
        ('Prednisone 20mg — 1 daily × 3/7 (severe)',               12),
    ]),

    ('Scabies', [
        ('Permethrin 5% cream — apply from neck down overnight, wash off after 8–14h; repeat in 7 days', 20),
        ('Benzyl benzoate 25% lotion — apply twice, 24h apart',    16),
    ]),

    # ── ANAEMIA / NUTRITION ───────────────────────────────────────────────────

    ('Iron deficiency anaemia', [
        ('Ferrous sulphate 200mg — 1 three times daily with meals', 20),
        ('Ferrous fumarate 200mg — 1 three times daily',            16),
        ('Folic acid 5mg — 1 daily',                                14),
    ]),

    ('Folic acid deficiency', [
        ('Folic acid 5mg — 1 daily until haemoglobin normalises',   20),
    ]),

    ('Vitamin B12 deficiency', [
        ('Vitamin B12 (cyanocobalamin) 1mg IM — every 2 months for life', 20),
        ('Vitamin B12 1000mcg oral — 1 daily',                      14),
    ]),

    ('Vitamin D deficiency', [
        ('Cholecalciferol 50 000 IU — 1 weekly × 8 weeks, then monthly', 20),
        ('Cholecalciferol 1000 IU — 1 daily (maintenance)',         16),
    ]),

    # ── PAIN MANAGEMENT ───────────────────────────────────────────────────────

    ('Acute pain', [
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        20),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     18),
        ('Tramadol 50mg — 1–2 every 6 hours PRN (max 400mg/day)',   12),
    ]),

    ('Chronic pain', [
        ('Tramadol 50mg — 1–2 every 6 hours PRN (max 400mg/day)',   20),
        ('Ibuprofen 400mg — 1 three times daily with food',         18),
        ('Amitriptyline 10–25mg — 1 at night (neuropathic)',        14),
    ]),

    ('Headache', [
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        20),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     18),
    ]),

    # ── PAEDIATRIC ────────────────────────────────────────────────────────────

    ('Deworming', [
        ('Mebendazole 500mg — single dose (>2 years)',              20),
        ('Albendazole 400mg — single dose (>2 years)',              18),
    ]),

    ('Paediatric fever', [
        ('Paracetamol 10–15mg/kg — every 6 hours PRN',             20),
        ('Ibuprofen 5–10mg/kg — every 6–8 hours with food PRN',    16),
    ]),

    ('Paediatric URTI', [
        ('Amoxicillin 90mg/kg/day — divided three times daily × 5/7', 20),
        ('Paracetamol 10–15mg/kg — every 6 hours PRN',             18),
    ]),

    # ── GENERAL / COMMON ──────────────────────────────────────────────────────

    ('Dehydration', [
        ('Oral rehydration solution — 200–400ml after each loose stool', 20),
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        14),
    ]),

    ('Allergic reaction', [
        ('Cetirizine 10mg — 1 daily',                               20),
        ('Chlorphenamine 4mg — 1 every 6 hours PRN',                18),
        ('Prednisone 20mg — 1 daily × 3/7 (moderate reaction)',     14),
    ]),

    ('Viral illness', [
        ('Paracetamol 500mg — 2 tablets every 6 hours PRN',        20),
        ('Ibuprofen 400mg — 1 three times daily with food PRN',     16),
        ('Cetirizine 10mg — 1 daily (if symptomatic rhinitis)',     10),
    ]),

]


class Command(BaseCommand):
    help = 'Seed ConditionPrescriptionLink with SA Standard Treatment Guideline data'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for condition, prescriptions in SEED:
            for prescription, count in prescriptions:
                obj, was_created = ConditionPrescriptionLink.objects.get_or_create(
                    condition=condition,
                    prescription=prescription,
                    defaults={'count': count, 'is_seeded': True},
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done — {created} entries created, {skipped} already existed.'
        ))
