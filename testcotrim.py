import re

# Test pattern matching
patterns = [
    (r"co-trimoxazole|cotrimoxazole|sulfamethoxazole|trimethoprim.sulfamethox", "Antibiotics"),
]

lines = [
    "1296 CO TRIMOXAZOLE 240MG/5ML 779881 CO-TRIM 240MG/5ML SUS 50 R 6.19 R 7.12",
    "1969 CO TRIMOXAZOLE 480MG 706434 BACTRIM ADULT 480MG TAB 500 R 222.00 R 255.30",
    "1298 CO TRIMOXAZOLE 960MG 706442 BACTRIM DS 960MG TAB 30 R 42.67 R 49.07",
]

line_pattern = re.compile(r"^\s*\d+\s+(.+?)\s+(\d{5,8})\s+(.+?)\s+(\S.*?)\s+\d+\s+R\s+[\d,]+")

for line in lines:
    m = line_pattern.match(line)
    if m:
        g = m.group(1)
        nappi = m.group(2)
        brand = m.group(3)
        strength = m.group(4)
        combined = g + " " + brand + " " + strength
        print(f"PARSE OK: nappi={nappi}, generic='{g}', brand='{brand}'")
        for p, cat in patterns:
            match = re.search(p, combined, re.IGNORECASE)
            if match:
                print(f"  PATTERN MATCH [{cat}]: '{p}'")
            else:
                print(f"  NO PATTERN MATCH: '{p}' on combined='{combined[:50]}'")
    else:
        print(f"LINE PATTERN FAIL: {line[:80]}")
