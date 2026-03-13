"""
Zerith AI — Screen Analyzer
Send screenshots to the LLM (vision model) for understanding screen content.
"""

import base64
from pathlib import Path
from utils.logger import log
import config


def encode_image_base64(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_screen(image_path: str, question: str = "What is on this screen?") -> str:
    """
    Analyze a screenshot using the LLM vision model.
    Falls back to OCR if vision model is unavailable.
    """
    if not Path(image_path).exists():
        return f"Image not found: {image_path}"

    log.info(f"Analyzing screen: {image_path}")

    # Try vision model first (OpenAI)
    if config.OPENAI_API_KEY:
        try:
            return _analyze_with_openai(image_path, question)
        except Exception as e:
            log.warning(f"OpenAI vision failed: {e}")

    # Try Ollama with vision-capable model
    try:
        return _analyze_with_ollama(image_path, question)
    except Exception as e:
        log.warning(f"Ollama vision failed: {e}")

    # Fallback to OCR
    log.info("Falling back to OCR for screen analysis")
    from vision.ocr_reader import read_text_from_image
    return read_text_from_image(image_path)


def _analyze_with_openai(image_path: str, question: str) -> str:
    """Use OpenAI GPT-4 Vision to analyze the screenshot."""
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    b64_image = encode_image_base64(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                    },
                ],
            }
        ],
        max_tokens=500,
    )
    result = response.choices[0].message.content
    log.info("Screen analysis complete (OpenAI Vision)")
    return result


def _analyze_with_ollama(image_path: str, question: str) -> str:
    """Use Ollama with a vision-capable model (e.g. llava)."""
    import requests

    b64_image = encode_image_base64(image_path)
    payload = {
        "model": "llava",
        "prompt": question,
        "images": [b64_image],
        "stream": False,
    }
    resp = requests.post(f"{config.OLLAMA_BASE_URL}/api/generate", json=payload, timeout=60)
    resp.raise_for_status()
    result = resp.json().get("response", "No response from model")
    log.info("Screen analysis complete (Ollama Vision)")
    return result


# Handler map for router registration
HANDLERS = {
    "analyze_screen": analyze_screen,
}
