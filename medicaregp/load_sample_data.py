import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicaregp.settings')
django.setup()

from django.utils import timezone
from datetime import date, timedelta, time
from patients.models import Patient, Vitals
from appointments.models import Appointment
from consultations.models import Consultation
from scripts.models import Document
from tasks.models import Task

today = timezone.now().date()

# ── 10 Patients ────────────────────────────────────────────────────────────────
patients_data = [
    dict(first_name='James',   last_name='Thornton',     date_of_birth=date(1978,4,12),  gender='M', id_number='7804125032085', phone='+27 83 445 2910', email='james.thornton@email.com',  address='14 Oak Ave, Cape Town',         medical_aid_name='Discovery Health', medical_aid_number='DH-29481-03', blood_type='O+',  allergies='Penicillin, Sulfa drugs',    chronic_conditions='Hypertension, Type 2 Diabetes'),
    dict(first_name='Amara',   last_name='Osei',          date_of_birth=date(1992,8,23),  gender='F', id_number='9208230148096', phone='+27 72 319 8874', email='amara.osei@gmail.com',        address='7 Palm Court, Sandton',         medical_aid_name='Bonitas',           medical_aid_number='BON-11203',   blood_type='A+',  allergies='Aspirin',                    chronic_conditions='Asthma'),
    dict(first_name='Pieter',  last_name='van der Berg',  date_of_birth=date(1955,11,30), gender='M', id_number='5511305014083', phone='+27 61 882 0043', email='',                            address='32 Church St, Stellenbosch',   medical_aid_name='Medihelp',          medical_aid_number='MED-88122',   blood_type='B-',  allergies='',                           chronic_conditions='COPD, Hypertension, Osteoarthritis'),
    dict(first_name='Lerato',  last_name='Dlamini',       date_of_birth=date(1988,2,14),  gender='F', id_number='8802140832081', phone='+27 79 556 4421', email='lerato.d@outlook.com',        address='55 Maple Rd, Johannesburg',    medical_aid_name='Momentum Health',   medical_aid_number='MOM-44209',   blood_type='AB+', allergies='Latex, NSAIDs',              chronic_conditions='Anxiety, Hypothyroidism'),
    dict(first_name='David',   last_name='Kaplan',        date_of_birth=date(1965,7,9),   gender='M', id_number='6507095012087', phone='+27 84 221 3305', email='david.k@gmail.com',           address='8 Harbour View, Durban',       medical_aid_name='Fedhealth',         medical_aid_number='FED-20391',   blood_type='O-',  allergies='Codeine',                    chronic_conditions='Gout, Hypertension'),
    dict(first_name='Naledi',  last_name='Sithole',       date_of_birth=date(2001,5,17),  gender='F', id_number='0105170294086', phone='+27 68 774 1120', email='naledi.s@gmail.com',          address='22 Jacaranda St, Pretoria',    medical_aid_name='',                  medical_aid_number='',            blood_type='A-',  allergies='',                           chronic_conditions=''),
    dict(first_name='Thabo',   last_name='Nkosi',         date_of_birth=date(1971,3,22),  gender='M', id_number='7103220714080', phone='+27 82 310 0048', email='thabo.n@gmail.com',           address='9 Acacia Rd, Port Elizabeth',  medical_aid_name='Discovery Health',  medical_aid_number='DH-51002-09', blood_type='B+',  allergies='Penicillin',                 chronic_conditions='Type 2 Diabetes, Hypertension'),
    dict(first_name='Chantal', last_name='Fourie',        date_of_birth=date(1983,9,5),   gender='F', id_number='8309050226083', phone='+27 76 889 2231', email='chantal.f@icloud.com',        address='4 Rose St, Bloemfontein',      medical_aid_name='Bonitas',           medical_aid_number='BON-77441',   blood_type='O+',  allergies='',                           chronic_conditions='Migraines'),
    dict(first_name='Sipho',   last_name='Dube',          date_of_birth=date(1980,6,14),  gender='M', id_number='8006145012087', phone='+27 71 334 5512', email='sipho.dube@gmail.com',        address='17 Baobab St, Nelspruit',      medical_aid_name='Discovery Health',  medical_aid_number='DH-63104-11', blood_type='A+',  allergies='Aspirin, Ibuprofen',         chronic_conditions='Epilepsy, Depression'),
    dict(first_name='Fatima',  last_name='Adams',         date_of_birth=date(1995,12,3),  gender='F', id_number='9512030184085', phone='+27 63 220 9945', email='fatima.adams@webmail.co.za',  address='88 Tulip Ave, Cape Town',      medical_aid_name='Medihelp',          medical_aid_number='MED-99034',   blood_type='B+',  allergies='',                           chronic_conditions='Polycystic Ovary Syndrome'),
]

