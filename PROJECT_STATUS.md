# Zerith AI — Project Status & Roadmap

> **Last Updated:** 2026-03-13
> **Rule:** Before starting any new feature, add it to **Pending Features** first, then execute.

---

## ✅ Completed Features

### Core AI Engine
- [x] LLM provider abstraction (`core/brain.py`) — supports Groq, Ollama, OpenAI
- [x] Groq cloud LLM integration (free, fast, no local RAM required)
- [x] Ollama local LLM support (fallback)
- [x] OpenAI API support (fallback)
- [x] JSON-structured responses with thought/plan/response format
- [x] Conversation history tracking (last 10 exchanges)
- [x] System prompt with full tool catalog
- [x] Fixed deprecated `langchain_community` → `langchain_openai` import

### Task Planning & Execution
- [x] Task planner (`core/task_planner.py`) — converts natural language → structured task steps
- [x] Agent router (`core/agent_router.py`) — dispatches steps to tool handlers
- [x] Task executor (`automation/task_executor.py`) — executes plans with retries
- [x] Workflow engine (`automation/workflow_engine.py`) — saved automation workflows
- [x] Safety/permission system (`utils/permissions.py`) — confirms critical actions

### Tool Modules (43 Actions Registered)
- [x] **Keyboard** (4): type_text, press_key, hotkey, write_text
- [x] **Mouse** (7): move_to, click, double_click, scroll, etc.
- [x] **System** (4): run_command, open_application, get_system_info, list_directory
- [x] **File** (4): read_file, write_file, find_file, list_directory
- [x] **Vision** (varies): screen capture, screen analysis, OCR text reading
- [x] **Web** (varies): web search, page scraping, content extraction
- [x] **Memory** (8): key-value store, vector memory (ChromaDB), user preferences
- [x] **Automation** (1): workflow execution

### User Interfaces
- [x] CLI interface (`ui/cli_interface.py`) — rich terminal UI with panels and tables
- [x] Chat interface (`ui/chat_interface.py`) — conversational terminal experience
- [x] **Web UI** (`web_ui.py`) — Flask + SocketIO browser-based GUI
  - [x] Dark theme with glassmorphism design
  - [x] Sidebar with status, tools list
  - [x] Real-time chat via WebSocket
  - [x] Welcome screen with quick-action hint cards
  - [x] Plan display cards with step-by-step execution
  - [x] Markdown rendering in responses
  - [x] `python main.py --ui` launches web UI

### Configuration & Setup
- [x] Environment-based config (`config.py`, `.env`)
- [x] Feature flags (vision, web, voice toggles)
- [x] `.gitignore` excludes secrets and data
- [x] Pushed to GitHub: https://github.com/adarshui/Zerith

---

## 🔧 Pending Fixes
- [ ] Web UI response sometimes shows raw JSON instead of clean text (partially fixed)
- [ ] Banner model display mismatch between config default and actual running model

---

## 📋 Pending Features

### High Priority
- [ ] **Electron/Desktop wrapper** — package web UI as a native desktop app
- [ ] **Streaming responses** — show LLM output token-by-token instead of waiting
- [ ] **Conversation persistence** — save/load chat history across sessions
- [ ] **Screenshot + Vision in Web UI** — display captured screenshots in chat

### Medium Priority
- [ ] **Voice input/output** — speech-to-text (Whisper) and text-to-speech (pyttsx3)
- [ ] **Plugin system** — allow users to add custom tool modules
- [ ] **Settings page in Web UI** — change provider, model, toggle features from UI
- [ ] **Dark/light theme toggle** in Web UI
- [ ] **Multi-step plan confirmation** — let user approve/reject individual steps before execution

### Low Priority
- [ ] **System tray icon** — run in background, activate with hotkey
- [ ] **Scheduled tasks** — run workflows at set times
- [ ] **Clipboard monitoring** — detect copied text and offer actions
- [ ] **Multi-language support** — UI translations
- [ ] **Usage analytics dashboard** — show command frequency, tool usage stats

---

## 📁 Project Structure

```
zerith-ai/
├── main.py              # Entry point (--ui for web, default CLI)
├── web_ui.py            # Flask + SocketIO web server
├── config.py            # Central configuration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example         # Template for .env
├── core/
│   ├── brain.py         # LLM reasoning engine
│   ├── task_planner.py  # Natural language → task plans
│   └── agent_router.py  # Dispatches tasks to tools
├── control/
│   ├── keyboard_control.py
│   ├── mouse_control.py
│   ├── system_commands.py
│   └── file_operations.py
├── automation/
│   ├── task_executor.py
│   └── workflow_engine.py
├── vision/
│   ├── screen_capture.py
│   ├── screen_analyzer.py
│   └── ocr_reader.py
├── web/
│   ├── web_search.py
│   ├── scraper.py
│   └── content_extractor.py
├── memory/
│   ├── memory_store.py
│   ├── vector_memory.py
│   └── user_preferences.py
├── ui/
│   ├── cli_interface.py
│   └── chat_interface.py
├── utils/
│   ├── logger.py
│   └── permissions.py
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── app.js
└── data/               # Runtime data (not in git)
```
