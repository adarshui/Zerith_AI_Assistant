"""
Zerith AI — Screen Capture
Capture full screen or specific regions using mss.
"""

import os
import time
from pathlib import Path
from utils.logger import log
import config


def capture_screen(region: dict = None, save_path: str = None) -> str:
    """
    Capture the screen (full or region) and save as PNG.
    region: {"left": 0, "top": 0, "width": 1920, "height": 1080}
    Returns the path to the saved screenshot.
    """
    try:
        import mss
        import mss.tools

        with mss.mss() as sct:
            if region:
                monitor = region
            else:
                monitor = sct.monitors[1]  # Primary monitor

            screenshot = sct.grab(monitor)

            if not save_path:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_path = str(config.SCREENSHOTS_DIR / f"screen_{timestamp}.png")

            mss.tools.to_png(screenshot.rgb, screenshot.size, output=save_path)
            log.info(f"[green]Screenshot saved:[/green] {save_path}")
            return save_path

    except Exception as e:
        log.warning(f"Screen capture failed: {e}")
        return f"Screen capture failed: {e}"


def capture_region(left: int, top: int, width: int, height: int) -> str:
    """Capture a specific region of the screen."""
    region = {"left": left, "top": top, "width": width, "height": height}
    return capture_screen(region=region)


def get_screen_size() -> str:
    """Return the primary monitor resolution."""
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            return f"{monitor['width']}x{monitor['height']}"
    except Exception as e:
        return f"Could not get screen size: {e}"


# Handler map for router registration
HANDLERS = {
    "capture_screen": capture_screen,
    "capture_region": capture_region,
    "get_screen_size": get_screen_size,
}
