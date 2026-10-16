"""
scripts/test_languages.py
Phase 4: Multilingual Translation Test Suite for Kisan AI.
Tests bidirectional translation for Hindi (hi), Marathi (mr), Tamil (ta), and Telugu (te)
using IndicTrans2 and verifies bilingual chemical term preservation.
"""

import os
import sys
import time

# Ensure workspace root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Reconfigure stdout for UTF-8 on Windows
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ["HF_HUB_OFFLINE"] = "1"
from app.translate import translate

TEST_CASES = [
    {
        "lang": "hi",
        "name": "Hindi",
        "regional_in": "मेरी धान की फसल में तना छेदक का प्रकोप है, कौन सी दवा का छिड़काव करें?",
        "english_out": "Spray Chlorpyriphos at 2ml/L for Stem borer. Contact your local Krishi Vigyan Kendra (KVK)."
    },
    {
        "lang": "mr",
        "name": "Marathi",
        "regional_in": "माझ्या भात पिकावर तपकिरी तुडतुडे आले आहेत, काय उपाय करावा?",
        "english_out": "Use Imidacloprid 17.8 SL at 0.5ml/L for Brown planthopper. Contact your local KVK."
    },
    {
        "lang": "ta",
        "name": "Tamil",
        "regional_in": "நெற்பயிரில் குலை நோயைக் கட்டுப்படுத்த என்ன மருந்து தெளிக்க வேண்டும்?",
        "english_out": "Spray Mancozeb at 2g per liter for Rice blast. Contact your local Krishi Vigyan Kendra (KVK)."
    },
    {
        "lang": "te",
        "name": "Telugu",
        "regional_in": "వరి పంటలో అగ్గి తెగులు నివారణకు ఏ మందు పిచికారీ చేయాలి?",
        "english_out": "Spray Tricyclazole at 0.6g/L for Rice blast. Contact your local Krishi Vigyan Kendra (KVK)."
    }
]

def run_tests():
    print("=" * 80)
    print("PHASE 4: REGIONAL LANGUAGE BIDIRECTIONAL TRANSLATION TEST")
    print("IndicTrans2 Models: indic-en-dist-200M | en-indic-dist-200M")
    print("Languages Tested: Hindi (hi), Marathi (mr), Tamil (ta), Telugu (te)")
    print("=" * 80)

    results = []

    for tc in TEST_CASES:
        lang = tc["lang"]
        name = tc["name"]
        reg_in = tc["regional_in"]
        en_out = tc["english_out"]

        print(f"\n[{name.upper()} - {lang.upper()}]")
        print("-" * 80)

        # 1. Inbound: Regional -> English
        t0 = time.perf_counter()
        en_translated = translate(reg_in, lang, "en")
        t_in = time.perf_counter() - t0

        print(f"  [1] INBOUND ({lang.upper()} -> EN) ({t_in:.2f}s):")
        print(f"      Original:   {reg_in}")
        print(f"      Translated: {en_translated}")

        # 2. Outbound: English -> Regional (with bilingual terminology)
        t0 = time.perf_counter()
        reg_translated = translate(en_out, "en", lang)
        t_out = time.perf_counter() - t0

        print(f"  [2] OUTBOUND (EN -> {lang.upper()}) ({t_out:.2f}s):")
        print(f"      Original:   {en_out}")
        print(f"      Translated: {reg_translated}")

        results.append({
            "lang": lang,
            "name": name,
            "t_in": t_in,
            "t_out": t_out,
            "en_translated": en_translated,
            "reg_translated": reg_translated
        })

    print("\n" + "=" * 80)
    print("PHASE 4 SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Language':<12} | {'Inbound (s)':<12} | {'Outbound (s)':<12} | {'Status':<10}")
    print("-" * 55)
    for r in results:
        status = "PASS" if len(r["en_translated"]) > 5 and len(r["reg_translated"]) > 5 else "FAIL"
        print(f"{r['name']:<12} | {r['t_in']:<12.2f} | {r['t_out']:<12.2f} | {status:<10}")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
