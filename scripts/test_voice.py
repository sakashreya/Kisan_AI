"""
scripts/test_voice.py
Phase 5.1: Test faster-whisper on voice audio.
Calls app.speech.transcribe() on an audio file and reports transcribed text and detected language.
"""

import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_voice(audio_path: str = ""):
    print("=" * 80)
    print("PHASE 5.1: FASTER-WHISPER SPEECH TRANSCRIPTION TEST")
    print("=" * 80)

    try:
        from app.speech import transcribe, _get
        from app.config import WHISPER_MODEL
        print(f"Configured Whisper Model: {WHISPER_MODEL}")

        print("Initializing Whisper model...")
        t0 = time.perf_counter()
        model = _get()
        t_load = time.perf_counter() - t0
        print(f"Model loaded successfully in {t_load:.2f}s.")

        if not audio_path or not os.path.exists(audio_path):
            print(f"\nNo audio file provided or file not found at: '{audio_path}'")
            print("Please provide a valid .wav, .mp3, or .ogg voice recording to test transcription.")
            return

        print(f"\nTranscribing: {audio_path}")
        t0 = time.perf_counter()
        text, detected_lang = transcribe(audio_path)
        t_trans = time.perf_counter() - t0

        print("\n" + "-" * 80)
        print(f"TRANSCRIPTION RESULT ({t_trans:.2f}s):")
        print(f"Detected Language: {detected_lang}")
        print(f"Transcribed Text:   {text}")
        print("-" * 80)

    except Exception as e:
        print(f"\nWhisper Execution Error: {e}")
        print("\nNote: If 'model.bin' consistency check fails, the 483MB model file for")
        print("Systran/faster-whisper-small must be copied into the HuggingFace cache directory.")

if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else ""
    test_voice(audio_file)
