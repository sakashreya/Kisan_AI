import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from .config import VERIFY_TOKEN, APP_SECRET
from .db import init_db
from .tasks import process_message
from .whatsapp import verify_signature

app = FastAPI(title="Kisan AI")


@app.on_event("startup")
def startup():
    env_mode = os.getenv("ENV", "development").lower()
    if not APP_SECRET and env_mode != "development":
        raise RuntimeError("APP_SECRET must be configured when ENV != 'development' for secure webhook operation.")
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/webhook")
def verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    if not verify_signature(body, request.headers.get("X-Hub-Signature-256", "")):
        raise HTTPException(status_code=403, detail="Bad signature")
    payload = json.loads(body)
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                background_tasks.add_task(process_message, msg)
    return Response(status_code=200)         # must return fast or Meta retries
