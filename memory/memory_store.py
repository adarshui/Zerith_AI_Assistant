"""
Zerith AI — Memory Store
JSON-based persistent key-value and text storage.
"""

import json
from pathlib import Path
from typing import Any, Optional
from utils.logger import log
import config


class MemoryStore:
    """Simple JSON-backed key-value memory."""

    def __init__(self, file_path: str = None):
        self.file_path = Path(file_path or config.MEMORY_STORE_FILE)
        self._data: dict = {}
        self._load()

    def _load(self):
        """Load memory from disk."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                log.debug(f"Memory loaded: {len(self._data)} entries")
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"Could not load memory: {e}")
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        """Persist memory to disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def store(self, key: str, value: Any) -> str:
        """Store a key-value pair."""
        self._data[key] = value
        self._save()
        log.info(f"Stored: {key}")
        return f"Stored '{key}'"

    def retrieve(self, key: str) -> Any:
        """Retrieve a value by key."""
        value = self._data.get(key)
        if value is None:
            return f"No memory found for '{key}'"
        return value

    def delete(self, key: str) -> str:
        """Delete a memory entry."""
        if key in self._data:
            del self._data[key]
            self._save()
            log.info(f"Deleted memory: {key}")
            return f"Deleted '{key}'"
        return f"Key '{key}' not found"

    def list_keys(self) -> str:
        """List all stored keys."""
        if not self._data:
            return "Memory is empty"
        return "\n".join(f"  • {k}" for k in sorted(self._data.keys()))

    def search(self, query: str) -> str:
        """Simple text search across keys and string values."""
        query_lower = query.lower()
        matches = []
        for k, v in self._data.items():
            if query_lower in k.lower() or (isinstance(v, str) and query_lower in v.lower()):
                matches.append(f"  {k}: {v}")
        return "\n".join(matches) if matches else "No matches found"


# Singleton instance
_store = None


def _get_store() -> MemoryStore:
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store


def store(key: str, value: str) -> str:
    return _get_store().store(key, value)


def retrieve(key: str) -> str:
    return str(_get_store().retrieve(key))


def delete(key: str) -> str:
    return _get_store().delete(key)


def list_memories() -> str:
    return _get_store().list_keys()


def search_memory(query: str) -> str:
    return _get_store().search(query)


# Handler map for router registration
HANDLERS = {
    "store": store,
    "retrieve": retrieve,
    "delete": delete,
    "list": list_memories,
    "search": search_memory,
}
