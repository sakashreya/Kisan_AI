"""
app/safety.py
Phase 8: Pesticide Safety Check.
Validates agricultural recommendations against CIB & RC restricted pesticide guidelines.
Prepends safety warnings for restricted/banned substances and flags unapproved crop applications.
"""

import json
import os
import re

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "restricted_pesticides.json")

_config_cache = None


def load_safety_config() -> dict:
    global _config_cache
    if _config_cache is None:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    _config_cache = json.load(f)
            except Exception as e:
                print(f"Error loading {CONFIG_PATH}: {e}")
                _config_cache = {"restricted": [], "approved_by_crop": {}}
        else:
            _config_cache = {"restricted": [], "approved_by_crop": {}}
    return _config_cache


def detect_crop(text: str) -> str:
    """Helper to detect crop name mentioned in question or context."""
    text_lower = text.lower()
    crop_keywords = {
        "rice": ["rice", "paddy", "धान", "भात", "நெல்", "వరి"],
        "cotton": ["cotton", "कपास", "कपाशी", "பருத்தி", "పత్తి"],
        "tomato": ["tomato", "टमाटर", "टोमॅटो", "தக்காளி", "టమోటా"],
        "chilli": ["chilli", "chili", "मिर्च", "मिरची", "மிளகாய்", "మిరప"],
        "groundnut": ["groundnut", "peanut", "मूंगफली", "भुईमूग", "நிலக்கடலை", "వేరుశనగ"],
        "sugarcane": ["sugarcane", "गन्ना", "ऊस", "கரும்பு", "చెరకు"],
        "banana": ["banana", "केला", "केळी", "வாழை", "అరటి"],
        "mango": ["mango", "आम", "आंबा", "மாம்பழம்", "మామిడి"]
    }
    for crop, kws in crop_keywords.items():
        if any(kw in text_lower for kw in kws):
            return crop
    return ""


def check_pesticide_safety(answer_en: str, crop: str = "") -> tuple[str, list[str]]:
    """
    Scans the generated English answer for chemical names.
    - If a restricted chemical is mentioned: prepends a WARNING line and adds a flag.
    - If a chemical is mentioned that is not in the approved list for the identified crop: adds a flag.
    Returns: (modified_answer, flags_list)
    """
    cfg = load_safety_config()
    restricted_list = cfg.get("restricted", [])
    approved_by_crop = cfg.get("approved_by_crop", {})

    flags = []
    warnings = []

    answer_lower = answer_en.lower()

    # 1. Scan for restricted/banned chemicals
    for chem in restricted_list:
        chem_clean = chem.strip().lower()
        if not chem_clean:
            continue
        # Use word boundary check
        pattern = rf"\b{re.escape(chem_clean)}\b"
        if re.search(pattern, answer_lower):
            flag = f"RESTRICTED_CHEMICAL: {chem_clean}"
            flags.append(flag)
            warn = (
                f"WARNING: '{chem.title()}' is a RESTRICTED/BANNED pesticide under CIB&RC guidelines. "
                "Do not apply without authorized agricultural officer approval."
            )
            warnings.append(warn)

    # 2. Check for crop-specific approval if crop is specified or detected
    crop_clean = crop.strip().lower()
    if crop_clean in approved_by_crop:
        approved_for_this_crop = [c.lower() for c in approved_by_crop[crop_clean]]
        # Collect all known chemicals from all crops to check if an unapproved chemical was used
        all_chemicals = set()
        for c_list in approved_by_crop.values():
            all_chemicals.update(c.lower() for c in c_list)

        for chem in all_chemicals:
            pattern = rf"\b{re.escape(chem)}\b"
            if re.search(pattern, answer_lower):
                if chem not in approved_for_this_crop and f"RESTRICTED_CHEMICAL: {chem}" not in flags:
                    flag = f"UNAPPROVED_FOR_CROP: {chem} on {crop_clean}"
                    flags.append(flag)

    modified_answer = answer_en
    if warnings:
        warning_header = "\n".join(warnings)
        modified_answer = f"{warning_header}\n\n{answer_en}"

    return modified_answer, flags
