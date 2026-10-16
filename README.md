# Kisan AI: Multilingual Agronomic Advisory Assistant

**Kisan AI** (L&T EduTech Project 08) is an agentic WhatsApp advisory assistant tailored for Indian smallholder farmers. The system ingests text queries, regional voice notes, crop/pest photos, and GPS/village locations to provide growth-stage-specific advice strictly grounded in **ICAR** and **TNAU (Tamil Nadu Agricultural University)** crop production guides.

---

## 🏗️ System Architecture

```
[Farmer WhatsApp] (Text / Voice / Photo / Location)
       │
       ▼
[Meta Cloud API Webhook] (GET challenge / POST HMAC-SHA256)
       │
       ▼
[FastAPI / Webhook Handler] ─── Duplicate Guard (24h TTL)
       │
       ▼
[Task Processor] (Celery Worker / Async Fallback)
       ├─► Voice Note: faster-whisper-small (transcription & language detect)
       ├─► Crop Photo: LLaVA:7b (symptoms & pathology diagnosis)
       └─► Text Query: IndicTrans2 (Regional -> English translation)
       │
       ▼
[LangChain ReAct Agent] (Qwen2.5:7b via Ollama)
       ├─► farmer_profile: Village, GPS coordinates, historical crops
       ├─► get_weather: Live 24h forecast via OpenWeatherMap
       ├─► get_soil: Topsoil pH, clay %, sand % via ISRIC SoilGrids
       └─► search_knowledge: ChromaDB Vector Store (3,467 ICAR/TNAU chunks)
       │
       ▼
[Pesticide Safety Guardrail] (CIB & RC Guidelines)
       ├─► Scans answer against 15 banned/restricted chemicals (e.g., Endosulfan, Monocrotophos)
       ├─► Prepends mandatory WARNING header if restricted substance detected
       ├─► Flags unapproved chemicals by target crop
       └─► Records safety flags to database QueryLog table
       │
       ▼
[IndicTrans2 Outbound Translation] (English -> HI / MR / TA / TE)
       └─► Protected Technical Glossary: Injects bilingual chemical names
           Format: Native Script (English) e.g., 'மான்கோசெப் (Mancozeb)'
       │
       ▼
[WhatsApp Reply Sent to Farmer via Graph API]
```

---

## 📊 Component Status & Verification Matrix

