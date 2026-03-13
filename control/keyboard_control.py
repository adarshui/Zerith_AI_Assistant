"""
Zerith AI — Keyboard Control
Type text, press keys, and execute keyboard shortcuts using pyautogui.
"""

import time
import pyautogui
from utils.logger import log

# Safety — prevent pyautogui from moving too fast
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True  # Move mouse to corner to abort


def type_text(text: str, interval: float = 0.03) -> str:
    """Type text character by character."""
    log.info(f"Typing: {text[:50]}{'...' if len(text) > 50 else ''}")
    pyautogui.typewrite(text, interval=interval)
    return f"Typed {len(text)} characters"


def press_key(key: str) -> str:
    """Press a single key (e.g. 'enter', 'tab', 'escape')."""
    log.info(f"Pressing key: {key}")
    pyautogui.press(key)
    return f"Pressed {key}"


def hotkey(*keys: str) -> str:
    """Execute a keyboard shortcut (e.g. hotkey('ctrl', 'c'))."""
    combo = "+".join(keys)
    log.info(f"Hotkey: {combo}")
    pyautogui.hotkey(*keys)
    return f"Executed hotkey: {combo}"


def write_text(text: str) -> str:
    """Write text using clipboard (handles special characters better)."""
    import subprocess
    log.info(f"Writing via clipboard: {text[:50]}...")
    subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.1)
    return f"Written {len(text)} characters via clipboard"


# Handler map for router registration
HANDLERS = {
    "type_text": type_text,
    "press_key": press_key,
    "hotkey": hotkey,
    "write_text": write_text,
}
