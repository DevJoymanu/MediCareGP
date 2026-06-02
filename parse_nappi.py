import re
import json
import os

# Already-owned codes to exclude
EXISTING_CODES = set([
    717725,716045,713153,792101,894281,862304,706930,720577,710857,700315,
    891980,705810,891983,778230,827592,706314,704606,745561,704791,785229,
    704401,811440,705637,714184,704068,853542,722938,705471,705100,717052,
    718711,707552,893402,716944,714192,704353,784354,716518,893951,742872,
    726346,703389,849960,717347,780561,710310,793329,897880,706327,837253,
    714312,703917,703916,707278,793124,711682,861545,881481,894324,891279,
    862053,703645,781703,700692,715649,785121,714869,710079,716495,716644,
    890470,880949,786586,786578,704651,704653,703914,704373,704133,739251,
    703909,709172,707670,706672,708281,827053,894502,729361,714582,716953,
    702923,706039,722456,720929,721619,717787,717786,717785,717788,849332,
    775274,775452,836001,835994,3004196,3004197,890164,786241,794007,718678,
    807885,718310,717385,718125,800155,703720,814407,716381,805149,3000589,
    849383,3005694,721061,897132,717376,715312,881589,712134,841609,3005572,
    715875,714828,700712,744611,715830,894498,792071,732478,707342,792691,
    721611,708722,815047,700167,894303,821063,840653,716520,719547,703232,
    711214,712092,715935,703999,712093,772003,771996,3002709,774472,774480,
    753181,761079,761087,721545,721546,835129,705532,710580,723814,756571,
    705853,727024,705531,710557,721366,3002180,3002652,711640,3002908,704941,
    750654,750662,807834,745472,700445,764353,827290,800163,754064,882934,
    846155,757527,894289,793493,712205,788554,712213,873551,823473,826340,
    706493,723040,715837,702504,713724,713759,817201,713872,717370,717371,
    719670,747297,878790,794333,715997,715091,723307,721498,712932,718601,
    712070,718672,721606,826030,720419,706705,706704,3000025,713058,3004784,
    713066
])

