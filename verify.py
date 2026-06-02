import json
import re

with open(r"d:\downloads\medicaregp_1\nappi_codes_final2.json") as f:
    data = json.load(f)

# Look for specific codes and terms
specific_codes = [714152, 702526, 716778, 840599, 720971, 833223, 842605, 874752, 760242, 718715, 706713]
for code in specific_codes:
    match = next((item for item in data if item["code"] == str(code)), None)
    if match:
        print(f"FOUND {code}: {match}")
    else:
        print(f"MISSING code {code}")

print("\n--- Category search for tiotropium ---")
for item in data:
    if "tiotropium" in item["desc"].lower() or "spiriva" in item["desc"].lower() or "forvent" in item["desc"].lower():
        print(f"  {item['code']}: {item['desc']}")

print("\n--- Category search for tamsulosin ---")
for item in data:
    if "tamsulosin" in item["desc"].lower() or "flomax" in item["desc"].lower() or "beniprosin" in item["desc"].lower() or "uromax" in item["desc"].lower():
        print(f"  {item['code']}: {item['desc']}")

print("\n--- Category search for latanoprost ---")
for item in data:
    if "latanoprost" in item["desc"].lower() or "xalatan" in item["desc"].lower() or "atana" in item["desc"].lower():
        print(f"  {item['code']}: {item['desc']}")

print("\n--- Category search for tretinoin ---")
for item in data:
    if "tretinoin" in item["desc"].lower() or "retin" in item["desc"].lower() or "ilotycin" in item["desc"].lower():
        print(f"  {item['code']}: {item['desc']}")
