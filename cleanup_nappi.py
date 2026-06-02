import json
import re

with open(r"d:\downloads\medicaregp_1\nappi_codes_extracted.json") as f:
    data = json.load(f)

def clean_desc(desc):
    # Remove criteria/review words at end
    criteria_words = [
        r'\s+Accepted treatment\s*$',
        r'\s+Clinical Review\s*$',
        r'\s+Clinical Motivation\s*$',
        r'\s+Specialist script\s*$',
        r'\s+Specialist motivation\s*$',
        r'\s+Special Investigations.*$',
        r'\s+SI.*$',
        r'\s+Yes\s+Yes.*$',
        r'\s+No\s+No.*$',
        r'\s+Yes\s+No.*$',
        r'\s+CDL.*$',
        r'\s+PBR.*$',
        r'\s+Non-PBR.*$',
        r'\s+PENICILLINS\s*$',
        r'\s+ORAL ANTI-DIABETIC AGENTS\s*$',
        r'\s+CORTICOSTEROIDS\s*$',
        r'\s+SYMPATHOMIMETICS\s*$',
        r'\s+COMBINATION BRONCHODILATORS\s*$',
        r'\s+GLUCOCORTICOIDS\s*$',
        r'\s+METHYLXANTHINES.*$',
        r'\s+ANTICHOLINERGICS\s*$',
        r'\s+CORTICO-STEROIDS.*$',
        r'\s+TAB\s*$',
        r'\s+CAP\s*$',
    ]
    for pattern in criteria_words:
        desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
    # Remove excessive spaces
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Remove trailing generic name repetition in parens
    desc = re.sub(r'\s*\([^)]+\)\s*$', '', desc).strip()
    return desc

# Fix Emergency/Injection category: add adrenaline and ceftriaxone entries
# and handle ciprofloxacin eye drops (which may be in Antibiotics)
fixed_data = []
for item in data:
    # Reclassify eye-specific ciprofloxacin to Eye/Ear
    if item['category'] == 'Antibiotics':
        low = item['desc'].lower()
        if ('eye' in low or 'opd' in low or 'ear' in low or 'ophthalmic' in low or 
            'ocular' in low or 'oph' in low or '0.3%' in low):
            item['category'] = 'Eye/Ear'
    
    # Reclassify injections to Emergency/Injection
    if item['category'] in ('Cardiovascular', 'Hormones', 'Antibiotics', 'Antidiabetic', 'GI') :
        low = item['desc'].lower()
        if ('adrenaline' in low or 'epinephrine' in low):
            item['category'] = 'Emergency/Injection'
        elif 'ceftriaxone' in low and ('inj' in low or 'ivp' in low or 'inf' in low or 'vial' in low):
            item['category'] = 'Emergency/Injection'
        elif 'dexamethasone' in low and ('inj' in low or 'ivp' in low or 'amp' in low):
            item['category'] = 'Emergency/Injection'
        elif 'ondansetron' in low and ('inj' in low or 'ivp' in low or 'amp' in low):
            item['category'] = 'Emergency/Injection'
        elif 'vitamin b12' in low or 'cyanocobalamin' in low or 'hydroxocobalamin' in low:
            if 'inj' in low or 'amp' in low or 'ivp' in low:
                item['category'] = 'Emergency/Injection'
        elif 'diclofenac' in low and ('inj' in low or 'amp' in low):
            item['category'] = 'Emergency/Injection'
    
    item['desc'] = clean_desc(item['desc'])
    
    # Skip if desc becomes too short
    if len(item['desc']) < 5:
        continue
    
    fixed_data.append(item)

# Deduplicate keeping first occurrence
seen = {}
for item in fixed_data:
    code = item['code']
    if code not in seen:
        seen[code] = item

final_list = sorted(seen.values(), key=lambda x: x['category'] + x['desc'])

print(f"Final count: {len(final_list)}")

from collections import Counter
cats = Counter(v['category'] for v in final_list)
for cat, cnt in sorted(cats.items()):
    print(f"  {cat}: {cnt}")

with open(r"d:\downloads\medicaregp_1\nappi_codes_final2.json", "w", encoding="utf-8") as f:
    json.dump(final_list, f, indent=2, ensure_ascii=False)
print("Saved nappi_codes_final2.json")

# Also show some samples of the specific drugs requested
print("\n--- Specific drug samples ---")
key_terms = ['ramipril', 'warfarin', 'clopidogrel', 'glimepiride', 'insulin glargine', 'tiotropium',
             'ondansetron', 'quetiapine', 'dolutegravir', 'tamsulosin', 'latanoprost', 'adrenaline',
             'allopurinol', 'tretinoin', 'co-trimoxazole', 'metformin xr', 'liraglutide']
for term in key_terms:
    matches = [item for item in final_list if term.lower() in item['desc'].lower()]
    print(f"\n{term}: {len(matches)} entries")
    for m in matches[:3]:
        print(f"  {m['code']} | {m['desc']}")
