import re

# Test exact parsing with the line_pattern
line_pattern = re.compile(r"^\s*(\d+)\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\w.*?)\s+(\d+)\s+R\s+[\d,]+")

test_lines = [
    "1637 TIOTROPIUM BROMIDE 18MCG CPS 714152 FORVENT (REFILL) 18MCG CPS 30 R 325.57 R 374.41",
    "1637 TIOTROPIUM BROMIDE 18MCG CPS 702526 SPIRIVA (REFILL) 18MCG CPS 30 R 325.57 R 374.41",
    "1623 TAMSULOSIN .4MG 716778 BENIPROSIN SR .4MG SRC 30 R 188.48 R 216.75",
    "1638 TIOTROPIUM BROMIDE 18MCG KIT 714167 FORVENT HANDIHALER COMPLETE WITH 301 INH 18MCG KITR 584.24 R 671.88",
]

for line in test_lines:
    m = line_pattern.match(line)
    if m:
        g = m.group(2)  # generic desc
        nappi = int(m.group(3))
        brand = m.group(4)
        strength = m.group(5)
        print(f"OK: NAPPI={nappi}, generic='{g}', brand='{brand}', strength='{strength}'")
        combined = f"{g} {brand} {strength}"
        has_tio = bool(re.search(r"\btiotropium\b", combined, re.IGNORECASE))
        has_tam = bool(re.search(r"\btamsulosin\b", combined, re.IGNORECASE))
        print(f"   tiotropium match: {has_tio}, tamsulosin match: {has_tam}")
    else:
        print(f"NO MATCH for: {line[:80]}")
