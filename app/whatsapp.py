import os
import hashlib
import hmac
import requests
from .config import WHATSAPP_TOKEN, PHONE_NUMBER_ID, APP_SECRET

GRAPH = "https://graph.facebook.com/v21.0"
def _headers():
    token = os.getenv("WHATSAPP_TOKEN") or WHATSAPP_TOKEN
    return {"Authorization": f"Bearer {token}"}


def verify_signature(body: bytes, header: str) -> bool:
    """Check X-Hub-Signature-256. Skipped when APP_SECRET is not set in dev mode only."""
    env_mode = os.getenv("ENV", "development").lower()
    secret = os.getenv("APP_SECRET") or APP_SECRET
    if not secret:
        return env_mode == "development"
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")


def send_text(to: str, text: str):
    phone_id = os.getenv("PHONE_NUMBER_ID") or PHONE_NUMBER_ID
    r = requests.post(
        f"{GRAPH}/{phone_id}/messages",
        headers=_headers(),
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text[:4000]},
        },
        timeout=30,
    )
    if not r.ok:
        print("WhatsApp send error:", r.status_code, r.text)
    return r.ok


def download_media(media_id: str):
    """Returns (bytes, mime_type) for a media id received in a webhook."""
    meta = requests.get(f"{GRAPH}/{media_id}", headers=_headers(), timeout=30)
    meta.raise_for_status()
    info = meta.json()
    data = requests.get(info["url"], headers=_headers(), timeout=60)
    data.raise_for_status()
    return data.content, info.get("mime_type", "")