created = []
for pd in patients_data:
    p, new = Patient.objects.get_or_create(id_number=pd['id_number'], defaults=pd)
    if not new:
        for k, v in pd.items():
            setattr(p, k, v)
        p.save()
    created.append(p)
    print(f'  Patient: {p}')

p1,p2,p3,p4,p5,p6,p7,p8,p9,p10 = created

# ── Vitals ──────────────────────────────────────────────────────────────────
vitals_rows = [
    (p1, today-timedelta(days=1),  '158/96', 158, 96,  78, 84.0, 178, 36.6, 98),
    (p1, today-timedelta(days=45), '152/94', 152, 94,  82, 85.0, 178, 36.7, 97),
    (p2, today-timedelta(days=2),  '110/72', 110, 72,  68, 58.0, 164, 36.8, 99),
    (p3, today-timedelta(days=15), '145/90', 145, 90,  88, 71.0, 172, 36.5, 94),
    (p4, today,                    '112/74', 112, 74,  72, 62.0, 168, 36.6, 99),
    (p5, today-timedelta(days=40), '138/84', 138, 84,  80, 88.0, 175, 36.7, 98),
    (p7, today-timedelta(days=6),  '142/88', 142, 88,  84, 91.0, 176, 36.8, 97),
    (p9, today-timedelta(days=3),  '128/82', 128, 82,  76, 78.0, 180, 36.9, 98),
    (p10,today-timedelta(days=10), '118/76', 118, 76,  70, 65.0, 163, 36.5, 99),
]
for (pat, dt, bp, bps, bpd, pulse, wt, ht, temp, o2) in vitals_rows:
    Vitals.objects.get_or_create(patient=pat, date=dt, defaults=dict(
        blood_pressure=bp, bp_systolic=bps, bp_diastolic=bpd,
        pulse=pulse, weight=wt, height=ht, temperature=temp, oxygen_saturation=o2
    ))
print('  Vitals: done')

# ── Appointments ─────────────────────────────────────────────────────────────
appt_rows = [
    (p1,  today,                    time(8,30),  'Blood pressure follow-up',        'Scheduled'),
    (p2,  today,                    time(9,15),  'Asthma review',                   'Scheduled'),
    (p4,  today,                    time(10,0),  'Anxiety medication review',        'Completed'),
    (p3,  today,                    time(11,30), 'COPD management',                 'Scheduled'),
    (p5,  today,                    time(14,0),  'Gout flare-up',                   'No-Show'),
    (p6,  today,                    time(15,30), 'General check-up',                'Scheduled'),
    (p7,  today,                    time(16,0),  'Diabetes review',                 'Scheduled'),
    (p8,  today+timedelta(days=1),  time(9,30),  'Migraine management',             'Scheduled'),
    (p9,  today+timedelta(days=2),  time(10,0),  'Epilepsy medication follow-up',   'Scheduled'),
    (p10, today+timedelta(days=2),  time(11,0),  'PCOS review and hormonal panel',  'Scheduled'),
    (p1,  today-timedelta(days=1),  time(9,0),   'Lab results review',              'Completed'),
    (p2,  today-timedelta(days=2),  time(10,30), 'Vaccination',                     'Completed'),
    (p7,  today-timedelta(days=6),  time(8,0),   'HbA1c results',                   'Completed'),
    (p9,  today-timedelta(days=3),  time(14,0),  'Seizure episode review',          'Completed'),
    (p10, today-timedelta(days=10), time(11,30), 'Routine gynae check',             'Completed'),
]
appts = []
for (pat, dt, t, reason, status) in appt_rows:
    a, _ = Appointment.objects.get_or_create(patient=pat, date=dt, time=t, defaults=dict(reason=reason, status=status))
    appts.append(a)
