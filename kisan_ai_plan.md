# Kisan AI — Complete Project Plan
**No files or data will be deleted. No destructive actions.**

---

## Current True Status (from audit)

| What | Status |
|---|---|
| ChromaDB | 1,525 chunks (FAO rice chunks already removed by you) |
| Files on disk | 54 PDFs/TXTs in data/pdfs |
| Not yet ingested | `multi__tnau_horticulture_guide.pdf` |
| Agent tested | Mango question only, in English→Hindi |
| Untested | Voice, photo, WhatsApp, Celery, Marathi/Tamil/Telugu, weather API live call |

---

## PHASE 1 — Fix the Knowledge Base (No Deletion)
**Goal: make the RAG layer accurate and complete before anything else.**

### Step 1.1 — Ingest the missing horticulture guide
- **Action:** Run `scripts/ingest.py` for `multi__tnau_horticulture_guide.pdf`
- **Why:** It is on disk but not in ChromaDB. Large document covering many crops.
- **Risk:** None. Adds chunks, does not remove anything.

### Step 1.2 — Fix crop key naming in `app/rag.py`
- **Problem:** ChromaDB has split keys like `rice_diseases`, `chickpea_disease`,
  `castor_diseases`, `maize_disease_new` etc. But the alias map and farmer_profile
  tool only record simple names like `rice`, `chickpea`.
  A query with `crop=rice` will miss all `rice_diseases` chunks entirely.
- **Action:** Add compound crop name aliases to the `ALIASES` dict so:
  - `rice` also searches `rice_diseases`
  - `chickpea` also searches `chickpea_disease`
  - `maize` also searches `maize_disease_new`
  - `cotton` also searches `cotton_diseases`
  - `banana` also searches `banana_diseases`
  - etc.
- **How:** Modify `search()` to run two retrieval passes when compound keys exist,
  merge results, deduplicate, and return top-k.
- **Risk:** None. Only changes search logic, not stored data.

---

## PHASE 2 — Fix the Agent Brain
**Goal: answers that are short, accurate, source-grounded, and safe.**

### Step 2.1 — Rewrite system prompt in `app/agent.py`
Current problems:
- Answers drift to unrelated pests
- Too long (120 words allowed, should be 100)
- Omits doses and thresholds that are in the retrieved text
- Does not say "not covered" when sources have nothing

New prompt rules (exact wording to implement):
1. Answer ONLY the question asked. Do not add pests or diseases not mentioned.
2. Maximum 6 numbered steps, under 100 words total.
3. Include thresholds, timing and doses exactly as the source states, with units.
4. Never invent a number, chemical name or dosage. If the source does not give a dose, say "dose not specified in source."
5. Write all chemical names in English.
6. If the knowledge base does not cover the crop or question, say exactly:
   "This crop or issue is not in my knowledge base. Please contact your local Krishi Vigyan Kendra (KVK)."

### Step 2.2 — Add an agronomic glossary to `app/translate.py`
- **Problem:** Hindi translation rendered a pest name as a weed.
- **Action:** Add a `PROTECTED_TERMS` dict — a list of pest names, chemical names,
  and agronomic terms that must NOT be translated (passed through as-is in English).
- **How:** Before sending to IndicTrans2, replace protected terms with placeholders.
  After translation, restore them.
- **Risk:** None. Does not change model weights.

---

## PHASE 3 — Evaluation (Measure Before Claiming)
**Goal: a real baseline number before calling anything "working".**

### Step 3.1 — Build `scripts/evaluate.py`
- 30 questions covering:
  - 8 crops well covered in the KB (rice, mango, cotton, banana, citrus, chilli, tomato, groundnut)
  - 4 crops with thin coverage (onion: 1 chunk, gerbera: 1 chunk, groundnut: 1 chunk, cardamom: 2 chunks)
  - 3 crops NOT in the KB at all (wheat rust, saffron, areca nut) — expect "not covered" answer
  - 5 language questions (same question in Hindi, Marathi, Tamil, Telugu, English)
- For each question, record:
  - Question text
  - Language
  - Answer text
  - Sources retrieved (filename + page)
  - Time taken per stage: translation-in, retrieval, agent, translation-out, total
- Write to `scripts/eval_results.csv`

### Step 3.2 — Latency logging in `app/pipeline.py`
- Add `time.perf_counter()` checkpoints at each stage in `run_pipeline()`.
- Print a summary table at end: `translate_in | retrieval | agent | translate_out | total`.
- Target: total < 30 seconds.

---

## PHASE 4 — Language Testing
**Goal: verify all 4 regional languages work in both directions.**

### Step 4.1 — Confirm IndicTrans2 model files exist locally
- Check that `ai4bharat/indictrans2-indic-en-dist-200M` and
  `ai4bharat/indictrans2-en-indic-dist-200M` are in the HuggingFace cache.
- If missing: run `scripts/download_models.py` (must be done with network).

