"""
Zerith AI — OCR Reader
Extract text from screenshots and images using pytesseract.
"""

from pathlib import Path
from utils.logger import log
import config


def read_text_from_image(image_path: str, lang: str = "eng") -> str:
    """
    Extract text from an image file using Tesseract OCR.
    """
    if not Path(image_path).exists():
        return f"Image not found: {image_path}"

    try:
        import pytesseract
        from PIL import Image

        pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        text = text.strip()

        log.info(f"OCR extracted {len(text)} characters from {Path(image_path).name}")
        return text or "(no text found in image)"

    except Exception as e:
        log.warning(f"OCR failed: {e}")
        return f"OCR failed: {e}"


def read_text_from_screen() -> str:
    """Capture the screen and extract text in one step."""
    from vision.screen_capture import capture_screen

    screenshot_path = capture_screen()
    if screenshot_path.startswith("Screen capture failed"):
        return screenshot_path
    return read_text_from_image(screenshot_path)


# Handler map for router registration
HANDLERS = {
    "read_text": read_text_from_image,
    "read_screen_text": read_text_from_screen,
}
