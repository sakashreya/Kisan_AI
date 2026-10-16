"""
scripts/test_phase8_safety.py
Phase 8: Pesticide Safety Check Verification Suite.
Tests:
1. Validation of config/restricted_pesticides.json (CIB & RC guidelines).
2. Detection and warning prepending for restricted/banned chemicals.
3. Flagging of unapproved chemicals by crop.
4. Persistence of safety flags in the QueryLog database table.
"""

import os
import sys
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.safety import check_pesticide_safety, load_safety_config, detect_crop
from app.db import init_db, log_query, Session, QueryLog

def run_tests():
    print("=" * 80)
    print("PHASE 8: PESTICIDE SAFETY CHECK VERIFICATION SUITE")
    print("=" * 80)

    # 1. Config Validation (Step 8.1)
    cfg = load_safety_config()
    restricted = cfg.get("restricted", [])
    approved = cfg.get("approved_by_crop", {})
    print(f"\n1. Config Verification (config/restricted_pesticides.json):")
    print(f"   Restricted substances count: {len(restricted)} (e.g., {restricted[:4]})")
    print(f"   Crops configured: {list(approved.keys())}")
    assert len(restricted) >= 5, "Restricted pesticides list must contain CIB banned/restricted chemicals"
    assert "rice" in approved and "cotton" in approved

    # 2. Case A: Banned / Restricted Chemical (Step 8.2)
    print("\n2. Case A: Restricted Chemical Warning Test (Monocrotophos):")
    unsafe_ans = "For severe stem borer, spray Monocrotophos 36 SL at 1.5 ml/L. Wear gloves."
    checked_ans, flags = check_pesticide_safety(unsafe_ans, crop="rice")
    print("   Original Answer:")
    print(f"     {unsafe_ans}")
    print("   Flags Detected:")
    print(f"     {flags}")
    print("   Safety-Checked Answer:")
    for line in checked_ans.split("\n"):
        print(f"     {line}")
    assert "RESTRICTED_CHEMICAL: monocrotophos" in flags
    assert "WARNING:" in checked_ans
    assert "RESTRICTED/BANNED" in checked_ans

    # 3. Case B: Approved Chemical for Crop
    print("\n3. Case B: Approved Chemical Test (Tricyclazole on Rice):")
    safe_ans = "Spray Tricyclazole 75 WP at 0.6g/L for Rice blast at early tillering stage."
    checked_safe, safe_flags = check_pesticide_safety(safe_ans, crop="rice")
    print(f"   Flags Detected: {safe_flags} (Expect empty)")
    print(f"   Warning in text: {'WARNING' in checked_safe} (Expect False)")
    assert safe_flags == []
    assert "WARNING" not in checked_safe

    # 4. Case C: Unapproved Chemical for Crop
    print("\n4. Case C: Unapproved Chemical on Crop Test (Spinosad on Rice):")
    # Spinosad is approved for cotton/tomato/chilli, but not in CIB standard rice list
    unapproved_ans = "Apply Spinosad 45 SC at 0.5 ml/L to control rice leaf folder."
    checked_unapp, unapp_flags = check_pesticide_safety(unapproved_ans, crop="rice")
    print(f"   Flags Detected: {unapp_flags} (Expect UNAPPROVED_FOR_CROP)")
    assert any("UNAPPROVED_FOR_CROP" in f for f in unapp_flags)

    # 5. Database Logging & Schema Persistence (Step 8.2)
    print("\n5. Database Flag Logging Test (QueryLog Table):")
    init_db()
    test_phone = "919876543088"
    log_query(test_phone, "What medicine for stem borer?", checked_ans, flags=flags)

    with Session() as s:
        last_log = s.query(QueryLog).filter_by(phone=test_phone).order_by(QueryLog.id.desc()).first()
        print(f"   Persisted QueryLog ID: {last_log.id}")
        print(f"   Stored Flags: {last_log.flags}")
        assert last_log.flags == flags
        assert "RESTRICTED_CHEMICAL: monocrotophos" in last_log.flags

    print("\n" + "=" * 80)
    print("PHASE 8 RESULTS: ALL PESTICIDE SAFETY CHECKS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
