"""
Zerith AI — Speech to Text
Whisper-based speech recognition from microphone input.
"""

from utils.logger import log
import config


def listen(duration: int = 5) -> str:
    """
    Record audio from microphone and transcribe with Whisper.
    duration: recording length in seconds.
    """
    if not config.ENABLE_VOICE:
        return "Voice input is disabled. Set ENABLE_VOICE=true in .env"

    log.info(f"[cyan]Listening for {duration} seconds...[/cyan]")

    try:
        import whisper
        import sounddevice as sd
        import numpy as np
        import tempfile
        import soundfile as sf

        # Record audio
        samplerate = 16000
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()

        # Save to temp file
        temp_path = tempfile.mktemp(suffix=".wav")
        sf.write(temp_path, audio, samplerate)

        # Transcribe
        model = whisper.load_model(config.WHISPER_MODEL)
        result = model.transcribe(temp_path)
        text = result["text"].strip()

        log.info(f"[green]Heard:[/green] {text}")
        return text or "(no speech detected)"

    except ImportError as e:
        log.warning(f"Voice dependency missing: {e}")
        return f"Voice not available — install: pip install openai-whisper sounddevice soundfile"
    except Exception as e:
        log.warning(f"Speech-to-text failed: {e}")
        return f"Could not understand audio: {e}"


# Handler map
HANDLERS = {
    "listen": listen,
}
