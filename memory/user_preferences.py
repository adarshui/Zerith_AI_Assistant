"""
Zerith AI — User Preferences
Track and retrieve user preferences with auto-learning from usage patterns.
"""

import json
from pathlib import Path
from collections import Counter
from utils.logger import log
import config


class UserPreferences:
    """Manage user preferences and usage patterns."""

    def __init__(self, file_path: str = None):
        self.file_path = Path(file_path or config.PREFERENCES_FILE)
        self._prefs: dict = {"settings": {}, "patterns": {}, "favorites": {}}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._prefs = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._prefs, f, indent=2, ensure_ascii=False)

    # ── Settings ─────────────────────────────────────────

    def set_preference(self, key: str, value: str) -> str:
        """Set a user preference."""
        self._prefs["settings"][key] = value
        self._save()
        log.info(f"Preference set: {key} = {value}")
        return f"Set '{key}' = '{value}'"

    def get_preference(self, key: str, default: str = "") -> str:
        """Get a user preference."""
        return self._prefs["settings"].get(key, default)

    def list_preferences(self) -> str:
        """List all preferences."""
        settings = self._prefs.get("settings", {})
        if not settings:
            return "No preferences set"
        return "\n".join(f"  {k}: {v}" for k, v in sorted(settings.items()))

    # ── Usage Pattern Tracking ───────────────────────────

    def record_pattern(self, category: str, value: str):
        """Record a usage pattern for auto-learning."""
        if category not in self._prefs["patterns"]:
            self._prefs["patterns"][category] = []
        self._prefs["patterns"][category].append(value)
        # Keep last 100 entries per category
        self._prefs["patterns"][category] = self._prefs["patterns"][category][-100:]
        self._save()

    def get_frequent(self, category: str, top_n: int = 5) -> list[str]:
        """Get the most frequently used items in a category."""
        items = self._prefs["patterns"].get(category, [])
        counter = Counter(items)
        return [item for item, _ in counter.most_common(top_n)]

    # ── Favorites ────────────────────────────────────────

    def add_favorite(self, category: str, item: str) -> str:
        """Add an item to favorites."""
        if category not in self._prefs["favorites"]:
            self._prefs["favorites"][category] = []
        if item not in self._prefs["favorites"][category]:
            self._prefs["favorites"][category].append(item)
            self._save()
        return f"Added '{item}' to {category} favorites"

    def get_favorites(self, category: str) -> list[str]:
        """Get favorite items for a category."""
        return self._prefs["favorites"].get(category, [])


# Singleton
_prefs = None


def _get_prefs() -> UserPreferences:
    global _prefs
    if _prefs is None:
        _prefs = UserPreferences()
    return _prefs


def set_pref(key: str, value: str) -> str:
    return _get_prefs().set_preference(key, value)


def get_pref(key: str) -> str:
    return _get_prefs().get_preference(key) or f"No preference set for '{key}'"


def list_prefs() -> str:
    return _get_prefs().list_preferences()


# Handler map for router registration
HANDLERS = {
    "set_preference": set_pref,
    "get_preference": get_pref,
    "list_preferences": list_prefs,
}
