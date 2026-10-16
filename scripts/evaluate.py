import os
import sys
import csv
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Ensure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.pipeline import run_pipeline_timed
from app.db import init_db

# 30 Curated Evaluation Questions
QUESTIONS = [
    # 1-8: Well-covered crops
    {"id": 1, "crop": "rice", "cat": "well_covered", "lang": "en", "q": "What chemical spray should I use for rice blast disease, and at what dosage?"},
    {"id": 2, "crop": "mango", "cat": "well_covered", "lang": "en", "q": "How to manage anthracnose disease in mango fruits?"},
    {"id": 3, "crop": "cotton", "cat": "well_covered", "lang": "en", "q": "What is the recommended control for pink bollworm in cotton?"},
    {"id": 4, "crop": "banana", "cat": "well_covered", "lang": "en", "q": "How do I control Panama wilt in banana?"},
    {"id": 5, "crop": "citrus", "cat": "well_covered", "lang": "en", "q": "What is the treatment for citrus canker?"},
    {"id": 6, "crop": "chilli", "cat": "well_covered", "lang": "en", "q": "How to manage leaf curl virus and thrips in chilli?"},
    {"id": 7, "crop": "tomato", "cat": "well_covered", "lang": "en", "q": "What fungicide should I spray for early blight in tomato?"},
    {"id": 8, "crop": "groundnut", "cat": "well_covered", "lang": "en", "q": "What is the treatment for tikka leaf spot in groundnut?"},

    # 9-12: Thin-coverage crops
    {"id": 9, "crop": "onion", "cat": "thin_coverage", "lang": "en", "q": "What is the control for purple blotch in onion?"},
    {"id": 10, "crop": "gerbera", "cat": "thin_coverage", "lang": "en", "q": "How to manage powdery mildew in gerbera?"},
    {"id": 11, "crop": "cardamom", "cat": "thin_coverage", "lang": "en", "q": "How to control capsule rot or azhukal disease in cardamom?"},
    {"id": 12, "crop": "safflower", "cat": "thin_coverage", "lang": "en", "q": "What is the recommended treatment for aphid infestation in safflower?"},

    # 13-15: Not covered crops (Expect KVK fallback)
    {"id": 13, "crop": "saffron", "cat": "not_covered", "lang": "en", "q": "How to cure corm rot in saffron?"},
    {"id": 14, "crop": "apple", "cat": "not_covered", "lang": "en", "q": "How to manage apple scab disease?"},
    {"id": 15, "crop": "barley", "cat": "not_covered", "lang": "en", "q": "How to control stripe rust in barley?"},

    # 16-20: Multilingual equivalent queries (Brown planthopper in rice)
    {"id": 16, "crop": "rice", "cat": "multilingual", "lang": "en", "q": "How to manage brown planthopper in rice crop?"},
    {"id": 17, "crop": "rice", "cat": "multilingual", "lang": "hi", "q": "धान की फसल में भूरा फुदका कीट का नियंत्रण कैसे करें?"},
    {"id": 18, "crop": "rice", "cat": "multilingual", "lang": "mr", "q": "भातावरील तपकिरी तुडतुडे किडीचे नियंत्रण कसे करावे?"},
    {"id": 19, "crop": "rice", "cat": "multilingual", "lang": "ta", "q": "நெற்பயிரில் பழுப்பு தத்துப்பூச்சி மேலாண்மை செய்வது எப்படி?"},
    {"id": 20, "crop": "rice", "cat": "multilingual", "lang": "te", "q": "వరి పంటలో సుడి దోమ నివారణ ఎలా చేయాలి?"},

    # 21-30: Practical agronomy & tool scenarios
    {"id": 21, "crop": "rice", "cat": "weather_advisory", "lang": "en", "q": "It is raining heavily today. Can I spray fungicide for rice sheath blight?"},
    {"id": 22, "crop": "multi", "cat": "soil_management", "lang": "en", "q": "My soil pH is 5.2. How should I adjust it for growing vegetables?"},
    {"id": 23, "crop": "pulses", "cat": "biocontrol", "lang": "en", "q": "How to use Trichoderma viride for pulse seed treatment?"},
    {"id": 24, "crop": "rice", "cat": "biocontrol", "lang": "en", "q": "What is the dosage of Pseudomonas fluorescens for seedling root dip in rice?"},
    {"id": 25, "crop": "multi", "cat": "botanical", "lang": "en", "q": "How do I prepare and apply 5% Neem Seed Kernel Extract (NSKE) for caterpillars?"},
    {"id": 26, "crop": "banana", "cat": "fertilizer", "lang": "en", "q": "What is the recommended NPK fertilizer schedule for banana?"},
    {"id": 27, "crop": "cotton", "cat": "fertilizer", "lang": "en", "q": "What fertilizer dose is recommended for irrigated cotton?"},
    {"id": 28, "crop": "tomato", "cat": "stage_specific", "lang": "en", "q": "My tomato plants are at flowering stage. How to manage fruit borer?"},
    {"id": 29, "crop": "rice", "cat": "threshold_etl", "lang": "en", "q": "What is the economic threshold level for stem borer in rice?"},
    {"id": 30, "crop": "safety", "cat": "safety_precautions", "lang": "en", "q": "What precautions should I take when handling and spraying chemical pesticides?"},
]


