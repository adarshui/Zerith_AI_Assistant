"""
Zerith AI — Text to Speech
pyttsx3-based text-to-speech engine.
"""

from utils.logger import log
import config


_engine = None


def _get_engine():
    """Lazy-initialize the TTS engine."""
    global _engine
    if _engine is None:
        try:
            import pyttsx3
            _engine = pyttsx3.init()
            _engine.setProperty("rate", config.TTS_RATE)
            log.debug("TTS engine initialized")
        except Exception as e:
            log.warning(f"TTS init failed: {e}")
    return _engine


def speak(text: str) -> str:
    """Speak text aloud."""
    if not config.ENABLE_VOICE:
        return "Voice output is disabled. Set ENABLE_VOICE=true in .env"

    engine = _get_engine()
    if not engine:
        return "TTS engine not available"

    log.info(f"[cyan]Speaking:[/cyan] {text[:80]}...")
    try:
        engine.say(text)
        engine.runAndWait()
        return f"Spoke: {text[:80]}..."
    except Exception as e:
        log.warning(f"TTS failed: {e}")
        return f"Could not speak: {e}"


# Handler map
HANDLERS = {
    "speak": speak,
}
