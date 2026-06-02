import re

# Test the pattern matching on sample lines
test_lines = [
    "1637 TIOTROPIUM BROMIDE 18MCG CPS 714152 FORVENT (REFILL) 18MCG CPS 30 R 325.57 R 374.41",
    "1623 TAMSULOSIN .4MG 716778 BENIPROSIN SR .4MG SRC 30 R 188.48 R 216.75",
    "1623 TAMSULOSIN .4MG 840599 FLOMAX SR .4MG SRC 30 R 188.48 R 216.75",
]

# Current pattern
line_pattern = re.compile(r"^\s*(\d+)\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\w.*?)\s+(\d+)\s+R\s+[\d,]+")

for line in test_lines:
    m = line_pattern.match(line)
    if m:
        print(f"MATCH: groups={m.groups()[:4]}")
    else:
        print(f"NO MATCH: {line[:80]}")
