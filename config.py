"""
Zerith AI Assistant — Central Configuration
All settings are loaded from environment variables or defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
LOGS_DIR = DATA_DIR / "logs"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

# Ensure directories exist
for d in [DATA_DIR, MEMORY_DIR, LOGS_DIR, SCREENSHOTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# AI Model Settings
# ──────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")            # "ollama", "openai", or "groq"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

# ──────────────────────────────────────────────
# Vision Settings
# ──────────────────────────────────────────────
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# ──────────────────────────────────────────────
# Safety Settings
# ──────────────────────────────────────────────
REQUIRE_CONFIRMATION_FOR = [
    "delete_file",
    "delete_folder",
    "run_command",
    "modify_system",
    "install_package",
    "edit_file",      # Self-modification requires confirmation
]

# ──────────────────────────────────────────────
# Voice Settings
# ──────────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
TTS_RATE = int(os.getenv("TTS_RATE", "175"))

# ──────────────────────────────────────────────
# Memory Settings
# ──────────────────────────────────────────────
CHROMA_PERSIST_DIR = str(MEMORY_DIR / "chroma_db")
PREFERENCES_FILE = str(MEMORY_DIR / "user_preferences.json")
MEMORY_STORE_FILE = str(MEMORY_DIR / "memory_store.json")
CONVERSATION_DB_FILE = str(MEMORY_DIR / "conversations.db")
MAX_CONTEXT_MEMORIES = 5  # Number of relevant memories to load into context

# ──────────────────────────────────────────────
# Feature Flags
# ──────────────────────────────────────────────
ENABLE_VOICE = os.getenv("ENABLE_VOICE", "false").lower() == "true"
ENABLE_WEB = os.getenv("ENABLE_WEB", "true").lower() == "true"
ENABLE_VISION = os.getenv("ENABLE_VISION", "true").lower() == "true"
