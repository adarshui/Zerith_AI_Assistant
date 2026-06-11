# Zerith — Personal AI Desktop Assistant

Zerith is a local AI automation assistant that runs on your laptop. It understands natural language, controls your computer, reads the screen, manages files, searches the web, and automates complex multi-step workflows — all from a single interface.

---

## What Zerith Can Do

- Understand natural language commands
- Control mouse, keyboard, and system inputs
- Capture and analyze the screen with OCR
- Access and manage files and folders
- Execute terminal and system commands
- Search the web and extract useful information
- Automate multi-step workflows
- Maintain long-term memory about you and your preferences

### Example

```
User: Zerith, open my Django project and run the server.

Zerith:
  1. Locate project folder
  2. Open terminal
  3. Navigate to project
  4. Run command
```

---

## Architecture

Zerith is built as a collection of specialized modules that work together under a central reasoning engine.

```
Zerith
├── Zerith Core       — AI reasoning engine
├── Zerith Planner    — Task breakdown and sequencing
├── Zerith Control    — Mouse, keyboard, and system control
├── Zerith Vision     — Screen capture and OCR
├── Zerith Web        — Web search and scraping
├── Zerith Memory     — Long-term knowledge store
├── Zerith Tasks      — Workflow automation engine
└── Zerith Interface  — CLI and voice interface
```

---

## Project Structure

```
zerith-ai/
│
├── main.py
├── config.py
├── requirements.txt
│
├── core/
│   ├── brain.py
│   ├── task_planner.py
│   └── agent_router.py
│
├── control/
│   ├── keyboard_control.py
│   ├── mouse_control.py
│   └── system_commands.py
│
├── vision/
│   ├── screen_capture.py
│   ├── screen_analyzer.py
│   └── ocr_reader.py
│
├── web/
│   ├── web_search.py
│   ├── scraper.py
│   └── content_extractor.py
│
├── memory/
│   ├── memory_store.py
│   ├── vector_memory.py
│   └── user_preferences.py
│
├── automation/
│   ├── task_executor.py
│   └── workflow_engine.py
│
├── voice/
│   ├── speech_to_text.py
│   └── text_to_speech.py
│
├── ui/
│   ├── cli_interface.py
│   └── chat_interface.py
│
└── utils/
    ├── logger.py
    └── permissions.py
```

---

## Technology Stack

| Category | Tools |
|---|---|
| Language | Python |
| AI Models | Ollama (local LLM), OpenAI API (optional) |
| AI Frameworks | LangChain, CrewAI |
| Computer Control | pyautogui, pynput |
| Screen Vision | mss, OpenCV, pytesseract |
| Web Research | Playwright, BeautifulSoup, requests |
| Memory | ChromaDB, FAISS |
| Voice | Whisper, pyttsx3 |

---

## Implementation Roadmap

### Phase 1 — Zerith Core
Build the LLM-based reasoning system that converts natural language commands into structured, executable tasks.

```
User Command → LLM → Task Planner → Tool Execution
```

### Phase 2 — Zerith Control
Enable Zerith to interact with the computer: mouse movement, clicking, typing, opening applications, and running terminal commands.

### Phase 3 — Zerith Vision
Allow Zerith to understand what's on screen by capturing screenshots, extracting text via OCR, and sending screen context to the LLM.

### Phase 4 — Zerith Web Agent
Enable browser automation, search queries, result scraping, and content summarization.

### Phase 5 — Zerith Memory
Store user preferences, project paths, frequent workflows, and other useful context. Use vector search for fast, relevant retrieval.

### Phase 6 — Zerith Task Automation
Execute full multi-step tasks automatically. Example: deploy a project by opening a terminal, navigating to the folder, running the deployment command, and monitoring logs.

---

## Safety

Zerith will always ask for explicit permission before performing critical or irreversible operations, including:

- Deleting files or folders
- Executing system-level commands
- Modifying important directories

No destructive action is taken without user confirmation.

---

## Design Goals

- **Modular** — each capability lives in its own module and can be developed or replaced independently
- **Tool-based** — the LLM decides which tool to call based on the task at hand
- **Extensible** — built to grow into a full-featured AI desktop automation platform
- **Local-first** — core functionality runs on-device via Ollama, with optional cloud model support

---

## Getting Started

> Full setup instructions will be added as each phase is implemented.

```bash
git clone https://github.com/your-username/zerith-ai.git
cd zerith-ai
pip install -r requirements.txt
python main.py
```

---

## License

MIT License — see `LICENSE` for details.
