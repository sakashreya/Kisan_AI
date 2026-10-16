import os
import sys
import traceback
from celery import Celery
import redis

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .config import REDIS_URL
from .db import get_farmer, update_farmer
from .whatsapp import send_text, download_media
from .storage import save_audio, save_temp
from .pipeline import run_pipeline, script_lang, LANGS

celery = Celery("kisan", broker=REDIS_URL, backend=REDIS_URL)

FALLBACK = "Sorry, I could not process that. Please try again."

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, socket_timeout=0.5)
            _redis_client.ping()
        except Exception:
            _redis_client = False
    return _redis_client if _redis_client is not False else None

_local_seen_messages = set()

def is_duplicate_message(msg_id: str) -> bool:
    """Check if WhatsApp message ID was already processed (24h TTL)."""
    if not msg_id:
        return False
    r = get_redis()
    if r:
        try:
            is_new = r.set(f"seen_msg:{msg_id}", "1", nx=True, ex=86400)
            return not is_new
        except Exception as e:
            print("Redis duplicate check warning:", e)
    if msg_id in _local_seen_messages:
        return True
    _local_seen_messages.add(msg_id)
    return False


@celery.task(name="process_message")
def process_message(msg: dict):
    msg_id = msg.get("id", "")
    if msg_id and is_duplicate_message(msg_id):
        print(f"Skipping duplicate WhatsApp message ID: {msg_id}")
        return

    phone, mtype = msg["from"], msg["type"]
    temp_file_to_cleanup = None
    try:
        farmer = get_farmer(phone)
        text, in_lang, image_info = "", "en", ""

        if mtype == "text":
            text = msg["text"]["body"]
            in_lang = script_lang(text, farmer.language)

        elif mtype == "audio":
            from .speech import transcribe
            data, _ = download_media(msg["audio"]["id"])
            path = save_audio(data, phone)
            temp_file_to_cleanup = path
            text, lang = transcribe(path, farmer.language if farmer.language in LANGS else None)
            in_lang = lang if lang in LANGS else "hi"
            if not text:
                send_text(phone, "I could not hear anything. Please send the voice note again.")
                return

        elif mtype == "image":
            from .vision import describe_image
            data, mime = download_media(msg["image"]["id"])
            path = save_temp(data, ".jpg")
            temp_file_to_cleanup = path
            caption = msg["image"].get("caption", "")
            image_info = describe_image(path, caption)
            text = caption or "What is wrong with my crop? Identify the problem and suggest treatment."
            in_lang = script_lang(caption, farmer.language) if caption else "en"

        elif mtype == "location":
            loc = msg["location"]
            update_farmer(phone, lat=loc["latitude"], lon=loc["longitude"])
            send_text(phone, "Location saved. Now ask your farming question.")
            return

        else:
            send_text(phone, "Please send a text, voice note, or crop photo.")
            return

        print("\n" + "=" * 55)
        print(f"[WHATSAPP INCOMING] From: {phone} | Type: {mtype}")
        print(f"Farmer Message: {text}")
        print(f"Detected Language: {in_lang}")
        if image_info:
            print(f"Vision Analysis: {image_info}")
        print("Processing through Kisan AI RAG Agent & ICAR Guides...")
        print("=" * 55 + "\n")

        answer = run_pipeline(phone, text, in_lang, image_info)

        print("\n" + "=" * 55)
        print(f"[WHATSAPP OUTGOING REPLY] To: {phone}")
        print(f"Answer:\n{answer}")
        print("=" * 55 + "\n")

        send_text(phone, answer)
    except Exception:
        traceback.print_exc()
        send_text(phone, FALLBACK)
    finally:
        if temp_file_to_cleanup and os.path.exists(temp_file_to_cleanup):
            try:
                os.unlink(temp_file_to_cleanup)
            except Exception as e:
                print(f"Failed to unlink temp file {temp_file_to_cleanup}: {e}")
