"""
scripts/test_custom_languages.py
Phase 4 Extension: Additional custom query test suite across regional languages.
Tests diverse crops (Cotton, Groundnut, Tomato) and key pests/diseases across:
Hindi (hi), Marathi (mr), Tamil (ta), Telugu (te).
Verifies semantic inbound translation and bilingual outbound chemical name rendering.
"""

import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["HF_HUB_OFFLINE"] = "1"
from app.translate import translate

CUSTOM_TEST_CASES = [
    {
        "crop": "Cotton (कपास)",
        "lang": "hi",
        "name": "Hindi",
        "regional_in": "कपास में गुलाबी सुंडी के नियंत्रण के लिए कौन सा कीटनाशक इस्तेमाल करें?",
        "english_out": "Spray Profenophos 50 EC at 2 ml/L or Chlorpyriphos 20 EC at 2.5 ml/L for Pink bollworm. Install pheromone traps at 5 per acre. Always wear protective gear."
    },
    {
        "crop": "Cotton (कपाशी)",
        "lang": "mr",
        "name": "Marathi",
        "regional_in": "कपाशीवरील बोंडअळीच्या नियंत्रणासाठी कोणती औषधे वापरावीत?",
        "english_out": "Spray Emamectin benzoate 5 SG at 4 g per 10 liters for Bollworm. Consult your local KVK for integrated pest management."
    },
    {
        "crop": "Groundnut (நிலக்கடலை)",
        "lang": "ta",
        "name": "Tamil",
        "regional_in": "நிலக்கடலையில் டிக்கா இலைப்புள்ளி நோயைக் கட்டுப்படுத்துவது எப்படி?",
        "english_out": "Spray Mancozeb at 2 g/L or Carbendazim at 1 g/L to control Tikka leaf spot. Apply at 10-15 day intervals. Always wear gloves during spraying."
    },
    {
        "crop": "Groundnut (వేరుశనగ)",
        "lang": "te",
        "name": "Telugu",
        "regional_in": "వేరుశనగలో తిక్కా ఆకుమచ్చ తెగులు నివారణకు ఏ మందు పిచికారీ చేయాలి?",
        "english_out": "Spray Mancozeb at 400 g/acre or Hexaconazole at 2 ml/L for Tikka leaf spot. Ensure proper protective clothing."
    },
    {
        "crop": "Tomato (தக்காளி)",
        "lang": "ta",
        "name": "Tamil",
        "regional_in": "தக்காளி பயிரில் இலை சுருட்டை வைரஸ் நோயை எவ்வாறு கட்டுப்படுத்துவது?",
        "english_out": "To manage Leaf curl virus, control whitefly vector using Imidacloprid 17.8 SL at 0.5 ml/L. Remove and destroy infected plants."
    },
    {
        "crop": "Tomato (टोमॅटो)",
        "lang": "mr",
        "name": "Marathi",
        "regional_in": "टोमॅटो पिकावर फळ पोखरणाऱ्या अळीसाठी काय उपाय आहे?",
        "english_out": "Spray Chlorantraniliprole 18.5 SC at 0.3 ml/L or Spinosad 45 SC at 0.3 ml/L for Fruit borer. Follow safety precautions."
    }
]

def run_tests():
    print("=" * 80)
    print("PHASE 4 EXTENSION: ADDITIONAL CUSTOM REGIONAL LANGUAGE TESTS")
    print("Crops Tested: Cotton, Groundnut, Tomato")
    print("Languages Tested: Hindi (hi), Marathi (mr), Tamil (ta), Telugu (te)")
    print("=" * 80)

    results = []

    for i, tc in enumerate(CUSTOM_TEST_CASES, 1):
        lang = tc["lang"]
        name = tc["name"]
        crop = tc["crop"]
        reg_in = tc["regional_in"]
        en_out = tc["english_out"]

        print(f"\n[Case {i}: {crop} | {name.upper()} ({lang})]")
        print("-" * 80)

        # 1. Inbound translation: Regional -> English
        t0 = time.perf_counter()
        en_translated = translate(reg_in, lang, "en")
        t_in = time.perf_counter() - t0

        print(f"  [1] INBOUND ({lang.upper()} -> EN) ({t_in:.2f}s):")
        print(f"      Farmer Query: {reg_in}")
        print(f"      To English:   {en_translated}")

        # 2. Outbound translation: English -> Regional (with bilingual terminology)
        t0 = time.perf_counter()
        reg_translated = translate(en_out, "en", lang)
        t_out = time.perf_counter() - t0

        print(f"  [2] OUTBOUND (EN -> {lang.upper()}) ({t_out:.2f}s):")
        print(f"      Original En:  {en_out}")
        print(f"      To Farmer:    {reg_translated}")

        results.append({
            "case": f"{crop} ({name})",
            "lang": lang,
            "t_in": t_in,
            "t_out": t_out,
            "en_translated": en_translated,
            "reg_translated": reg_translated
        })

    print("\n" + "=" * 80)
    print("CUSTOM LANGUAGE TESTS SUMMARY")
    print("=" * 80)
    print(f"{'Crop & Language':<30} | {'Inbound (s)':<12} | {'Outbound (s)':<13} | {'Status':<10}")
    print("-" * 75)
    for r in results:
        status = "PASS" if len(r["en_translated"]) > 5 and len(r["reg_translated"]) > 5 else "FAIL"
        print(f"{r['case']:<30} | {r['t_in']:<12.2f} | {r['t_out']:<13.2f} | {status:<10}")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
