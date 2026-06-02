import re

DRUG_PATTERNS_UROLOGY = [
    (r"\btamsulosin\b", "Urology"),
]
DRUG_PATTERNS_RESP = [
    (r"\btiotropium\b", "Respiratory"),
]

test = [
    "TAMSULOSIN .4MG BENIPROSIN SR .4MG SRC",
    "TIOTROPIUM BROMIDE 18MCG CPS FORVENT (REFILL) 18MCG CPS",
]
for t in test:
    for pattern, cat in DRUG_PATTERNS_UROLOGY + DRUG_PATTERNS_RESP:
        m = re.search(pattern, t, re.IGNORECASE)
        if m:
            print(f"MATCH [{cat}]: '{pattern}' in '{t[:50]}'")
        else:
            print(f"NO MATCH: '{pattern}' in '{t[:50]}'")