def count_words(text: str) -> int:
    return len(text.strip().split())


def count_steps(text: str) -> int:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    step_count = sum(1 for line in lines if line[0].isdigit() and (line[1:3].startswith(".") or line[1:3].startswith(")")))
    return step_count


def run_evaluation(limit: int = None, ids: list[int] = None, output_csv: str = None):
    init_db()
    if output_csv is None:
        output_csv = os.path.join(ROOT, "scripts", "eval_results.csv")

    if ids:
        test_set = [q for q in QUESTIONS if q["id"] in ids]
    elif limit:
        test_set = QUESTIONS[:limit]
    else:
        test_set = QUESTIONS

    print("=" * 80, flush=True)
    print(f"RUNNING KISAN AI EVALUATION ({len(test_set)} queries)", flush=True)
    print(f"Target Output: {output_csv}", flush=True)
    print("=" * 80, flush=True)

    results = []
    fieldnames = [
        "id", "crop", "category", "language", "question",
        "answer", "words", "steps",
        "translate_in_s", "agent_s", "translate_out_s", "total_s",
        "pass_under_30s", "pass_under_100w", "pass_max_6steps", "kvk_fallback"
    ]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        f.flush()

        for item in test_set:
            qid = item["id"]
            lang = item["lang"]
            q = item["q"]
            crop = item["crop"]
            cat = item["cat"]
            phone = f"919876543{qid:03d}"

            print(f"\n[{qid}/{len(test_set)}] [{cat.upper()}] ({lang.upper()}) {q}", flush=True)

            try:
                ans, timings = run_pipeline_timed(phone=phone, text=q, in_lang=lang)
            except Exception as e:
                ans = f"ERROR: {e}"
                timings = {"translate_in": 0.0, "agent": 0.0, "translate_out": 0.0, "total": 0.0}

            words = count_words(ans)
            steps = count_steps(ans)
            is_kvk = "Krishi Vigyan Kendra" in ans or "KVK" in ans or "வேளாண் அறிவியல் மையம்" in ans or "कृषी विज्ञान केंद्र" in ans or "కేవీకే" in ans

            row = {
                "id": qid,
                "crop": crop,
                "category": cat,
                "language": lang,
                "question": q,
                "answer": ans.replace("\n", " "),
                "words": words,
                "steps": steps,
                "translate_in_s": timings["translate_in"],
                "agent_s": timings["agent"],
                "translate_out_s": timings["translate_out"],
                "total_s": timings["total"],
                "pass_under_30s": timings["total"] < 30.0,
                "pass_under_100w": words <= 100,
                "pass_max_6steps": steps <= 6,
                "kvk_fallback": is_kvk,
            }

            writer.writerow(row)
            f.flush()
            results.append(row)

            print(f"  --> Answer: {ans}", flush=True)
            print(f"  --> Words: {words} | Steps: {steps} | Total: {timings['total']}s", flush=True)

    # Summary Statistics
    total_q = len(results)
    avg_total_time = sum(r["total_s"] for r in results) / total_q if total_q else 0
    pass_time = sum(1 for r in results if r["pass_under_30s"])
    pass_words = sum(1 for r in results if r["pass_under_100w"])
    pass_steps = sum(1 for r in results if r["pass_max_6steps"])

    print("\n" + "=" * 80, flush=True)
    print("EVALUATION SUMMARY", flush=True)
    print("=" * 80, flush=True)
    print(f"Total Questions Evaluated: {total_q}", flush=True)
    print(f"Average Total Latency:    {avg_total_time:.2f}s", flush=True)
    print(f"Latency < 30s Pass Rate:   {pass_time}/{total_q} ({pass_time/total_q*100:.1f}%)", flush=True)
    print(f"Word Count <= 100 Pass:    {pass_words}/{total_q} ({pass_words/total_q*100:.1f}%)", flush=True)
    print(f"Step Count <= 6 Pass:      {pass_steps}/{total_q} ({pass_steps/total_q*100:.1f}%)", flush=True)

    # Check not_covered fallback correctness
    not_covered = [r for r in results if r["category"] == "not_covered"]
    if not_covered:
        kvk_pass = sum(1 for r in not_covered if r["kvk_fallback"])
        print(f"Uncovered Crops KVK Fallback: {kvk_pass}/{len(not_covered)} ({kvk_pass/len(not_covered)*100:.1f}%)", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Kisan AI evaluation suite")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions to evaluate")
    parser.add_argument("--focus", action="store_true", help="Run focused batch of representative queries")
    parser.add_argument("--ids", type=int, nargs="+", default=None, help="Specific question IDs to evaluate")
    parser.add_argument("--out", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    target_ids = [1, 13, 17] if args.focus else args.ids
    run_evaluation(limit=args.limit, ids=target_ids, output_csv=args.out)
