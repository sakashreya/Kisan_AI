import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import init_db, update_farmer
from app.pipeline import run_pipeline

init_db()
lang = sys.argv[1] if len(sys.argv) > 1 else "en"
phone = "919999999999"
update_farmer(phone, language=lang)   # reply in the language you are testing

while True:
    q = input("\nFarmer> ").strip()
    if not q:
        continue                      # ignore empty input
    print("\nKisan AI>", run_pipeline(phone, q, lang))