print(f'  Appointments: {len(appts)} loaded')

# ── Consultations ─────────────────────────────────────────────────────────────
consult_rows = [
    dict(patient=p1, appointment=appts[10], date=today-timedelta(days=1),
         subjective='Persistent morning headaches for one week, rating 6/10. High stress at work, poor sleep.',
         objective='BP 158/96 mmHg. PR 78 bpm. Weight 84 kg. No focal neurological deficit.',
         assessment='Hypertension — inadequately controlled, contributing to tension-type headaches.',
         plan='Increase Amlodipine to 10mg OD. Dietary sodium restriction. Follow-up in 2 weeks.',
         prescriptions='Amlodipine 10mg — 1 tablet daily (morning)\nParacetamol 500mg — 2 tablets 6-hourly PRN',
         follow_up_date=today+timedelta(days=13)),
    dict(patient=p2, appointment=appts[11], date=today-timedelta(days=2),
         subjective='Annual flu vaccine visit. Mild soreness at injection site. Asthma well-controlled.',
         objective='Lungs clear bilaterally. Peak flow 410 L/min (95% predicted). O2 sat 99%.',
         assessment='Well-controlled asthma. Influenza vaccination administered without complications.',
         plan='Continue Seretide 250/25 — 1 puff BD. Annual respiratory review in 6 months.',
         prescriptions='', follow_up_date=None),
    dict(patient=p4, appointment=appts[2], date=today,
         subjective='Improved mood stability past month. Sleep 6-7 hours per night. Appetite normalised.',
         objective='Alert and oriented. Normal affect. BP 112/74. Weight 62 kg. No goitre.',
         assessment='GAD responding well to pharmacological management. Hypothyroidism stable.',
         plan='Continue Escitalopram 20mg OD and Eltroxin 75mcg OD. Referral to psychologist for CBT.',
         prescriptions='Escitalopram 20mg — 1 tablet daily (morning)\nEltroxin 75mcg — 1 tablet daily (30 min before breakfast)',
         follow_up_date=today+timedelta(days=42)),
    dict(patient=p7, appointment=appts[12], date=today-timedelta(days=6),
         subjective='Increased fatigue, thirst and frequent urination past 2 weeks.',
         objective='HbA1c 8.4%. FBG 11.2 mmol/L. BP 142/88. Weight 91 kg. Foot sensation intact.',
         assessment='Type 2 Diabetes — suboptimally controlled. Hypertension requires closer management.',
         plan='Increase Metformin to 1g BD. Add Sitagliptin 100mg OD. Referral to dietitian.',
         prescriptions='Metformin 1000mg — 1 tablet twice daily (with meals)\nSitagliptin 100mg — 1 tablet daily',
         follow_up_date=today+timedelta(days=22)),
    dict(patient=p9, appointment=appts[13], date=today-timedelta(days=3),
         subjective='One breakthrough seizure 5 days ago lasting approximately 90 seconds. Possible sleep deprivation trigger.',
         objective='Neurological exam normal. GCS 15. No post-ictal deficit. Lamotrigine level 8.2 mg/L (therapeutic).',
         assessment='Epilepsy — breakthrough seizure likely triggered by sleep deprivation. Medication therapeutic.',
         plan='Strict sleep hygiene counselling. No driving for 6 months. Repeat EEG in 4 weeks. Neurology referral.',
         prescriptions='Lamotrigine 200mg — 1 tablet twice daily\nClonazepam 0.5mg — PRN rescue (max 1 per week)',
         follow_up_date=today+timedelta(days=14)),
]
for cd in consult_rows:
    Consultation.objects.get_or_create(patient=cd['patient'], date=cd['date'], defaults=cd)
