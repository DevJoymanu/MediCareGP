"""
Starter knowledge base for the provisional-diagnosis engine.

~47 conditions common in SA general practice, each with weighted symptom
links (1–10) and explicit history-modifier rules. Every ICD-10 code below
exists in consultations/icd10_data.py (there is a test asserting this).

This is a SEED, not gospel: the whole knowledge base is admin-editable
(Django admin → Provisional Diagnosis Support) so the doctor can tune
weights, add conditions, and add rules without a redeploy.

Format:
    (name, icd10, [(symptom, weight), ...], [(factor, match, delta, note), ...])
"""

# Symptoms that are observed signs rather than reported symptoms.
SIGNS = {
    'High blood pressure reading', 'Pallor', 'Wheals / hives',
    'Neck stiffness', 'Joint swelling', 'Joint redness', 'Skin redness',
    'Skin swelling', 'Leg swelling', 'Calf swelling', 'Swollen lymph nodes',
}

# A few useful synonym sets (admin-extendable).
SYNONYMS = {
    'Fever': 'pyrexia, high temperature, hot body',
    'Shortness of breath': 'dyspnoea, difficulty breathing',
    'Runny nose': 'rhinorrhoea',
    'Dysuria': 'burning urine, painful urination',
    'Heartburn': 'acid reflux',
    'Low mood': 'sadness, feeling down, depressed mood',
    'Seizure': 'convulsion, fit',
    'Itching': 'pruritus',
    'Diarrhoea': 'loose stools, running stomach',
    'Excessive thirst': 'polydipsia',
    'Frequent urination': 'polyuria',
}

