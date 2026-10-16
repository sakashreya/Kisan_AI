import time
from .db import get_farmer, update_farmer, log_query
from .agent import run_agent
from .translate import translate
from .safety import check_pesticide_safety, detect_crop

LANGS = {"hi", "mr", "ta", "te", "en"}


def script_lang(text: str, current: str = "hi") -> str:
    """Guess language from the script. Latin script -> 'en' (treated as English)."""
    for ch in text:
        o = ord(ch)
        if 0x0B80 <= o <= 0x0BFF:
            return "ta"
        if 0x0C00 <= o <= 0x0C7F:
            return "te"
        if 0x0900 <= o <= 0x097F:
            return current if current in ("hi", "mr") else "hi"
    return "en"


def run_pipeline(phone: str, text: str, in_lang: str = "en", image_info: str = "") -> str:
    ans, _ = run_pipeline_timed(phone, text, in_lang, image_info)
    return ans


def run_pipeline_timed(phone: str, text: str, in_lang: str = "en", image_info: str = "") -> tuple[str, dict]:
    t_start = time.perf_counter()
    farmer = get_farmer(phone)
    # Reply strictly in the user's input language (English, Hindi, Telugu, Tamil, Marathi)
    reply_lang = in_lang if in_lang in LANGS else (farmer.language or "en")
    if reply_lang != farmer.language:
        update_farmer(phone, language=reply_lang)

    # 1. Translation In (if non-English)
    t0 = time.perf_counter()
    english_q = translate(text, in_lang, "en") if in_lang != "en" else text
    t_trans_in = time.perf_counter() - t0

    # 2. Agent (ReAct reasoning + Tool calls / Retrieval)
    t1 = time.perf_counter()
    answer_en = run_agent(phone, english_q, image_info)
    t_agent = time.perf_counter() - t1

    # 3. Post-Check: Pesticide Safety Check (Phase 8)
    crop = detect_crop(english_q)
    if not crop and farmer.crops and isinstance(farmer.crops, list) and len(farmer.crops) > 0:
        crop = farmer.crops[-1]
    safe_answer_en, flags = check_pesticide_safety(answer_en, crop=crop)
    if flags:
        print(f"[SAFETY CHECK] flags detected: {flags}")

    # 4. Translation Out (if non-English target)
    t2 = time.perf_counter()
    answer = translate(safe_answer_en, "en", reply_lang) if reply_lang != "en" else safe_answer_en
    t_trans_out = time.perf_counter() - t2

    t_total = time.perf_counter() - t_start

    log_query(phone, text, answer, flags=flags)

    timings = {
        "translate_in": round(t_trans_in, 2),
        "agent": round(t_agent, 2),
        "translate_out": round(t_trans_out, 2),
        "total": round(t_total, 2),
    }

    status = "PASS (<30s)" if t_total < 30.0 else "EXCEED (>=30s)"
    print(f"\n[LATENCY] phone={phone} | lang={in_lang}->{reply_lang} | total={t_total:.2f}s [{status}]")
    print(f"  translate_in:  {t_trans_in:5.2f}s | agent+tools: {t_agent:5.2f}s | translate_out: {t_trans_out:5.2f}s")

    return answer, timings