# Drug keyword patterns and category mapping
DRUG_PATTERNS = [
    # Cardiovascular
    (r'\bramipril\b', 'Cardiovascular'),
    (r'\bvalsartan\b', 'Cardiovascular'),
    (r'\btelmisartan\b', 'Cardiovascular'),
    (r'\bcarvedilol\b', 'Cardiovascular'),
    (r'\bfurosemide\b', 'Cardiovascular'),
    (r'\bspironolactone\b', 'Cardiovascular'),
    (r'\bwarfarin\b', 'Cardiovascular'),
    (r'\bclopidogrel\b', 'Cardiovascular'),
    (r'\bglyceryl trinitrate\b|\bgtn\b|\bnitroglycerin\b', 'Cardiovascular'),
    (r'\bdigoxin\b', 'Cardiovascular'),
    (r'\bamiodarone\b', 'Cardiovascular'),
    (r'\bdiltiazem\b', 'Cardiovascular'),
    (r'\bsotalol\b', 'Cardiovascular'),
    (r'\brivaroxaban\b', 'Cardiovascular'),
    (r'\bapixaban\b', 'Cardiovascular'),
    (r'\baspirin\b', 'Cardiovascular'),
    (r'\bamlodipine\b', 'Cardiovascular'),
    (r'\bnifedipine\b', 'Cardiovascular'),
    (r'\bisosorbide\b', 'Cardiovascular'),
    (r'\batenolol\b', 'Cardiovascular'),
    (r'\bbisoprolol\b', 'Cardiovascular'),
    (r'\blosartan\b', 'Cardiovascular'),
    (r'\birbesartan\b', 'Cardiovascular'),
    (r'\benalapril\b', 'Cardiovascular'),
    (r'\blisinopril\b', 'Cardiovascular'),
    (r'\bperindopril\b', 'Cardiovascular'),
    (r'\bhydralazine\b', 'Cardiovascular'),
    (r'\bnebivolol\b', 'Cardiovascular'),
    (r'\brosuvastatin\b', 'Cardiovascular'),
    (r'\batorvastatin\b', 'Cardiovascular'),
    (r'\bsimvastatin\b', 'Cardiovascular'),
    (r'\bfenofibrate\b', 'Cardiovascular'),
    (r'\bdabigatran\b', 'Cardiovascular'),
    (r'\bedoxaban\b', 'Cardiovascular'),
    (r'\bdipyridamole\b', 'Cardiovascular'),
    # Antidiabetic
    (r'\bmetformin\b', 'Antidiabetic'),
    (r'\bglimepiride\b', 'Antidiabetic'),
    (r'\bpioglitazone\b', 'Antidiabetic'),
    (r'\bliraglutide\b', 'Antidiabetic'),
    (r'\binsulin glargine\b|\blantus\b|\bbasaglar\b|\btoujeo\b', 'Antidiabetic'),
    (r'\binsulin aspart\b|\bnovorapid\b|\bnovoLog\b', 'Antidiabetic'),
    (r'\binsulin detemir\b|\blevemir\b', 'Antidiabetic'),
    (r'\binsulin lispro\b|\bhumalog\b', 'Antidiabetic'),
    (r'\bpremixed insulin\b|\binsulin mix\b|\bnovomix\b|\bhumalog mix\b|\bmixtard\b', 'Antidiabetic'),
    (r'\binsulin 30\b|\binsulin 50\b|\bbiphasic\b', 'Antidiabetic'),
    (r'\bempagliflozin\b', 'Antidiabetic'),
    (r'\bdapagliflozin\b', 'Antidiabetic'),
    (r'\bcanagliflozin\b', 'Antidiabetic'),
    (r'\bsitagliptin\b', 'Antidiabetic'),
    (r'\bvildagliptin\b', 'Antidiabetic'),
    (r'\bsaxagliptin\b', 'Antidiabetic'),
    (r'\bexenatide\b', 'Antidiabetic'),
    (r'\bglibenclamide\b|\bglyburide\b', 'Antidiabetic'),
    (r'\bgliclazide\b', 'Antidiabetic'),
    (r'\bglipizide\b', 'Antidiabetic'),
    (r'\binsulin isophane\b|\bnph insulin\b|\bhumulin n\b|\binsulard\b', 'Antidiabetic'),
    (r'\binsulin regular\b|\bactrapid\b|\bhumulin r\b', 'Antidiabetic'),
    (r'\bdulaglutide\b', 'Antidiabetic'),
    (r'\bsemaglutide\b', 'Antidiabetic'),
    # Respiratory
    (r'\btiotropium\b', 'Respiratory'),
    (r'\bsalmeterol\b', 'Respiratory'),
    (r'\bfluticasone\b', 'Respiratory'),
    (r'\bbudesonide\b', 'Respiratory'),
    (r'\bformoterol\b', 'Respiratory'),
    (r'\btheophylline\b', 'Respiratory'),
    (r'\bacetylcysteine\b', 'Respiratory'),
    (r'\bipratropium\b', 'Respiratory'),
    (r'\bsalbutamol\b', 'Respiratory'),
    (r'\bterbutaline\b', 'Respiratory'),
    (r'\bmontelukast\b', 'Respiratory'),
    (r'\bromflumilast\b|\broflumilast\b', 'Respiratory'),
    (r'\bindacaterol\b', 'Respiratory'),
    (r'\bglycopyrronium\b|\bglycopyrrolate\b', 'Respiratory'),
    (r'\bumeclidinium\b', 'Respiratory'),
    (r'\bvilanterol\b', 'Respiratory'),
    (r'\bbeclomethasone\b|\bbeclometasone\b', 'Respiratory'),
    (r'\bciclesonide\b', 'Respiratory'),
    (r'\bfenoterol\b', 'Respiratory'),
    # GI
    (r'\bondansetron\b', 'GI'),
    (r'\bhyoscine\b|\bbuscopan\b', 'GI'),
    (r'\bbisacodyl\b', 'GI'),
    (r'\bsenna\b', 'GI'),
    (r'\bpolyethylene glycol\b|\bmovicol\b|\bmacrogol\b', 'GI'),
    (r'\bomeprazole\b', 'GI'),
    (r'\besomeprazole\b', 'GI'),
    (r'\blansoprazole\b', 'GI'),
    (r'\bpantoprazole\b', 'GI'),
    (r'\branitidine\b', 'GI'),
    (r'\bcimetidine\b', 'GI'),
    (r'\bdomperidone\b', 'GI'),
    (r'\bmetoclopramide\b', 'GI'),
    (r'\bloperamide\b', 'GI'),
    (r'\bprochlorperazine\b', 'GI'),
    # CNS
    (r'\bquetiapine\b', 'CNS'),
    (r'\bcarbamazepine\b', 'CNS'),
    (r'\bsodium valproate\b|\bvalproate\b|\bvalproic acid\b', 'CNS'),
    (r'\blamotrigine\b', 'CNS'),
    (r'\bgabapentin\b', 'CNS'),
    (r'\bpregabalin\b', 'CNS'),
    (r'\bzolpidem\b', 'CNS'),
    (r'\bmethylphenidate\b', 'CNS'),
    (r'\bdonepezil\b', 'CNS'),
    (r'\bmirtazapine\b', 'CNS'),
    (r'\bvenlafaxine\b', 'CNS'),
    (r'\bduloxetine\b', 'CNS'),
    (r'\bhaloperidol\b', 'CNS'),
    (r'\bolanzapine\b', 'CNS'),
    (r'\brisperidone\b', 'CNS'),
    (r'\bclozapine\b', 'CNS'),
    (r'\baripiprazole\b', 'CNS'),
    (r'\bfluoxetine\b', 'CNS'),
    (r'\bsertraline\b', 'CNS'),
    (r'\bcitalopram\b', 'CNS'),
    (r'\bescitalopram\b', 'CNS'),
    (r'\bparoxetine\b', 'CNS'),
    (r'\bamitriptyline\b', 'CNS'),
    (r'\bimipramine\b', 'CNS'),
    (r'\bclomipramine\b', 'CNS'),
    (r'\bdiazepam\b', 'CNS'),
    (r'\blorazepam\b', 'CNS'),
    (r'\bclonazepam\b', 'CNS'),
    (r'\bphenytoin\b|\bphenytoin sodium\b', 'CNS'),
    (r'\blevetiracetam\b', 'CNS'),
    (r'\btopiramate\b', 'CNS'),
    (r'\boxcarbazepine\b', 'CNS'),
    (r'\bphenobarbitone\b|\bphenobarbital\b', 'CNS'),
    (r'\blithium\b', 'CNS'),
    (r'\bramelteon\b|\bzopiclone\b', 'CNS'),
    (r'\bmelatonin\b', 'CNS'),
    (r'\bmemantine\b', 'CNS'),
    (r'\brivastigmine\b', 'CNS'),
    (r'\bgalantamine\b', 'CNS'),
    (r'\batomoxetine\b', 'CNS'),
    (r'\bbupropion\b', 'CNS'),
    (r'\btrazodone\b', 'CNS'),
    # Hormones
    (r'\blevothyroxine\b|\bthyroxine\b', 'Hormones'),
    (r'\bdexamethasone\b', 'Hormones'),
    (r'\bhydrocortisone\b', 'Hormones'),
    (r'\bmethylprednisolone\b', 'Hormones'),
    (r'\bprednisolone\b', 'Hormones'),
    (r'\bprednisone\b', 'Hormones'),
    (r'\bfludrocortisone\b', 'Hormones'),
    (r'\btriamcinolone\b', 'Hormones'),
    # Antibiotics
    (r'\bco-trimoxazole\b|\bcotrimoxazole\b|\btrimethoprim.sulfamethoxazole\b', 'Antibiotics'),
    (r'\bnitrofurantoin\b', 'Antibiotics'),
    (r'\bcefuroxime\b', 'Antibiotics'),
    (r'\blevofloxacin\b', 'Antibiotics'),
    (r'\bclarithromycin\b', 'Antibiotics'),
    (r'\bphenoxymethylpenicillin\b|\bpenicillin v\b', 'Antibiotics'),
    (r'\bamoxicillin\b', 'Antibiotics'),
    (r'\bcephalexin\b|\bcefalexin\b', 'Antibiotics'),
    (r'\bclindamycin\b', 'Antibiotics'),
    (r'\bdoxycycline\b', 'Antibiotics'),
    (r'\btetracycline\b', 'Antibiotics'),
    (r'\berythromycin\b', 'Antibiotics'),
    (r'\bazithromycin\b', 'Antibiotics'),
    (r'\bciprofloxacin\b', 'Antibiotics'),
    (r'\bnorfloxacin\b', 'Antibiotics'),
    (r'\bmetronidazole\b', 'Antibiotics'),
    (r'\btinidazole\b', 'Antibiotics'),
    (r'\bflucloxacillin\b|\bdicloxacillin\b', 'Antibiotics'),
    (r'\bamoxicillin.clavulanate\b|\bco.amoxiclav\b|\baugmentin\b', 'Antibiotics'),
    (r'\bceftriaxone\b', 'Antibiotics'),
    (r'\bcefazolin\b', 'Antibiotics'),
    (r'\bvancomycin\b', 'Antibiotics'),
    (r'\bgentamicin\b', 'Antibiotics'),
    # HIV/TB
    (r'\bdolutegravir\b|\btivicay\b', 'HIV/TB'),
    (r'\btenofovir.lamivudine.dolutegravir\b|\btdf.3tc.dtg\b|\bodimune\b|\btriumeq\b', 'HIV/TB'),
    (r'\blamivudine\b|\b3tc\b', 'HIV/TB'),
    (r'\bisoniazid\b', 'HIV/TB'),
    (r'\brifampicin\b|\brifampin\b', 'HIV/TB'),
    (r'\bpyrazinamide\b', 'HIV/TB'),
    (r'\brhze\b|\brifampicin.isoniazid.pyrazinamide.ethambutol\b|\bfourfix\b|\brifafour\b', 'HIV/TB'),
    (r'\bethambutol\b', 'HIV/TB'),
    (r'\befavirenz\b', 'HIV/TB'),
    (r'\btenofovir\b|\btdf\b', 'HIV/TB'),
    (r'\bemtricitabine\b', 'HIV/TB'),
    (r'\bnevirapine\b', 'HIV/TB'),
    (r'\blopinavir\b|\britonavir\b|\bkaletra\b', 'HIV/TB'),
    (r'\batazanavir\b', 'HIV/TB'),
    (r'\bdarunavir\b', 'HIV/TB'),
    (r'\braltegravir\b', 'HIV/TB'),
    (r'\bcabotegravir\b', 'HIV/TB'),
    (r'\babacavir\b', 'HIV/TB'),
    (r'\bdidanosine\b|\bstavudine\b|\bzidovudine\b|\bazt\b', 'HIV/TB'),
    # Urology
    (r'\btamsulosin\b', 'Urology'),
    (r'\bfinasteride\b', 'Urology'),
    (r'\bsildenafil\b', 'Urology'),
    (r'\btadalafil\b', 'Urology'),
    (r'\boxybutynin\b', 'Urology'),
    (r'\bsolifenacin\b', 'Urology'),
    (r'\btolterodine\b', 'Urology'),
    (r'\bdutasteride\b', 'Urology'),
    (r'\balfuzosin\b', 'Urology'),
    (r'\bdoxazosin\b', 'Urology'),
    # Eye/Ear
    (r'\bartificial tears\b|\bhypromellose\b|\bcarmellose\b|\bsodium hyaluronate\b', 'Eye/Ear'),
    (r'\btobramycin\b', 'Eye/Ear'),
    (r'\blatanoprost\b', 'Eye/Ear'),
    (r'\btimolol\b', 'Eye/Ear'),
    (r'\bbimatoprost\b', 'Eye/Ear'),
    (r'\btravoprost\b', 'Eye/Ear'),
    (r'\bdorzolamide\b', 'Eye/Ear'),
    (r'\bbrimonidine\b', 'Eye/Ear'),
    (r'\bchloramphenicol eye\b', 'Eye/Ear'),
    # Emergency/Injection
    (r'\badrenaline\b|\bepinephrine\b', 'Emergency/Injection'),
    (r'\bdiclofenac\b', 'Emergency/Injection'),
    (r'\bvitamin b12\b|\bcyanocobalamin\b|\bhydroxocobalamin\b', 'Emergency/Injection'),
    # Osteoporosis/Gout
    (r'\ballopurinol\b', 'Osteoporosis/Gout'),
    (r'\bcolchicine\b', 'Osteoporosis/Gout'),
    (r'\balendronate\b|\balendronic acid\b', 'Osteoporosis/Gout'),
    (r'\brisedronate\b', 'Osteoporosis/Gout'),
    (r'\bzoledronic acid\b', 'Osteoporosis/Gout'),
    # Dermatology
    (r'\btretinoin\b', 'Dermatology'),
    (r'\bisotretinoin\b', 'Dermatology'),
    (r'\bbenzoyl peroxide\b', 'Dermatology'),
    (r'\bfusidic acid\b|\bfusidate\b', 'Dermatology'),
    (r'\bpermethrin\b', 'Dermatology'),
    (r'\bcalcipotriol\b', 'Dermatology'),
    (r'\bclobetasol\b', 'Dermatology'),
    (r'\bbetamethasone\b', 'Dermatology'),
    (r'\bketoconazole\b', 'Dermatology'),
    (r'\bclotrimazole\b', 'Dermatology'),
    (r'\bmiconazole\b', 'Dermatology'),
    (r'\bterbinafine\b', 'Dermatology'),
    (r'\bdapsone\b', 'Dermatology'),
]

