import json

with open(r"d:\downloads\medicaregp_1\nappi_codes_final2.json") as f:
    data = json.load(f)

cotrim_codes = [779881, 894842, 705259, 793310, 758221, 706434, 773603, 716731, 721751, 704095, 735698]
for code in cotrim_codes:
    match = next((item for item in data if item["code"] == str(code)), None)
    if match:
        print(f"FOUND {code}: {match['desc']}")
    else:
        print(f"MISSING {code}")
