import os
from .config import WHISPER_MODEL

_model = None


def _get_local_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        # int8 on CPU is fine for dev. On a GPU use device="cuda", compute_type="float16"
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model


def transcribe(path: str, language_hint: str | None = None) -> tuple[str, str]:
    """
    Transcribes audio file at `path`.
    Returns (transcribed_text, detected_language_code).
    Priority:
    1. Groq Cloud Whisper (ultra-fast, <500ms) if GROQ_API_KEY is configured.
    2. OpenAI Cloud Whisper if OPENAI_API_KEY is configured.
    3. Local faster-whisper model.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # 1. Groq Cloud API (Lightning fast ~300ms, free tier)
    if groq_key:
        try:
            from openai import OpenAI
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            with open(path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=f,
                    response_format="verbose_json",
                    language=language_hint if language_hint else None,
                )
            text = transcription.text.strip()
            lang = getattr(transcription, "language", language_hint or "hi")
            return text, lang
        except Exception as e:
            print(f"[SPEECH] Groq API transcription failed: {e}. Falling back...")

    # 2. OpenAI Cloud Whisper API
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            with open(path, "rb") as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    language=language_hint if language_hint else None,
                )
            text = transcription.text.strip()
            lang = getattr(transcription, "language", language_hint or "hi")
            return text, lang
        except Exception as e:
            print(f"[SPEECH] OpenAI transcription failed: {e}. Falling back...")

    # 3. Local faster-whisper fallback
    try:
        model = _get_local_model()
        segments, info = model.transcribe(path, beam_size=5, language=language_hint, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text, info.language
    except Exception as e:
        print(f"[SPEECH] Local faster-whisper failed: {e}")
        return "", language_hint or "hi"
