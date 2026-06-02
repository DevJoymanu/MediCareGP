import re
import json

with open(r"d:\downloads\medicaregp_1\nappi_codes_final2.json") as f:
    data = json.load(f)

# Fix categorizations
fix_count = 0
for item in data:
    desc_lower = item["desc"].lower()
    
    # Eye/Ear corrections - latanoprost/timolol ophthalmic
    if item["category"] == "Urology":
        if any(x in desc_lower for x in ["opd", "oph", "eye", "ocular", ".3%", "0.3%", "ophthalmic",
                                           "atana", "xalatan", "aglatan", "co-atana", "xalacom",
                                           "vyzulta", "lumigan", "travatan", "azarga", "azopt",
                                           "atimol", "timolol", "xalacom", "latanoprost", "bimatoprost"]):
            item["category"] = "Eye/Ear"
            fix_count += 1
    
    # Emergency/Injection corrections
    if item["category"] in ("Cardiovascular", "Hormones", "Antibiotics", "GI"):
        if any(x in desc_lower for x in ["adrenalin", "epinephrin", "epipen", "jext"]):
            item["category"] = "Emergency/Injection"
            fix_count += 1
        elif "ceftriaxone" in desc_lower and any(x in desc_lower for x in ["inj", "inf", "vial", "amp"]):
            item["category"] = "Emergency/Injection"
            fix_count += 1
        elif "ondansetron" in desc_lower and any(x in desc_lower for x in ["inj", "amp", "ivp", "1ml", "2ml", "4ml"]):
            item["category"] = "Emergency/Injection"
            fix_count += 1
        elif "diclofenac" in desc_lower and any(x in desc_lower for x in ["inj", "amp", "ivp"]):
            item["category"] = "Emergency/Injection"
            fix_count += 1

print(f"Fixed {fix_count} categorizations")

# Improve descriptions by adding generic name where it's just a brand name
# Load the Oct2024 data for generic names
with open(r"d:\downloads\medicaregp_1\extracted_GEMS_Oct2024.txt", "r", encoding="utf-8") as f:
    oct_lines = f.readlines()

# Build NAPPI -> generic_name mapping from Oct 2024
line_pattern = re.compile(r"^\s*\d+\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\S.*?)\s+\d+\s+R\s+[\d,]+")
nappi_to_generic = {}
for line in oct_lines:
    m = line_pattern.match(line)
    if m:
        generic = m.group(1).strip()
        nappi = str(int(m.group(2)))
        nappi_to_generic[nappi] = generic

print(f"Generic name lookup has {len(nappi_to_generic)} entries")

# Enhance descriptions
enhanced = 0
for item in data:
    code = item["code"]
    if code in nappi_to_generic:
        generic = nappi_to_generic[code]
        # Only add generic if it's not already in description and meaningful
        if len(generic) > 3 and generic.upper() not in item["desc"].upper():
            # Clean generic
            generic_clean = re.sub(r"\s+\d+MG.*$", "", generic).strip()
            if len(generic_clean) > 3:
                item["desc"] = item["desc"] + " [" + generic + "]"
                enhanced += 1

print(f"Enhanced {enhanced} descriptions with generic names")

# Final dedup and sort
seen = {}
for item in data:
    code = item["code"]
    if code not in seen:
        seen[code] = item

final_list = sorted(seen.values(), key=lambda x: x["category"] + x["desc"])
print(f"\nFinal count: {len(final_list)}")

from collections import Counter
cats = Counter(v["category"] for v in final_list)
for cat, cnt in sorted(cats.items()):
    print(f"  {cat}: {cnt}")

with open(r"d:\downloads\medicaregp_1\nappi_codes_final2.json", "w", encoding="utf-8") as f:
    json.dump(final_list, f, indent=2, ensure_ascii=False)
print("Saved final JSON")

# Show sample for each important target drug  
print("\n--- Samples for requested drugs ---")
targets = {
    "ramipril": "ramipril",
    "warfarin": "warfarin",
    "rivaroxaban": "rivaroxaban",
    "apixaban": "apixaban",
    "metformin XR": "metformin xr",
    "glimepiride": "glimepiride",
    "insulin glargine": "insulin glargine",
    "tiotropium": "tiotropium",
    "ondansetron": "ondansetron",
    "quetiapine": "quetiapine",
    "dolutegravir": "dolutegravir",
    "tamsulosin": "tamsulosin",
    "latanoprost": "latanoprost",
    "allopurinol": "allopurinol",
    "tretinoin": "tretinoin",
    "co-trimoxazole": "co-trimoxazole",
    "liraglutide": "liraglutide",
    "lamotrigine": "lamotrigine",
    "pregabalin": "pregabalin",
    "ceftriaxone": "ceftriaxone",
}
for name, term in targets.items():
    matches = [item for item in final_list if term.lower() in item["desc"].lower()]
    print(f"\n{name}: {len(matches)} entries")
    for m in matches[:3]:
        print(f"  {m['code']} | {m['desc'][:80]}")
