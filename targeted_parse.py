import re
import json
import os

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

DRUG_PATTERNS = [
    (r"ramipril", "Cardiovascular"),
    (r"valsartan", "Cardiovascular"),
    (r"telmisartan", "Cardiovascular"),
    (r"carvedilol", "Cardiovascular"),
    (r"furosemide|frusemide", "Cardiovascular"),
    (r"spironolactone", "Cardiovascular"),
    (r"warfarin", "Cardiovascular"),
    (r"clopidogrel", "Cardiovascular"),
    (r"glyceryl trinitrate|gtn spray|nitroglycerin|isosorbide dinitrate|isosorbide mononitrate", "Cardiovascular"),
    (r"digoxin|lanoxin", "Cardiovascular"),
    (r"amiodarone|cordarone", "Cardiovascular"),
    (r"diltiazem", "Cardiovascular"),
    (r"sotalol", "Cardiovascular"),
    (r"rivaroxaban|xarelto", "Cardiovascular"),
    (r"apixaban|eliquis", "Cardiovascular"),
    (r"aspirin|acetylsalicylic", "Cardiovascular"),
    (r"amlodipine", "Cardiovascular"),
    (r"nifedipine", "Cardiovascular"),
    (r"atenolol", "Cardiovascular"),
    (r"bisoprolol", "Cardiovascular"),
    (r"losartan", "Cardiovascular"),
    (r"irbesartan", "Cardiovascular"),
    (r"enalapril", "Cardiovascular"),
    (r"lisinopril", "Cardiovascular"),
    (r"perindopril", "Cardiovascular"),
    (r"hydralazine", "Cardiovascular"),
    (r"nebivolol", "Cardiovascular"),
    (r"rosuvastatin", "Cardiovascular"),
    (r"atorvastatin", "Cardiovascular"),
    (r"simvastatin", "Cardiovascular"),
    (r"fenofibrate", "Cardiovascular"),
    (r"dabigatran|pradaxa", "Cardiovascular"),
    (r"dipyridamole", "Cardiovascular"),
    (r"metoprolol", "Cardiovascular"),
    (r"propranolol", "Cardiovascular"),
    (r"isosorbide", "Cardiovascular"),
    (r"nitrendipine|felodipine|lercanidipine|lacidipine", "Cardiovascular"),
    (r"ezetimibe", "Cardiovascular"),
    (r"pravastatin|fluvastatin|lovastatin", "Cardiovascular"),
    (r"candesartan|olmesartan|azilsartan|eprosartan", "Cardiovascular"),
    (r"captopril|fosinopril|quinapril|trandolapril|moexipril", "Cardiovascular"),
    (r"metformin", "Antidiabetic"),
    (r"glimepiride|amaryl", "Antidiabetic"),
    (r"pioglitazone|actos", "Antidiabetic"),
    (r"liraglutide|victoza", "Antidiabetic"),
    (r"insulin glargine|lantus|basaglar|toujeo|optisulin", "Antidiabetic"),
    (r"insulin aspart|novorapid|novolog|novoaspart", "Antidiabetic"),
    (r"insulin detemir|levemir", "Antidiabetic"),
    (r"insulin lispro|humalog", "Antidiabetic"),
    (r"novomix|mixtard|humulin|insuman|actraphane|actrapid|insulatard|protaphane", "Antidiabetic"),
    (r"biphasic insulin|premix insulin|insulin 30|insulin 50|insulin mix", "Antidiabetic"),
    (r"empagliflozin|jardiance", "Antidiabetic"),
    (r"dapagliflozin|farxiga|forxiga", "Antidiabetic"),
    (r"canagliflozin|invokana", "Antidiabetic"),
    (r"sitagliptin|januvia|janumet", "Antidiabetic"),
    (r"vildagliptin|galvus", "Antidiabetic"),
    (r"saxagliptin|onglyza", "Antidiabetic"),
    (r"exenatide|byetta|bydureon", "Antidiabetic"),
    (r"glibenclamide|glyburide|daonil|euglucon", "Antidiabetic"),
    (r"gliclazide|diamicron", "Antidiabetic"),
    (r"glipizide|glucotrol", "Antidiabetic"),
    (r"dulaglutide|trulicity", "Antidiabetic"),
    (r"semaglutide|ozempic|rybelsus", "Antidiabetic"),
    (r"alogliptin|nesina|vipidia", "Antidiabetic"),
    (r"repaglinide|prandin|novonorm", "Antidiabetic"),
    (r"tiotropium|spiriva", "Respiratory"),
    (r"salmeterol|serevent", "Respiratory"),
    (r"fluticasone", "Respiratory"),
    (r"budesonide|pulmicort", "Respiratory"),
    (r"formoterol|foradil|oxis", "Respiratory"),
    (r"theophylline|aminophylline", "Respiratory"),
    (r"acetylcysteine|mucomyst|fluimucil|acc ", "Respiratory"),
    (r"ipratropium|atrovent", "Respiratory"),
    (r"salbutamol|albuterol|ventolin|asthavent", "Respiratory"),
    (r"terbutaline|bricanyl", "Respiratory"),
    (r"montelukast|singulair", "Respiratory"),
    (r"roflumilast|daxas", "Respiratory"),
    (r"indacaterol|onbrez|arcapta", "Respiratory"),
    (r"glycopyrronium|seebri", "Respiratory"),
    (r"umeclidinium|incruse", "Respiratory"),
    (r"vilanterol", "Respiratory"),
    (r"beclomethasone|beclometasone|becotide|beclazone", "Respiratory"),
    (r"ciclesonide|alvesco", "Respiratory"),
    (r"fenoterol|berotec", "Respiratory"),
    (r"ondansetron|zofran", "GI"),
    (r"hyoscine|buscopan|scopolamine", "GI"),
    (r"bisacodyl|dulcolax", "GI"),
    (r"senna|senokot", "GI"),
    (r"polyethylene glycol|macrogol|movicol|peg 3350", "GI"),
    (r"omeprazole|losec", "GI"),
    (r"esomeprazole|nexium", "GI"),
    (r"lansoprazole|prevacid", "GI"),
    (r"pantoprazole|protonix", "GI"),
    (r"domperidone|motilium", "GI"),
    (r"metoclopramide|maxolon|pramin", "GI"),
    (r"loperamide|imodium", "GI"),
    (r"prochlorperazine|stemetil", "GI"),
    (r"oral rehydration|ORS|rehydrat|dioralyte", "GI"),
    (r"lactulose", "GI"),
    (r"glycerol suppository|glycerin suppository", "GI"),
    (r"mebeverine|colofac", "GI"),
    (r"quetiapine|seroquel", "CNS"),
    (r"carbamazepine|tegretol", "CNS"),
    (r"sodium valproate|valproate|valproic acid|epilim|depakote|depakine", "CNS"),
    (r"lamotrigine|lamictal", "CNS"),
    (r"gabapentin|neurontin", "CNS"),
    (r"pregabalin|lyrica", "CNS"),
    (r"zolpidem|stilnox|ambien", "CNS"),
    (r"methylphenidate|ritalin|concerta", "CNS"),
    (r"donepezil|aricept", "CNS"),
    (r"mirtazapine|remeron", "CNS"),
    (r"venlafaxine|effexor", "CNS"),
    (r"duloxetine|cymbalta", "CNS"),
    (r"haloperidol|haldol", "CNS"),
    (r"olanzapine|zyprexa", "CNS"),
    (r"risperidone|risperdal", "CNS"),
    (r"clozapine|clozaril|leponex", "CNS"),
    (r"aripiprazole|abilify", "CNS"),
    (r"fluoxetine|prozac|sarafem", "CNS"),
    (r"sertraline|zoloft|lustral", "CNS"),
    (r"citalopram|celexa", "CNS"),
    (r"escitalopram|lexapro|cipralex", "CNS"),
    (r"paroxetine|paxil|seroxat", "CNS"),
    (r"amitriptyline|elavil|tryptizol", "CNS"),
    (r"imipramine|tofranil", "CNS"),
    (r"clomipramine|anafranil", "CNS"),
    (r"diazepam|valium", "CNS"),
    (r"lorazepam|ativan", "CNS"),
    (r"clonazepam|rivotril|klonopin", "CNS"),
    (r"phenytoin|dilantin", "CNS"),
    (r"levetiracetam|keppra", "CNS"),
    (r"topiramate|topamax", "CNS"),
    (r"oxcarbazepine|trileptal", "CNS"),
    (r"phenobarbitone|phenobarbital|luminal", "CNS"),
    (r"lithium|camcolit|priadel", "CNS"),
    (r"zopiclone|imovane", "CNS"),
    (r"melatonin", "CNS"),
    (r"memantine|ebixa|namenda", "CNS"),
    (r"rivastigmine|exelon", "CNS"),
    (r"galantamine|reminyl|razadyne", "CNS"),
    (r"atomoxetine|strattera", "CNS"),
    (r"bupropion|wellbutrin|zyban", "CNS"),
    (r"trazodone|desyrel", "CNS"),
    (r"paliperidone|invega", "CNS"),
    (r"ziprasidone|geodon", "CNS"),
    (r"levothyroxine|thyroxine|eltroxin|synthroid", "Hormones"),
    (r"dexamethasone", "Hormones"),
    (r"hydrocortisone", "Hormones"),
    (r"methylprednisolone|solu-medrol", "Hormones"),
    (r"prednisolone", "Hormones"),
    (r"prednisone", "Hormones"),
    (r"fludrocortisone|florinef", "Hormones"),
    (r"triamcinolone|kenalog", "Hormones"),
    (r"betamethasone", "Hormones"),
    (r"co-trimoxazole|cotrimoxazole|sulfamethoxazole|trimethoprim.sulfamethox", "Antibiotics"),
    (r"nitrofurantoin|macrobid|macrodantin", "Antibiotics"),
    (r"cefuroxime|zinnat|zinacef", "Antibiotics"),
    (r"levofloxacin|levaquin", "Antibiotics"),
    (r"clarithromycin|biaxin|klacid", "Antibiotics"),
    (r"phenoxymethylpenicillin|penicillin v|pen vk", "Antibiotics"),
    (r"amoxicillin", "Antibiotics"),
    (r"cephalexin|cefalexin|keflex", "Antibiotics"),
    (r"clindamycin|dalacin", "Antibiotics"),
    (r"doxycycline|vibramycin", "Antibiotics"),
    (r"tetracycline", "Antibiotics"),
    (r"erythromycin|ery-tab|ilosone", "Antibiotics"),
    (r"azithromycin|zithromax|zpack", "Antibiotics"),
    (r"ciprofloxacin", "Antibiotics"),
    (r"norfloxacin|noroxin", "Antibiotics"),
    (r"metronidazole|flagyl", "Antibiotics"),
    (r"tinidazole|fasigyn", "Antibiotics"),
    (r"flucloxacillin|floxapen", "Antibiotics"),
    (r"amoxicillin.clavulanate|co-amoxiclav|augmentin|amoxyclav", "Antibiotics"),
    (r"ceftriaxone|rocephin", "Antibiotics"),
    (r"cefazolin|ancef", "Antibiotics"),
    (r"vancomycin|vancocin", "Antibiotics"),
    (r"gentamicin|garamycin", "Antibiotics"),
    (r"cefpodoxime|cefditorin|cefdinir|cefixime", "Antibiotics"),
    (r"meropenem|imipenem|ertapenem", "Antibiotics"),
    (r"piperacillin|tazobactam", "Antibiotics"),
    (r"sulfamethoxazole", "Antibiotics"),
    (r"dolutegravir|tivicay", "HIV/TB"),
    (r"tenofovir.lamivudine.dolutegravir|tdf.3tc.dtg|odimune|triumeq|acriptega", "HIV/TB"),
    (r"lamivudine|3tc ", "HIV/TB"),
    (r"isoniazid", "HIV/TB"),
    (r"rifampicin|rifampin|rifadin", "HIV/TB"),
    (r"pyrazinamide", "HIV/TB"),
    (r"rhze|rifampicin.isoniazid.pyrazinamide.ethambutol|fourfix|rifafour|rifinah|rimactazid", "HIV/TB"),
    (r"ethambutol|myambutol", "HIV/TB"),
    (r"efavirenz|sustiva|stocrin", "HIV/TB"),
    (r"tenofovir|viread", "HIV/TB"),
    (r"emtricitabine|emtriva", "HIV/TB"),
    (r"nevirapine|viramune", "HIV/TB"),
    (r"lopinavir|ritonavir|kaletra", "HIV/TB"),
    (r"atazanavir|reyataz", "HIV/TB"),
    (r"darunavir|prezista", "HIV/TB"),
    (r"raltegravir|isentress", "HIV/TB"),
    (r"abacavir|ziagen", "HIV/TB"),
    (r"stavudine|d4t|zerit", "HIV/TB"),
    (r"zidovudine|azt|retrovir", "HIV/TB"),
    (r"tamsulosin|flomax|uromax|omsal", "Urology"),
    (r"finasteride|proscar|propecia", "Urology"),
    (r"sildenafil|viagra|revatio", "Urology"),
    (r"tadalafil|cialis|adcirca", "Urology"),
    (r"oxybutynin|ditropan", "Urology"),
    (r"solifenacin|vesicare", "Urology"),
    (r"tolterodine|detrol|detrusitol", "Urology"),
    (r"dutasteride|avodart", "Urology"),
    (r"alfuzosin|uroxatral|xatral", "Urology"),
    (r"doxazosin|cardura", "Urology"),
    (r"mirabegron|myrbetriq|betmiga", "Urology"),
    (r"latanoprost|xalatan|monopost", "Urology"),
    (r"timolol eye|timolol ophthalmic|timolol opd|timolol oph|timolol opt", "Eye/Ear"),
    (r"bimatoprost|lumigan", "Eye/Ear"),
    (r"travoprost|travatan", "Eye/Ear"),
    (r"dorzolamide|trusopt", "Eye/Ear"),
    (r"brimonidine|alphagan", "Eye/Ear"),
    (r"tobramycin|tobrex", "Eye/Ear"),
    (r"artificial tears|hypromellose|carmellose|lubricant eye|hydroxyethyl|polyvinyl|sodium hyaluronate", "Eye/Ear"),
    (r"adrenaline|epinephrine|epipen", "Emergency/Injection"),
    (r"diclofenac", "Emergency/Injection"),
    (r"vitamin b12|cyanocobalamin|hydroxocobalamin|methylcobalamin", "Emergency/Injection"),
    (r"allopurinol|zyloprim", "Osteoporosis/Gout"),
    (r"colchicine|colcrys", "Osteoporosis/Gout"),
    (r"alendronate|alendronic acid|fosamax", "Osteoporosis/Gout"),
    (r"risedronate|actonel", "Osteoporosis/Gout"),
    (r"zoledronic acid|zometa|aclasta", "Osteoporosis/Gout"),
    (r"probenecid", "Osteoporosis/Gout"),
    (r"febuxostat|uloric", "Osteoporosis/Gout"),
    (r"tretinoin|retin-a|retinoic acid|retinova", "Dermatology"),
    (r"isotretinoin|accutane|roaccutane|acnetane", "Dermatology"),
    (r"benzoyl peroxide|panoxyl|benzac|brevoxyl", "Dermatology"),
    (r"fusidic acid|fusidate|fucidin|fucithalmic", "Dermatology"),
    (r"permethrin|lyclear|nix|elimite", "Dermatology"),
    (r"calcipotriol|dovonex|daivonex", "Dermatology"),
    (r"clobetasol|temovate|dermovate", "Dermatology"),
    (r"ketoconazole|nizoral", "Dermatology"),
    (r"clotrimazole|canesten|lotremin", "Dermatology"),
    (r"miconazole|daktarin", "Dermatology"),
    (r"terbinafine|lamisil", "Dermatology"),
    (r"dapsone|aczone", "Dermatology"),
    (r"adapalene|differin", "Dermatology"),
    (r"azelaic acid|skinoren", "Dermatology"),
    (r"pimecrolimus|elidel", "Dermatology"),
    (r"tacrolimus|protopic", "Dermatology"),
    (r"nystatin|mycostatin", "Dermatology"),
    (r"coal tar|alphosyl", "Dermatology"),
    (r"urea cream|carbamide", "Dermatology"),
]

