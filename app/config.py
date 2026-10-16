import os
import socket
from dotenv import load_dotenv

# Ensure fast IPv4 routing on Windows (prevents 20s IPv6 TCP timeout on Google APIs)
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_first_getaddrinfo(*args, **kwargs):
    res = _orig_getaddrinfo(*args, **kwargs)
    ipv4 = [r for r in res if r[0] == socket.AF_INET]
    return ipv4 if ipv4 else res
socket.getaddrinfo = _ipv4_first_getaddrinfo

load_dotenv()
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

def env(key, default=""):
    return os.getenv(key, default)


WHATSAPP_TOKEN = env("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = env("PHONE_NUMBER_ID")
VERIFY_TOKEN = env("VERIFY_TOKEN", "kisan-verify-123")
APP_SECRET = env("APP_SECRET")
OPENWEATHER_API_KEY = env("OPENWEATHER_API_KEY")
DATABASE_URL = env("DATABASE_URL", "postgresql+psycopg2://kisan:kisan@localhost:5432/kisan")
REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")
MINIO_ENDPOINT = env("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = env("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = env("MINIO_SECRET_KEY", "minioadmin")
AGENT_MODEL = env("AGENT_MODEL", "qwen2.5:7b")
VISION_MODEL = env("VISION_MODEL", "llava:7b")
WHISPER_MODEL = env("WHISPER_MODEL", "small")
EMBED_MODEL = env("EMBED_MODEL", "intfloat/multilingual-e5-small")
CHROMA_PATH = env("CHROMA_PATH", "chroma_db")
GEMINI_API_KEY = env("GEMINI_API_KEY", "")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-flash-lite-latest")