def get_category(text):
    text_lower = text.lower()
    for pattern, cat in DRUG_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return cat
    return None

# Parse GEMS Oct 2024 (format: group_code GENERIC_NAME nappi_code BRAND_NAME strength form pack price)
def parse_gems_oct2024(filepath):
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Pattern: [group_code] [generic_desc] [nappi_code] [product_name] [strength_and_form] [pack] [price]
    # E.g: "1174 ACETYLCYSTEINE 824291 ACC 200MG EFT 25 R 83.68"
    line_pattern = re.compile(r'^\s*(\d+)\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\w.*?)\s+(\d+)\s+R\s+[\d,]+')
    
    for line in lines:
        m = line_pattern.match(line)
        if m:
            generic_desc = m.group(2).strip()
            nappi_code = int(m.group(3))
            product_name = m.group(4).strip()
            strength_form = m.group(5).strip()
            
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            
            # Check text for drug matches
            combined = f"{generic_desc} {product_name} {strength_form}"
            cat = get_category(combined)
            if cat:
                desc = f"{product_name} {strength_form}".strip()
                results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

# Parse GEMS Jan 2025 (format: nappi BRAND_NAME generic strength form criteria)
def parse_gems_jan2025(filepath):
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    line_pattern = re.compile(r'^(\d{5,8})\s+([A-Z][^\d]+?)\s+(\w.+?)$')
    
    for line in lines:
        m = line_pattern.match(line.strip())
        if m:
            nappi_code = int(m.group(1))
            rest = m.group(2).strip() + ' ' + m.group(3).strip()
            
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            
            cat = get_category(rest)
            if cat:
                desc = rest.split('  ')[0].strip()
                results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