def get_category(text):
    text_lower = text.lower()
    for pattern, cat in DRUG_PATTERNS:
        if re.search(pattern, text_lower):
            return cat
    return None

def clean_desc(desc):
    criteria_words = [
        r"\s+Accepted treatment\s*$",
        r"\s+Clinical Review\s*$",
        r"\s+Clinical Motivation\s*$",
        r"\s+Specialist script\s*$",
        r"\s+Specialist motivation\s*$",
        r"\s+Special Investigations.*$",
        r"\s+SI\s+.*$",
        r"\s+Yes\s+Yes.*$",
        r"\s+No\s+No.*$",
        r"\s+Yes\s+No.*$",
        r"\s+CDL.*$",
        r"\s+PBR.*$",
        r"\s+Non-PBR.*$",
    ]
    for pattern in criteria_words:
        desc = re.sub(pattern, "", desc, flags=re.IGNORECASE)
    desc = re.sub(r"\s+", " ", desc).strip()
    return desc

basedir = r"d:\downloads\medicaregp_1"

# Parse GEMS Oct 2024 (most comprehensive)
def parse_gems_oct2024(filepath):
    results = {}
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    line_pattern = re.compile(r"^\s*\d+\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\S.*?)\s+\d+\s+R\s+[\d,]+")
    
    for line in lines:
        m = line_pattern.match(line)
        if not m:
            continue
        generic_desc = m.group(1).strip()
        nappi_code = int(m.group(2))
        product_name = m.group(3).strip()
        strength_form = m.group(4).strip()
        
        if nappi_code in EXISTING_CODES:
            continue
        if nappi_code in results:
            continue
        
        combined = generic_desc + " " + product_name + " " + strength_form
        cat = get_category(combined)
        if cat:
            desc = (product_name + " " + strength_form).strip()
            desc = clean_desc(desc)
            results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