| Phase | Component | Status | Verification Result |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Knowledge Base (Additive RAG)** | **VERIFIED** | ChromaDB enlarged to 3,467 chunks with TNAU Horticulture Guide. FAO rice chunks filtered (`EXCLUDED_SOURCES`). |
| **Phase 2** | **Agent Prompt & Bilingual Terms** | **VERIFIED** | Enforced $< 100$ words, $\le 6$ steps, safety warning, and bilingual `Native (English)` glossary. |
| **Phase 3** | **Evaluation & Timed Pipeline** | **VERIFIED** | `run_pipeline_timed()` implemented with per-stage latency tracking. Focused evaluation executed. |
| **Phase 4** | **Language Testing (HI, MR, TA, TE)** | **VERIFIED** | 100% pass across all 4 languages in both directions with alphanumeric placeholder protection (`ZTAG{i}Z`). |
| **Phase 5** | **Vision: LLaVA-7B** | **VERIFIED** | Successfully identified rice crop blast lesions from close-up field photograph in 137s. |
| **Phase 5** | **Voice: Faster-Whisper** | **READY** | Pipeline wired in `app/speech.py`. `model.bin` requires offline copy due to corporate proxy block. |
| **Phase 6** | **API Tools: Weather & Soil** | **VERIFIED** | Live OpenWeather (1.14s) and ISRIC SoilGrids query (3.19s) functional for delta farmland. |
| **Phase 7** | **WhatsApp Webhook & Security** | **VERIFIED** | HMAC signature enforcement, 24h duplicate message deduplication, and temp file cleanup verified. |
| **Phase 8** | **Pesticide Safety Check** | **VERIFIED** | `config/restricted_pesticides.json` configured. Restricted chemical warning prepending and QueryLog logging verified. |

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- **Operating System:** Windows 10/11 or Linux
- **Python:** Python 3.11+
- **Ollama:** Installed from [ollama.com](https://ollama.com) with models:
  ```bash
  ollama pull qwen2.5:7b
  ollama pull llava:7b
  ollama pull nomic-embed-text
  ```

### 2. Environment Configuration
Create `.env` from `.env.example`:
```env
OPENWEATHER_API_KEY=<your_openweather_api_key>
VERIFY_TOKEN=kisan-verify-123
WHATSAPP_TOKEN=<your_meta_access_token>
PHONE_NUMBER_ID=<your_phone_number_id>
APP_SECRET=<your_meta_app_secret>
DATABASE_URL=sqlite:///kisan.db
ENV=development
```

### 3. Run Test Verification Suites
Each phase includes an automated test script:

- **Phase 4 (Regional Languages):**
  ```powershell
  .venv\Scripts\python.exe scripts\test_languages.py
  .venv\Scripts\python.exe scripts\test_custom_languages.py
  ```
- **Phase 5 (Vision Analysis):**
  ```powershell
  .venv\Scripts\python.exe scripts\test_vision.py
  ```
- **Phase 6 (Weather & Soil APIs):**
  ```powershell
  .venv\Scripts\python.exe scripts\test_api_tools.py
  ```
- **Phase 7 (WhatsApp Integration & Security):**
  ```powershell
  .venv\Scripts\python.exe scripts\test_phase7_whatsapp.py
  ```
- **Phase 8 (Pesticide Safety):**
  ```powershell
  .venv\Scripts\python.exe scripts\test_phase8_safety.py
  ```

### 4. Start the Application

#### Option A: Interactive CLI (Testing without WhatsApp)
```powershell
.venv\Scripts\python.exe scripts\chat_cli.py hi    # Hindi
.venv\Scripts\python.exe scripts\chat_cli.py ta    # Tamil
.venv\Scripts\python.exe scripts\chat_cli.py mr    # Marathi
.venv\Scripts\python.exe scripts\chat_cli.py te    # Telugu
.venv\Scripts\python.exe scripts\chat_cli.py en    # English
```

#### Option B: Webhook Server
```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

---

## ⚠️ Known Limitations & Hardware Requirements

1. **CPU vs GPU Latency SLA:**
   - On CPU (AVX2), local 7B LLM inference takes ~120–250 seconds per multi-step tool query.
   - For production (<30 second target), an NVIDIA GPU with at least 8GB VRAM (e.g., RTX 3060/4060 or T4/A10G) is required.
2. **Knowledge Base Geographic Scope:**
   - The knowledge base is grounded in **ICAR** and **TNAU (Tamil Nadu Agricultural University)** guides. Crops covered include Rice, Cotton, Tomato, Chilli, Groundnut, Sugarcane, Banana, Mango, and vegetables.
   - Non-covered crops (e.g. Saffron, Apple, Wheat rust) automatically fall back to the farmer's local **Krishi Vigyan Kendra (KVK)** as required by project protocol.
3. **Whisper Model Weights:**
   - `faster-whisper-small` weights (`model.bin`, ~483MB) must be transferred into HuggingFace cache if the host network proxy restricts large binary file downloads.

---

## 📚 Knowledge Base Ingestion

To add new agronomy manuals or university package of practices:
1. Place PDF documents in `data/pdfs/` using the crop naming convention:
   - `<crop>__<guide_name>.pdf` (e.g., `cotton__cicr_management_guide.pdf`)
   - `multi__<guide_name>.pdf` (for multi-crop handbooks)
2. Run the additive ingestion script:
   ```powershell
   .venv\Scripts\python.exe scripts\ingest.py
   ```
   *(Existing ChromaDB collections and vector chunks are preserved additively).*