# Parse Discovery 2025 (format: nappi product_name strength dosage_form price...)
def parse_discovery(filepath):
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Format: NAPPI product_name strength FORM ...
    for line in lines:
        # Look for lines starting with NAPPI code
        parts = line.strip().split()
        if not parts:
            continue
        if re.match(r'^\d{5,8}$', parts[0]):
            nappi_code = int(parts[0])
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            rest = ' '.join(parts[1:])
            cat = get_category(rest)
            if cat:
                # Try to extract meaningful desc
                # Discovery format: nappi ProductName strength FORM price...
                # Remove trailing numeric/price data
                desc_parts = []
                for p in parts[1:]:
                    if re.match(r'^[\d.R,]+$', p):
                        break
                    if p in ('Yes', 'No'):
                        break
                    desc_parts.append(p)
                desc = ' '.join(desc_parts)
                results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

# Parse Medimed (format: MEDICINE_NAME ACTIVE_INGREDIENT THERAPEUTIC_GROUP NAPPI_CODE PACK_SIZE FIRST_TIER)
def parse_medimed(filepath):
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        # Find NAPPI codes in lines - they usually look like 9-digit codes (nappi+pack size appended)
        # Format: BRAND ACTIVE THERAP_GROUP NAPPICODE PACK TIER
        # E.g: FLORINEF 0.1MG TABS FLUDROCORTISONE ACETATE TAB 0.1 MG CORTICOSTEROIDS 726540005 100 YES
        m = re.search(r'\b(\d{5,8})\d{3}\b', line)
        if m:
            nappi_code = int(m.group(1))
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            cat = get_category(line)
            if cat:
                # Extract desc from beginning of line
                # Remove trailing code+pack+YES/NO
                desc_line = re.sub(r'\s+\d{9,}\s+\d+\s+(YES|NO).*', '', line).strip()
                results[nappi_code] = {"code": str(nappi_code), "desc": desc_line, "category": cat}
    return results