CONDITIONS = [
    ('Common cold (acute URTI)', 'J06.9',
     [('Runny nose', 8), ('Nasal congestion', 8), ('Sneezing', 7), ('Sore throat', 6),
      ('Cough', 5), ('Fever', 3), ('Headache', 3)],
     [('age_band', '0-5', 2, 'Very common in young children')]),

    ('Influenza', 'J11.1',
     [('Fever', 8), ('Muscle aches', 8), ('Fatigue', 6), ('Cough', 6),
      ('Headache', 5), ('Sore throat', 4), ('Runny nose', 3)],
     []),

    ('Acute bronchitis', 'J20.9',
     [('Cough', 9), ('Productive cough', 7), ('Chest tightness', 5), ('Wheeze', 4),
      ('Fever', 3), ('Fatigue', 3)],
     [('smoking', 'Current', 2, 'Smokers are prone to bronchitis')]),

    ('Community-acquired pneumonia', 'J18.9',
     [('Productive cough', 8), ('Fever', 7), ('Shortness of breath', 7),
      ('Chest pain', 6), ('Fatigue', 4)],
     [('age_band', '65-120', 3, 'Elderly at higher risk of pneumonia'),
      ('chronic', 'hiv', 2, 'HIV increases pneumonia risk'),
      ('alcohol', 'Heavy', 1, 'Heavy alcohol use increases risk')]),

    ('Pulmonary tuberculosis', 'A16.9',
     [('Chronic cough (>2 weeks)', 9), ('Night sweats', 9), ('Weight loss', 8),
      ('Coughing up blood', 8), ('Fever', 5), ('Fatigue', 5)],
     [('chronic', 'hiv', 4, 'HIV is the strongest TB risk factor'),
      ('prior_episode', '', 3, 'Previous TB episode on file')]),

    ('Asthma', 'J45.9',
     [('Wheeze', 9), ('Shortness of breath', 7), ('Chest tightness', 7),
      ('Night-time cough', 6), ('Cough', 5)],
     [('prior_episode', '', 4, 'Known asthmatic — prior episode on file'),
      ('chronic', 'asthma', 4, 'Asthma listed as chronic condition'),
      ('chronic', 'eczema', 1, 'Atopy raises asthma likelihood')]),

    ('COPD', 'J44.9',
     [('Shortness of breath', 8), ('Chronic cough (>2 weeks)', 7),
      ('Productive cough', 6), ('Wheeze', 5)],
     [('smoking', 'Current', 4, 'Smoking is the main COPD cause'),
      ('smoking', 'Former', 2, 'Past smoking still raises COPD risk'),
      ('age_band', '40-120', 2, 'COPD is a disease of older adults'),
      ('age_band', '0-30', -4, 'COPD is rare under 30 — contradicts')]),

    ('Allergic rhinitis', 'J30.4',
     [('Sneezing', 8), ('Itchy eyes', 8), ('Runny nose', 7), ('Nasal congestion', 6)],
     [('chronic', 'asthma', 2, 'Atopy — asthma on file'),
      ('chronic', 'eczema', 2, 'Atopy — eczema on file')]),

    ('Acute sinusitis', 'J01.9',
     [('Facial pain', 9), ('Nasal congestion', 7), ('Headache', 5),
      ('Runny nose', 5), ('Fever', 3)],
     []),

    ('Acute tonsillitis', 'J03.9',
     [('Sore throat', 9), ('Difficulty swallowing', 8), ('Fever', 6), ('Headache', 3)],
     [('age_band', '3-15', 2, 'Most common in school-age children')]),

    ('Otitis media', 'H66.9',
     [('Ear pain', 9), ('Ear discharge', 7), ('Reduced hearing', 5), ('Fever', 5)],
     [('age_band', '0-5', 3, 'Very common in under-5s')]),

    ('Gastroenteritis', 'A09',
     [('Diarrhoea', 9), ('Vomiting', 8), ('Nausea', 6), ('Abdominal pain', 5), ('Fever', 4)],
     []),

    ('Gastro-oesophageal reflux (GERD)', 'K21.9',
     [('Heartburn', 9), ('Regurgitation', 8), ('Epigastric pain', 6), ('Chest pain', 4)],
     [('alcohol', 'Heavy', 2, 'Alcohol worsens reflux'),
      ('smoking', 'Current', 1, 'Smoking worsens reflux')]),

    ('Peptic ulcer', 'K27.9',
     [('Epigastric pain', 9), ('Blood in stool', 5), ('Nausea', 4), ('Heartburn', 4)],
     [('alcohol', 'Heavy', 2, 'Alcohol is a peptic-ulcer risk factor'),
      ('prior_episode', '', 3, 'Previous ulcer on file')]),

    ('Irritable bowel syndrome', 'K58.9',
     [('Bloating', 8), ('Abdominal pain', 7), ('Constipation', 5), ('Diarrhoea', 5)],
     [('age_band', '60-120', -2, 'New IBS diagnosis unusual over 60 — exclude organic disease')]),

    ('Constipation', 'K59.0',
     [('Constipation', 10), ('Bloating', 5), ('Abdominal pain', 4)],
     []),

    ('Acute appendicitis', 'K35.8',
     [('Right lower abdominal pain', 10), ('Loss of appetite', 5), ('Abdominal pain', 5),
      ('Nausea', 5), ('Vomiting', 4), ('Fever', 4)],
     [('age_band', '5-40', 2, 'Peak incidence 5–40 years')]),

    ('Acute cystitis (UTI)', 'N30.0',
     [('Dysuria', 9), ('Urinary frequency', 8), ('Urinary urgency', 7),
      ('Blood in urine', 5), ('Suprapubic pain', 5)],
     [('sex', 'F', 2, 'UTIs are far more common in women')]),

    ('Acute pyelonephritis', 'N10',
     [('Flank pain', 9), ('Fever', 7), ('Dysuria', 5), ('Nausea', 4), ('Vomiting', 4)],
     [('sex', 'F', 1, 'More common in women')]),

    ('Essential hypertension', 'I10',
     [('High blood pressure reading', 10), ('Headache', 4), ('Dizziness', 3),
      ('Visual disturbance', 2)],
     [('age_band', '40-120', 2, 'Prevalence rises with age'),
      ('prior_episode', '', 3, 'Known hypertensive'),
      ('chronic', 'hypertension', 3, 'Hypertension on chronic list'),
      ('smoking', 'Current', 1, 'Smoking raises blood pressure')]),

    ('Type 2 diabetes mellitus', 'E11.9',
     [('Excessive thirst', 8), ('Frequent urination', 8), ('Weight loss', 5),
      ('Fatigue', 5), ('Blurred vision', 4)],
     [('age_band', '35-120', 2, 'Type 2 typically presents from mid-adulthood'),
      ('chronic', 'diabetes', 3, 'Diabetes on chronic list')]),

    ('Migraine', 'G43.9',
     [('Unilateral throbbing headache', 9), ('Photophobia', 8), ('Visual aura', 8),
      ('Nausea', 6), ('Headache', 5)],
     [('sex', 'F', 2, 'Migraine is 2–3× more common in women'),
      ('prior_episode', '', 3, 'Known migraineur')]),

    ('Tension-type headache', 'G44.2',
     [('Band-like head pressure', 9), ('Headache', 7), ('Neck pain', 4), ('Poor sleep', 3)],
     []),

    ('Meningitis', 'G03.9',
     [('Neck stiffness', 10), ('Fever', 7), ('Headache', 7), ('Photophobia', 7),
      ('Confusion', 6), ('Vomiting', 5)],
     [('age_band', '0-5', 2, 'Young children at higher risk')]),

    ('Malaria', 'B54',
     [('Fever', 9), ('Chills / rigors', 8), ('Recent travel to malaria area', 9),
      ('Headache', 5), ('Muscle aches', 5), ('Night sweats', 4), ('Nausea', 4)],
     []),

    ('Anaemia', 'D64.9',
     [('Pallor', 9), ('Fatigue', 8), ('Dizziness', 5), ('Shortness of breath', 4),
      ('Palpitations', 4)],
     [('sex', 'F', 1, 'Menstruating women at higher risk')]),

    ('Hypothyroidism', 'E03.9',
     [('Weight gain', 8), ('Cold intolerance', 8), ('Fatigue', 7), ('Dry skin', 5),
      ('Constipation', 4)],
     [('sex', 'F', 2, 'Much more common in women'),
      ('age_band', '40-120', 1, 'Incidence rises with age')]),

    ('Hyperthyroidism', 'E05.9',
     [('Heat intolerance', 8), ('Weight loss', 7), ('Palpitations', 7), ('Tremor', 7),
      ('Anxiety / excessive worry', 4), ('Diarrhoea', 3)],
     [('sex', 'F', 2, 'Much more common in women')]),

    ('Depressive episode', 'F32.9',
     [('Low mood', 9), ('Loss of interest', 9), ('Poor sleep', 6),
      ('Poor concentration', 5), ('Fatigue', 5), ('Appetite change', 4)],
     []),

    ('Generalised anxiety disorder', 'F41.9',
     [('Anxiety / excessive worry', 9), ('Palpitations', 6), ('Poor sleep', 5),
      ('Tremor', 4), ('Chest tightness', 3), ('Dizziness', 3)],
     []),

    ('Atopic dermatitis (eczema)', 'L20.9',
     [('Itching', 8), ('Dry skin', 7), ('Rash', 6)],
     [('age_band', '0-5', 2, 'Usually starts in early childhood'),
      ('chronic', 'asthma', 2, 'Atopy — asthma on file')]),

    ('Urticaria', 'L50.9',
     [('Wheals / hives', 10), ('Itching', 7), ('Rash', 5)],
     []),

    ('Cellulitis', 'L03.9',
     [('Skin redness', 9), ('Skin swelling', 8), ('Skin warmth / tenderness', 8), ('Fever', 4)],
     [('chronic', 'diabetes', 2, 'Diabetes predisposes to skin infection')]),

    ('Scabies', 'B86',
     [('Itching worse at night', 9), ('Itching', 9), ('Household contacts itching', 8),
      ('Rash', 6)],
     []),

    ('Low back pain', 'M54.5',
     [('Low back pain', 10), ('Muscle aches', 3)],
     []),

    ('Osteoarthritis', 'M19.9',
     [('Joint pain', 8), ('Joint stiffness', 7), ('Joint swelling', 4)],
     [('age_band', '50-120', 3, 'Degenerative — prevalence rises with age'),
      ('age_band', '0-30', -3, 'Uncommon under 30 — contradicts')]),

    ('Gout', 'M10.9',
     [('Big toe pain', 10), ('Joint swelling', 7), ('Joint redness', 7), ('Joint pain', 5)],
     [('sex', 'M', 2, 'Far more common in men'),
      ('alcohol', 'Heavy', 2, 'Alcohol precipitates gout'),
      ('chronic', 'hypertension', 1, 'Hypertension/diuretics raise urate')]),

    ('Angina pectoris', 'I20.9',
     [('Exertional chest pain', 10), ('Chest pain', 8), ('Shortness of breath', 5),
      ('Palpitations', 3)],
     [('age_band', '45-120', 3, 'Ischaemic heart disease rises with age'),
      ('smoking', 'Current', 2, 'Smoking — major cardiac risk factor'),
      ('chronic', 'hypertension', 2, 'Hypertension — cardiac risk factor'),
      ('chronic', 'diabetes', 2, 'Diabetes — cardiac risk factor')]),

    ('Acute myocardial infarction', 'I21.9',
     [('Crushing chest pain', 10), ('Pain radiating to arm / jaw', 9), ('Chest pain', 7),
      ('Sweating', 6), ('Shortness of breath', 5), ('Nausea', 4)],
     [('age_band', '45-120', 3, 'Ischaemic heart disease rises with age'),
      ('smoking', 'Current', 2, 'Smoking — major cardiac risk factor'),
      ('chronic', 'hypertension', 2, 'Hypertension — cardiac risk factor'),
      ('chronic', 'diabetes', 2, 'Diabetes — cardiac risk factor')]),

    ('Heart failure', 'I50.9',
     [('Orthopnoea', 9), ('Leg swelling', 8), ('Shortness of breath', 7), ('Fatigue', 5)],
     [('age_band', '60-120', 3, 'Most common in the elderly'),
      ('chronic', 'hypertension', 2, 'Hypertension — leading HF cause'),
      ('chronic', 'heart', 2, 'Known heart disease on file')]),

    ('Deep vein thrombosis', 'I80.2',
     [('Calf pain', 9), ('Calf swelling', 9), ('Recent immobilisation / long travel', 7),
      ('Leg redness', 5)],
     []),

    ('Dysmenorrhoea', 'N94.6',
     [('Painful periods', 10), ('Pelvic pain', 6), ('Low back pain', 3)],
     [('sex', 'F', 3, 'Gynaecological condition'),
      ('sex', 'M', -10, 'Not possible in male patients — contradicts')]),

    ('Pelvic inflammatory disease', 'N73.9',
     [('Pelvic pain', 9), ('Vaginal discharge', 8), ('Pain during intercourse', 7),
      ('Fever', 5)],
     [('sex', 'F', 3, 'Gynaecological condition'),
      ('sex', 'M', -10, 'Not possible in male patients — contradicts')]),

    ('Vaginal candidiasis', 'B37.3',
     [('Vaginal itching', 9), ('Vaginal discharge', 8)],
     [('sex', 'F', 2, 'Gynaecological condition'),
      ('sex', 'M', -10, 'Not possible in male patients — contradicts'),
      ('chronic', 'diabetes', 2, 'Diabetes predisposes to candidiasis')]),

    ('Conjunctivitis', 'H10.9',
     [('Red eye', 9), ('Eye discharge', 8), ('Itchy eyes', 5), ('Visual disturbance', 2)],
     []),

    ('Epilepsy', 'G40.9',
     [('Seizure', 10), ('Blackout / loss of consciousness', 7), ('Confusion', 5)],
     [('prior_episode', '', 4, 'Known epileptic — prior episode on file'),
      ('chronic', 'epilepsy', 4, 'Epilepsy on chronic list')]),

    ('HIV disease', 'B24',
     [('Recurrent infections', 7), ('Swollen lymph nodes', 7), ('Weight loss', 6),
      ('Night sweats', 5), ('Fatigue', 5)],
     []),
]
