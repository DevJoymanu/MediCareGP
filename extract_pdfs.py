import pdfplumber
import sys
import os

tool_path = r"C:\Users\Mr Emmanuel\.claude\projects\d--downloads-medicaregp-1\b01925f3-9bfd-45ad-a94d-17f640e1030e\tool-results"
pdfs = [
    "webfetch-1780003909133-t6t5z9.pdf",
    "webfetch-1780003913522-92tgs2.pdf",
    "webfetch-1780003919253-vk5rh5.pdf",
    "webfetch-1780003924132-dsw8t9.pdf",
    "webfetch-1780003930957-1qcsa1.pdf",
]

labels = ["GEMS_Jan2025", "GEMS_Oct2024", "Discovery2025", "Medimed", "MMI_GEMS_tariff"]

for i, pdf in enumerate(pdfs):
    path = os.path.join(tool_path, pdf)
    out_path = os.path.join(r"d:\downloads\medicaregp_1", f"extracted_{labels[i]}.txt")
    print(f"Processing {labels[i]}...")
    try:
        with pdfplumber.open(path) as doc:
            total_pages = len(doc.pages)
            print(f"  {total_pages} pages")
            with open(out_path, "w", encoding="utf-8") as f:
                for j, page in enumerate(doc.pages):
                    text = page.extract_text()
                    if text:
                        f.write(text + "\n")
                    if (j+1) % 50 == 0:
                        print(f"  Page {j+1}/{total_pages}")
        size = os.path.getsize(out_path)
        print(f"  Saved {size} bytes to {out_path}")
    except Exception as e:
        print(f"  ERROR: {e}")
print("Done")
