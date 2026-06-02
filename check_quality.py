import json
with open(r"d:\downloads\medicaregp_1\nappi_codes_extracted.json") as f:
    data = json.load(f)

from collections import defaultdict
cats = defaultdict(list)
for item in data:
    cats[item["category"]].append(item)

for cat in sorted(cats.keys()):
    print("\n=== " + cat + " (first 8) ===")
    for item in cats[cat][:8]:
        print("  " + item["code"] + " | " + item["desc"])