# Parse MMI tariff (huge file - similar format check)
def parse_mmi(filepath):
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Look for NAPPI-code-like patterns with drug names
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        # Lines often: NAPPI DESCRIPTION STRENGTH FORM ...
        if re.match(r'^\d{5,8}$', parts[0]):
            nappi_code = int(parts[0])
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            rest = ' '.join(parts[1:])
            cat = get_category(rest)
            if cat:
                desc_parts = []
                for p in parts[1:]:
                    if re.match(r'^R[\d.]+$', p):
                        break
                    desc_parts.append(p)
                desc = ' '.join(desc_parts)
                results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

basedir = r'd:\downloads\medicaregp_1'
all_results = {}

print("Parsing GEMS Oct 2024...")
r1 = parse_gems_oct2024(os.path.join(basedir, 'extracted_GEMS_Oct2024.txt'))
print(f"  Found {len(r1)} entries")
all_results.update(r1)

print("Parsing GEMS Jan 2025...")
r2 = parse_gems_jan2025(os.path.join(basedir, 'extracted_GEMS_Jan2025.txt'))
print(f"  Found {len(r2)} entries")
for k, v in r2.items():
    if k not in all_results:
        all_results[k] = v

print("Parsing Discovery 2025...")
r3 = parse_discovery(os.path.join(basedir, 'extracted_Discovery2025.txt'))
print(f"  Found {len(r3)} entries")
for k, v in r3.items():
    if k not in all_results:
        all_results[k] = v

print("Parsing Medimed...")
r4 = parse_medimed(os.path.join(basedir, 'extracted_Medimed.txt'))
print(f"  Found {len(r4)} entries")
for k, v in r4.items():
    if k not in all_results:
        all_results[k] = v

print("Parsing MMI GEMS tariff...")
r5 = parse_mmi(os.path.join(basedir, 'extracted_MMI_GEMS_tariff.txt'))
print(f"  Found {len(r5)} entries")
for k, v in r5.items():
    if k not in all_results:
        all_results[k] = v

final_list = sorted(all_results.values(), key=lambda x: x['category'] + x['desc'])
print(f"\nTotal unique new entries: {len(final_list)}")

# Show by category
from collections import Counter
cats = Counter(v['category'] for v in final_list)
for cat, cnt in sorted(cats.items()):
    print(f"  {cat}: {cnt}")

# Save result
out_path = os.path.join(basedir, 'nappi_codes_extracted.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(final_list, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {out_path}")
