"""
scripts/test_vision.py
Phase 5.2: Test LLaVA Vision on crop leaf image.
Calls app.vision.describe_image() directly on an agricultural test photo.
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

from app.vision import describe_image

def test_vision():
    # Test image path
    image_path = os.path.join(
        os.path.expanduser("~"),
        r".gemini\antigravity-ide\brain\8264ac9d-3c76-4d82-a3e4-b26c82e02cef\rice_leaf_blast_1791450909531.jpg"
    )

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    print("=" * 80)
    print("PHASE 5.2: LLAVA VISION TEST (CROP PHOTO ANALYSIS)")
    print(f"Image: {image_path}")
    print("Model: llava:7b via Ollama (127.0.0.1:11434)")
    print("=" * 80)

    caption = "Farmer noticed these lesions spreading on their paddy field."
    print(f"\nFarmer note: {caption}\n")
    print("Analyzing image with LLaVA...")

    t0 = time.perf_counter()
    analysis = describe_image(image_path, caption=caption)
    t_el = time.perf_counter() - t0

    print("\n" + "-" * 80)
    print("LLAVA ANALYSIS RESULT:")
    print("-" * 80)
    print(analysis)
    print("-" * 80)
    print(f"Analysis completed in {t_el:.2f} seconds.")
    print("=" * 80)

if __name__ == "__main__":
    test_vision()
