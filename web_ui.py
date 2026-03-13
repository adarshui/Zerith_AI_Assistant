"""
Zerith AI — Web UI Server
Flask + SocketIO backend for the graphical chat interface.
"""

import sys
import os
import json
import threading
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

import config
from utils.logger import log
from core.brain import Brain
from core.task_planner import TaskPlanner
from core.agent_router import AgentRouter
from automation.task_executor import TaskExecutor
from automation.workflow_engine import WorkflowEngine


# ── Flask App ────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "zerith-ai-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Initialize AI modules ────────────────────────────────
brain = None
planner = None
router = None
executor = None
workflow_engine = None


def init_ai():
    """Initialize all AI modules."""
    global brain, planner, router, executor, workflow_engine

    log.info("Initializing Zerith AI...")

    brain = Brain()
    planner = TaskPlanner(brain)
    router = AgentRouter()
    executor = TaskExecutor(router)
    workflow_engine = WorkflowEngine()

    # Register all tools
    from control.keyboard_control import HANDLERS as kb_handlers
    router.register_module("keyboard", kb_handlers)

    from control.mouse_control import HANDLERS as mouse_handlers
    router.register_module("mouse", mouse_handlers)

    from control.system_commands import HANDLERS as sys_handlers
    router.register_module("system", sys_handlers)

    if config.ENABLE_VISION:
        from vision.screen_capture import HANDLERS as cap_handlers
        router.register_module("vision", cap_handlers)
        from vision.screen_analyzer import HANDLERS as sa_handlers
        router.register_module("vision", sa_handlers)
        from vision.ocr_reader import HANDLERS as ocr_handlers
        router.register_module("vision", ocr_handlers)

    if config.ENABLE_WEB:
        from web.web_search import HANDLERS as ws_handlers
        router.register_module("web", ws_handlers)
        from web.scraper import HANDLERS as scraper_handlers
        router.register_module("web", scraper_handlers)
        from web.content_extractor import HANDLERS as ce_handlers
        router.register_module("web", ce_handlers)

    from memory.memory_store import HANDLERS as mem_handlers
    router.register_module("memory", mem_handlers)

    from memory.vector_memory import HANDLERS as vec_handlers
    router.register_module("memory", vec_handlers)

    from memory.user_preferences import HANDLERS as pref_handlers
    router.register_module("preferences", pref_handlers)

    from control.file_operations import HANDLERS as file_handlers
    router.register_module("file", file_handlers)

    from automation.workflow_engine import HANDLERS as wf_handlers
    router.register_module("automation", wf_handlers)

    tool_count = sum(len(v) for v in router.available_tools.values())
    log.info(f"✓ Registered {tool_count} tool actions")
    log.info("Zerith AI is ready!")


# ── Routes ───────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main chat UI."""
    model_map = {
        "groq": config.GROQ_MODEL,
        "ollama": config.OLLAMA_MODEL,
        "openai": config.OPENAI_MODEL,
    }
    active_model = model_map.get(config.LLM_PROVIDER, "unknown")
    return render_template("index.html",
                           provider=config.LLM_PROVIDER,
                           model=active_model)


@app.route("/api/tools")
def get_tools():
    """Return available tools as JSON."""
    tools = router.available_tools
    return json.dumps(tools)


@app.route("/api/status")
def get_status():
    """Return system status as JSON."""
    model_map = {
        "groq": config.GROQ_MODEL,
        "ollama": config.OLLAMA_MODEL,
        "openai": config.OPENAI_MODEL,
    }
    return json.dumps({
        "provider": config.LLM_PROVIDER,
        "model": model_map.get(config.LLM_PROVIDER, "unknown"),
        "vision": config.ENABLE_VISION,
        "web": config.ENABLE_WEB,
        "voice": config.ENABLE_VOICE,
        "tools": sum(len(v) for v in router.available_tools.values()),
    })


# ── SocketIO Events ─────────────────────────────────────

@socketio.on("connect")
def handle_connect():
    """Client connected."""
    log.info("Web client connected")
    emit("status", {"connected": True})


@socketio.on("disconnect")
def handle_disconnect():
    """Client disconnected."""
    log.info("Web client disconnected")


@socketio.on("chat_message")
def handle_chat(data):
    """Process a chat message from the user."""
    user_input = data.get("message", "").strip()
    if not user_input:
        return

    log.info(f"Web UI message: {user_input}")

    # Send thinking indicator
    emit("thinking", {"status": True})

    try:
        # Get plan from AI
        plan = planner.plan(user_input)

        # Clean the response text — extract from JSON wrapper if needed
        response_text = plan.response
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict) and "response" in parsed:
                response_text = parsed["response"]
        except (json.JSONDecodeError, TypeError):
            pass

        if plan.steps:
            # Send the plan for review
            steps_data = []
            for step in plan.steps:
                steps_data.append({
                    "step": step.step,
                    "tool": step.tool,
                    "action": step.action,
                    "params": step.params,
                    "status": step.status,
                })

            emit("plan", {
                "thought": plan.thought,
                "response": response_text,
                "steps": steps_data,
            })

            # Auto-execute the plan
            emit("executing", {"status": True})

            summary = executor.execute_plan(plan)

            # Send results
            results_data = []
            for step in plan.steps:
                results_data.append({
                    "step": step.step,
                    "tool": step.tool,
                    "action": step.action,
                    "status": step.status,
                    "result": step.result,
                })

            emit("plan_result", {
                "response": response_text,
                "results": results_data,
                "summary": {
                    "total": summary["total_steps"],
                    "success": summary["success"],
                    "failed": summary["failed"],
                },
            })
        else:
            # Conversational response only
            emit("chat_response", {"message": response_text})

    except Exception as e:
        log.warning(f"Chat error: {e}")
        emit("chat_response", {"message": f"An error occurred: {e}", "error": True})

    emit("thinking", {"status": False})

    # Record usage
    try:
        from memory.user_preferences import _get_prefs
        _get_prefs().record_pattern("commands", user_input)
    except Exception:
        pass


@socketio.on("clear_history")
def handle_clear():
    """Clear conversation history."""
    brain.reset_history()
    emit("history_cleared", {"status": True})


# ── Launch ───────────────────────────────────────────────

def start_web_ui(host="127.0.0.1", port=5000):
    """Start the web UI server."""
    init_ai()

    # Open browser after a short delay
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(f"http://{host}:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    print(f"\n  ⚡ Zerith AI Web UI running at http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")

    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    start_web_ui()