# Parse GEMS Jan 2025 (formulary with brand + generic + strength + form)
def parse_gems_jan2025(filepath):
    results = {}
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Pattern: NAPPI BRAND GENERIC? STRENGTH FORM [criteria...]
    line_pattern = re.compile(r"^(\d{5,8})\s+(.+)$")
    
    for line in lines:
        line = line.strip()
        m = line_pattern.match(line)
        if not m:
            continue
        nappi_code = int(m.group(1))
        rest = m.group(2).strip()
        
        if nappi_code in EXISTING_CODES:
            continue
        if nappi_code in results:
            continue
        
        cat = get_category(rest)
        if cat:
            desc = clean_desc(rest)
            results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

# Parse Discovery 2025
def parse_discovery(filepath):
    results = {}
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        if re.match(r"^\d{5,8}$", parts[0]):
            nappi_code = int(parts[0])
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            rest = " ".join(parts[1:])
            cat = get_category(rest)
            if cat:
                desc_parts = []
                for p in parts[1:]:
                    if p in ("Yes", "No", "CDL", "PBR", "Non-PBR", "HIV", "Oncology"):
                        break
                    if re.match(r"^[\d.R,]+$", p) and len(p) > 3:
                        break
                    desc_parts.append(p)
                desc = " ".join(desc_parts)
                desc = clean_desc(desc)
                results[nappi_code] = {"code": str(nappi_code), "desc": desc, "category": cat}
    return results