print('  Consultations: done')

# ── Documents ─────────────────────────────────────────────────────────────────
doc_rows = [
    dict(patient=p1, doc_type='Sick Note', category='Administrative',
         content='Patient James Thornton is unfit for work for 3 days due to tension headaches and poorly controlled hypertension.\n\nDr. Sarah Malan\nGeneral Practitioner',
         issued_by='Dr. Sarah Malan'),
    dict(patient=p4, doc_type='Referral Letter', category='Clinical',
         content='Dear Dr. Nkosi,\n\nI am referring Ms. Lerato Dlamini (DOB: 14/02/1988) for CBT for Generalised Anxiety Disorder. She is currently stable on Escitalopram 20mg OD.\n\nKind regards,\nDr. Sarah Malan',
         issued_by='Dr. Sarah Malan'),
    dict(patient=p2, doc_type='Vaccination Record', category='Administrative',
         content='Patient: Amara Osei\nVaccine: Influenza (Vaxigrip Tetra)\nBatch: VGT-2026-04\nSite: Left deltoid\nNo adverse reaction observed.',
         issued_by='Dr. Sarah Malan'),
    dict(patient=p7, doc_type='Referral Letter', category='Clinical',
         content='Dear Registered Dietitian,\n\nPlease see Mr. Thabo Nkosi for nutritional management of Type 2 Diabetes (HbA1c 8.4%). Advise on carbohydrate counting and portion control.\n\nDr. Sarah Malan',
         issued_by='Dr. Sarah Malan'),
    dict(patient=p9, doc_type='Referral Letter', category='Clinical',
         content='Dear Neurologist,\n\nI am referring Mr. Sipho Dube for specialist review following a breakthrough seizure on Lamotrigine 200mg BD. Repeat EEG has been requested.\n\nDr. Sarah Malan',
         issued_by='Dr. Sarah Malan'),
]
for dd in doc_rows:
    Document.objects.get_or_create(patient=dd['patient'], doc_type=dd['doc_type'], defaults=dd)
print('  Documents: done')

# ── Tasks ─────────────────────────────────────────────────────────────────────
task_rows = [
    dict(title='Review spirometry results for Pieter van der Berg', patient=p3,   due_date=today+timedelta(days=2), priority='High',   done=False),
    dict(title='Call Naledi Sithole re: lab results',                patient=p6,   due_date=today+timedelta(days=1), priority='Medium', done=False),
    dict(title='Submit monthly billing report',                      patient=None,  due_date=today+timedelta(days=5), priority='Low',    done=False),
    dict(title='Update CME credits log',                             patient=None,  due_date=today,                   priority='Medium', done=True),
    dict(title='Follow up David Kaplan uric acid levels',           patient=p5,   due_date=today+timedelta(days=3), priority='High',   done=False),
    dict(title='Prepare referral notes for Lerato Dlamini',          patient=p4,   due_date=today+timedelta(days=1), priority='High',   done=False),
    dict(title='Order prescription pads — stock low',                patient=None,  due_date=today+timedelta(days=4), priority='Low',    done=False),
    dict(title='Annual leave form submission',                       patient=None,  due_date=today-timedelta(days=2), priority='Medium', done=True),
    dict(title='Confirm Sipho Dube neurology referral appointment',  patient=p9,   due_date=today+timedelta(days=3), priority='High',   done=False),
    dict(title='Review Fatima Adams PCOS hormone panel results',     patient=p10,  due_date=today+timedelta(days=5), priority='Medium', done=False),
]
for td in task_rows:
    Task.objects.get_or_create(title=td['title'], defaults=td)
print('  Tasks: done')

print()
print('Sample data loaded successfully.')
print(f'  Patients:      {Patient.objects.count()}')
print(f'  Appointments:  {Appointment.objects.count()}')
print(f'  Consultations: {Consultation.objects.count()}')
print(f'  Documents:     {Document.objects.count()}')
print(f'  Tasks:         {Task.objects.count()}')
print(f'  Vitals:        {Vitals.objects.count()}')
