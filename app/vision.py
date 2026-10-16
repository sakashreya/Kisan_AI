import ollama
from .config import VISION_MODEL, GEMINI_API_KEY, GEMINI_MODEL

PROMPT = (
    "You are an agricultural expert. Look at this crop photo. In 3-4 short sentences say: "
    "which crop it is (if clear), the visible symptoms, and the most likely pest or disease. "
    "If you are not sure, say so."
)


def describe_image(path: str, caption: str = "") -> str:
    prompt = PROMPT + (f" Farmer's note: {caption}" if caption else "")
    if GEMINI_API_KEY:
        try:
            from google import genai
            from PIL import Image
            client = genai.Client(api_key=GEMINI_API_KEY)
            img = Image.open(path)
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[img, prompt],
            )
            return resp.text.strip()
        except Exception as e:
            print(f"[VISION] Gemini vision error ({e}), falling back to local Ollama")

    client = ollama.Client(host="http://127.0.0.1:11434")
    resp = client.chat(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": prompt, "images": [path]}],
    )
    return resp["message"]["content"].strip()