### Step 4.2 — Test all 4 languages
- Run a small test script that sends one question in each of:
  Hindi, Marathi, Tamil, Telugu → English (translation in)
  English answer → Hindi, Marathi, Tamil, Telugu (translation out)
- Show the actual translated text output. Flag any mistranslation.

---

## PHASE 5 — Voice and Vision
**Goal: test the two untested input modes.**

### Step 5.1 — Test faster-whisper
- Use any short `.ogg` or `.wav` file (can record on phone).
- Run `app/speech.py` directly on the file.
- Show transcribed text and detected language.
- Confirm `WHISPER_MODEL=small` works. Note that `large-v3` is the spec requirement
  for production but is too large for dev.

### Step 5.2 — Test LLaVA vision
- Use any crop photo (leaf, pest, field).
- Run `app/vision.py` directly on the image file.
- Show the description output from LLaVA.
- Requires `ollama pull llava:7b` to be done first.

---

## PHASE 6 — Verify API Tools
**Goal: confirm live weather and soil data actually return.**

### Step 6.1 — Weather tool live test
- Call `get_weather(lat=13.08, lon=80.27)` (Chennai) directly.
- Show the returned string. Verify API key in `.env` is valid.

### Step 6.2 — Soil tool live test
- Call `get_soil(lat=13.08, lon=80.27)` directly.
- Show the returned string. SoilGrids API needs no key but is sometimes slow.

---

## PHASE 7 — WhatsApp End-to-End
**Goal: a real message from a phone reaches the agent and a reply comes back.**

### Step 7.1 — Local services up
- `docker compose up -d` (Postgres, Redis, MinIO)
- Confirm all three containers are running.

### Step 7.2 — Start FastAPI + Celery worker
- `uvicorn app.main:app --reload --port 8000`
- `celery -A app.tasks.celery worker --concurrency=1 -l info -P solo`

### Step 7.3 — Expose with ngrok
- `ngrok http 8000` → copy the HTTPS URL.
- In Meta developer portal: set webhook URL to `https://<ngrok>/webhook`,
  verify token = value in `.env`, subscribe to "messages".

### Step 7.4 — Duplicate message protection
- Add a Redis SET to store processed WhatsApp message IDs.
- Before processing, check if message ID already in Redis. If yes, skip silently.
- TTL: 24 hours per message ID.

### Step 7.5 — Temp file cleanup
- After processing each voice note or image, `os.unlink()` the temp file.
- Add a `finally:` block in the Celery task to ensure cleanup even on error.

### Step 7.6 — APP_SECRET enforcement
- If `APP_SECRET` is empty and `ENV != "development"`, refuse to start the webhook.
- Currently `verify_signature()` returns `True` when `APP_SECRET` is missing —
  acceptable only in dev mode.

---

## PHASE 8 — Pesticide Safety Check
**Goal: flag any chemical in an answer that may be restricted.**

### Step 8.1 — Create `config/restricted_pesticides.json`
- Create an empty structure that YOU will fill from the CIB registered list.
- Format:
  ```json
  {
    "restricted": ["endosulfan", "monocrotophos"],
    "approved_by_crop": {
      "rice": ["cartap hydrochloride", "chlorpyriphos"],
      "cotton": ["imidacloprid", "spinosad"]
    }
  }
  ```
- I will NOT fill this list. You supply it from cibrc.gov.in.

### Step 8.2 — Add post-check in `app/agent.py` or `app/pipeline.py`
- After the agent generates an answer, scan it for chemical names from the config.
- If a restricted chemical is mentioned: prepend a WARNING line to the answer.
- If a chemical is mentioned but not in the approved list for that crop: flag it.
- Log all flags to the QueryLog table.

---

## PHASE 9 — README and Documentation
**Goal: README reflects actual state, not aspirational state.**

- Accurate setup steps (what commands to run, in what order).
- Honest status table (tested vs not tested).
- Known limitations section.
- Data sources section (TNAU, Tamil Nadu focus, 2011 docs).
- How to add new documents (naming convention, ingest command).

---

## Summary Timeline

| Phase | What | Files Changed |
|---|---|---|
| 1 | Knowledge base fix | `app/rag.py`, run `scripts/ingest.py` |
| 2 | Agent prompt + glossary | `app/agent.py`, `app/translate.py` |
| 3 | Evaluation + latency | `scripts/evaluate.py`, `app/pipeline.py` |
| 4 | Language testing | New test script, no prod file changes |
| 5 | Voice + vision testing | New test script, no prod file changes |
| 6 | API tools verification | New test script |
| 7 | WhatsApp end-to-end | `app/tasks.py`, `app/whatsapp.py`, `app/main.py` |
| 8 | Pesticide safety | `config/restricted_pesticides.json`, `app/pipeline.py` |
| 9 | README | `README.md` |

**No files will be deleted. No ChromaDB collections will be dropped. No tables will be truncated.**
Every step adds or fixes — nothing removes.
