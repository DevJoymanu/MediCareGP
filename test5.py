import re

# Test the Oct 2024 line_pattern on tiotropium lines
lines = [
    "1637 TIOTROPIUM BROMIDE 18MCG CPS 714152 FORVENT (REFILL) 18MCG CPS 30 R 325.57 R 374.41",
    "1638 TIOTROPIUM BROMIDE 18MCG KIT 714167 FORVENT HANDIHALER COMPLETE WITH 301 INH 18MCG KITR 584.24 R 671.88",
    "1623 TAMSULOSIN .4MG 716778 BENIPROSIN SR .4MG SRC 30 R 188.48 R 216.75",
    "2105 LATANOPROST 720971 ATANA 2.5ML 50MCG/1ML OPD 1 R 172.80 R 198.72",
    "1653 TRETINOIN CREAM .5MG/1G 842605 ILOTYCIN-A .5MG/1G CRE 20 R 261.99 R 301.29",
]

# old pattern (with space before R)
p1 = re.compile(r"^\s*\d+\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\S.*?)\s+\d+\s+R\s+[\d,]+")

for line in lines:
    m = p1.match(line)
    if m:
        generic_desc = m.group(1).strip()
        nappi_code = int(m.group(2))
        product_name = m.group(3).strip()
        strength_form = m.group(4).strip()
        combined = generic_desc + " " + product_name + " " + strength_form
        
        # Check category
        hits = []
        for pattern in [r"tiotropium", r"tamsulosin", r"latanoprost", r"tretinoin"]:
            if re.search(pattern, combined, re.IGNORECASE):
                hits.append(pattern)
        
        print(f"MATCH: nappi={nappi_code}, gen='{generic_desc[:30]}', prod='{product_name[:20]}', str='{strength_form[:15]}'")
        print(f"  combined hits: {hits}")
    else:
        print(f"NO MATCH: {line[:80]}")
