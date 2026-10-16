"""Downloads real government / university agronomy documents into data/pdfs.
File names are  <crop>__<source>.pdf  - the crop prefix is used for filtering ('multi' = many crops).
Run:  python scripts/download_data.py
URLs that fail are listed at the end - download those by hand and save with the same naming."""
import os
import requests

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "pdfs")
os.makedirs(OUT, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Confirmed sources
TNAU = "https://agritech.tnau.ac.in/horticulture/pdf/tech_bulletin/national/"
FIXED = [
    ("banana__tnau_ipm.pdf", [TNAU + "IPM-Banana-Revised-Sept2011.pdf"]),
    ("citrus__tnau_ipm.pdf", [TNAU + "IPM-CITRUS-Revised-May2011.pdf"]),
    ("guava__tnau_ipm.pdf", [TNAU + "IPM-GUAVA-Revised-Sept2011.pdf"]),
    ("mango__tnau_ipm.pdf", [TNAU + "IPM-Mango-Revised-Sept2011.pdf"]),
    ("amla__tnau_ipm.pdf", [TNAU + "IPM_Amla_Pest_Revised-sep2011.pdf"]),
    ("multi__tnau_ipm_vegetables.pdf", [TNAU + "IPM-Schedule-for-vegetables.pdf"]),
    ("multi__tnau_crop_production_guide.pdf", ["https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf"]),
    ("rice__fao_integrated_crop_management.pdf", ["https://www.fao.org/3/cc1163en/cc1163en.pdf"]),
    ("soybean__niphm_ipm_package.pdf", ["https://niphm.gov.in/IPMPackages/Soyabean.pdf"]),
    ("multi__tnau_horticulture_guide.pdf", ["https://agritech.tnau.ac.in/pdf/HORTICULTURE.pdf"]),

]


# DPPQS/NIPHM IPM packages (87 crops exist). File names are tried at both known locations;
# some names may differ, any miss is reported below.
IPM = {
    "rice": "Rice", "wheat": "Wheat", "maize": "Maize", "sorghum": "Sorghum",
    "cotton": "Cotton", "groundnut": "Groundnut", "chickpea": "Gram", "tur": "Red gram",
    "blackgram": "Black gram", "greengram": "Green gram", "mustard": "Rapeseed and Mustard",
    "sunflower": "Sunflower", "sugarcane": "Sugarcane", "tomato": "Tomato", "onion": "Onion",
    "potato": "Potato", "brinjal": "Brinjal", "chilli": "Chilli", "okra": "Okra",
}
for crop, name in IPM.items():
    FIXED.append((f"{crop}__niphm_ipm_package.pdf", [
        f"https://niphm.gov.in/IPMPackages/{name}.pdf",
        f"http://ppqs.gov.in/PDF/Revised IPM POP/{name}.pdf",
    ]))


def fetch(urls, dest):
    for u in urls:
        try:
            r = requests.get(u, headers=H, timeout=60)
            if r.ok and r.content[:5] == b"%PDF-":
                with open(dest, "wb") as f:
                    f.write(r.content)
                return u, len(r.content)
        except Exception as e:
            print("   error:", type(e).__name__, u)
    return None, 0


failed = []
for fname, urls in FIXED:
    dest = os.path.join(OUT, fname)
    if os.path.exists(dest):
        print("exists  ", fname)
        continue
    url, size = fetch(urls, dest)
    if url:
        print(f"ok      {fname}  ({size/1e6:.1f} MB)")
    else:
        print("MISSING ", fname)
        failed.append((fname, urls))

print("\n=== Download these by hand (save into data/pdfs with this name) ===")
for fname, urls in failed:
    print(fname, "<-", urls[0])
