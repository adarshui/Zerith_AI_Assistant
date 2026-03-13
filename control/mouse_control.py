"""
Zerith AI — Mouse Control
Move, click, scroll, and interact with screen elements using pyautogui.
"""

import pyautogui
from utils.logger import log

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True


def move_to(x: int, y: int, duration: float = 0.3) -> str:
    """Move mouse to absolute screen position."""
    log.info(f"Moving mouse to ({x}, {y})")
    pyautogui.moveTo(x, y, duration=duration)
    return f"Moved to ({x}, {y})"


def click(x: int = None, y: int = None, button: str = "left") -> str:
    """Click at current position or specified coordinates."""
    if x is not None and y is not None:
        log.info(f"Clicking at ({x}, {y}) [{button}]")
        pyautogui.click(x, y, button=button)
        return f"Clicked at ({x}, {y})"
    else:
        log.info(f"Clicking at current position [{button}]")
        pyautogui.click(button=button)
        pos = pyautogui.position()
        return f"Clicked at ({pos.x}, {pos.y})"


def double_click(x: int = None, y: int = None) -> str:
    """Double-click at current position or specified coordinates."""
    if x is not None and y is not None:
        log.info(f"Double-clicking at ({x}, {y})")
        pyautogui.doubleClick(x, y)
        return f"Double-clicked at ({x}, {y})"
    else:
        log.info("Double-clicking at current position")
        pyautogui.doubleClick()
        pos = pyautogui.position()
        return f"Double-clicked at ({pos.x}, {pos.y})"


def right_click(x: int = None, y: int = None) -> str:
    """Right-click at current position or specified coordinates."""
    return click(x, y, button="right")


def scroll(amount: int) -> str:
    """Scroll up (positive) or down (negative)."""
    direction = "up" if amount > 0 else "down"
    log.info(f"Scrolling {direction} by {abs(amount)}")
    pyautogui.scroll(amount)
    return f"Scrolled {direction} by {abs(amount)}"


def drag_to(x: int, y: int, duration: float = 0.5) -> str:
    """Drag from current position to target coordinates."""
    log.info(f"Dragging to ({x}, {y})")
    pyautogui.dragTo(x, y, duration=duration)
    return f"Dragged to ({x}, {y})"


def get_position() -> str:
    """Return current mouse position."""
    pos = pyautogui.position()
    return f"Mouse at ({pos.x}, {pos.y})"


# Handler map for router registration
HANDLERS = {
    "move_to": move_to,
    "click": click,
    "double_click": double_click,
    "right_click": right_click,
    "scroll": scroll,
    "drag_to": drag_to,
    "get_position": get_position,
}