# Parse Medimed
def parse_medimed(filepath):
    results = {}
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in lines:
        m = re.search(r"\b(\d{6,8})\d{3}\b", line)
        if m:
            nappi_code = int(m.group(1))
            if nappi_code in EXISTING_CODES:
                continue
            if nappi_code in results:
                continue
            cat = get_category(line)
            if cat:
                desc_line = re.sub(r"\s+\d{9,}\s+\d+\s+(YES|NO).*", "", line).strip()
                desc_line = clean_desc(desc_line)
                results[nappi_code] = {"code": str(nappi_code), "desc": desc_line, "category": cat}
    return results

all_results = {}

print("Parsing GEMS Oct 2024...")
r1 = parse_gems_oct2024(os.path.join(basedir, "extracted_GEMS_Oct2024.txt"))
print(f"  Found {len(r1)} entries")
all_results.update(r1)

print("Parsing GEMS Jan 2025...")
r2 = parse_gems_jan2025(os.path.join(basedir, "extracted_GEMS_Jan2025.txt"))
print(f"  Found {len(r2)} entries")
for k, v in r2.items():
    if k not in all_results:
        all_results[k] = v

print("Parsing Discovery 2025...")
r3 = parse_discovery(os.path.join(basedir, "extracted_Discovery2025.txt"))
print(f"  Found {len(r3)} entries")
for k, v in r3.items():
    if k not in all_results:
        all_results[k] = v

print("Parsing Medimed...")
r4 = parse_medimed(os.path.join(basedir, "extracted_Medimed.txt"))
print(f"  Found {len(r4)} entries")
for k, v in r4.items():
    if k not in all_results:
        all_results[k] = v

final_list = sorted(all_results.values(), key=lambda x: x["category"] + x["desc"])
print(f"\nTotal unique new entries: {len(final_list)}")

from collections import Counter
cats = Counter(v["category"] for v in final_list)
for cat, cnt in sorted(cats.items()):
    print(f"  {cat}: {cnt}")

# Spot-check specific drugs
print("\n--- Spot checks ---")
for term in ["tiotropium", "tamsulosin", "latanoprost", "adrenaline", "tretinoin", "liraglutide", "GTN", "isosorbide"]:
    matches = [item for item in final_list if term.lower() in item["desc"].lower()]
    print(f"{term}: {len(matches)} entries")
    for m in matches[:2]:
        print(f"  {m['code']} | {m['desc']}")

out_path = os.path.join(basedir, "nappi_codes_final2.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(final_list, f, indent=2, ensure_ascii=False)
print(f"\nSaved {len(final_list)} entries to {out_path}")
