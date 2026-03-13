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

# ── Initialize AI modules ───────────────────────────────
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

    from memory.conversation_store import HANDLERS as conv_handlers
    router.register_module("memory", conv_handlers)

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
        # Get relevant context from conversation memory
        from memory.conversation_store import get_context_for_query
        context = get_context_for_query(user_input)
        
        # Get plan from AI with context
        plan = planner.plan(user_input, context=context if context else "")

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

        # Save conversation to persistent memory
        try:
            from memory.conversation_store import add_conversation
            add_conversation(user_input, response_text)
        except Exception as conv_err:
            log.debug(f"Failed to save conversation: {conv_err}")

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


@socketio.on("memory_search")
def handle_memory_search(data):
    """Search past conversations for relevant context."""
    query = data.get("query", "").strip()
    if not query:
        emit("memory_results", {"results": "No search query provided", "error": True})
        return
    
    try:
        from memory.conversation_store import search_conversations
        results = search_conversations(query, limit=5)
        emit("memory_results", {"results": results})
    except Exception as e:
        log.warning(f"Memory search error: {e}")
        emit("memory_results", {"results": f"Search failed: {e}", "error": True})


@socketio.on("memory_stats")
def handle_memory_stats():
    """Get conversation memory statistics."""
    try:
        from memory.conversation_store import get_conversation_stats
        stats = get_conversation_stats()
        emit("memory_stats_result", {"stats": stats})
    except Exception as e:
        log.warning(f"Memory stats error: {e}")
        emit("memory_stats_result", {"stats": f"Error: {e}", "error": True})


@socketio.on("clear_memory")
def handle_clear_memory():
    """Clear all conversation memories."""
    try:
        from memory.conversation_store import clear_conversations
        result = clear_conversations()
        emit("memory_cleared", {"result": result})
    except Exception as e:
        log.warning(f"Clear memory error: {e}")
        emit("memory_cleared", {"result": f"Error: {e}", "error": True})


@socketio.on("voice_input")
def handle_voice_input(data):
    """Process voice input from the browser."""
    text = data.get("text", "").strip()
    if not text:
        emit("chat_response", {"message": "No speech detected", "error": True})
        return

    log.info(f"Voice input: {text}")
    # Echo back the recognized text - client will send as chat message
    emit("voice_recognized", {"text": text})


@socketio.on("tts_request")
def handle_tts_request(data):
    """Handle TTS request - send back to browser for speech synthesis."""
    text = data.get("text", "").strip()
    if not text:
        return

    log.info(f"TTS request: {text[:50]}...")
    # Send back to browser for speech synthesis
    emit("tts_ready", {"text": text})


@socketio.on("image_analyze")
def handle_image_analyze(data):
    """Analyze an image from the browser."""
    image_data = data.get("image", "")
    if not image_data:
        emit("image_result", {"result": "No image provided", "error": True})
        return

    log.info("Image analysis request from browser")
    emit("thinking", {"status": True})

    try:
        # Save the image to a temporary file
        import base64
        import uuid
        from pathlib import Path

        # Extract base64 data
        if ";base64," in image_data:
            header, image_data = image_data.split(";base64,")

        image_bytes = base64.b64decode(image_data)

        # Save to temp file
        temp_filename = f"browser_capture_{uuid.uuid4().hex[:8]}.png"
        temp_path = config.SCREENSHOTS_DIR / temp_filename

        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        log.info(f"Saved image to: {temp_path}")

        # Analyze the image
        from vision.screen_analyzer import analyze_screen
        result = analyze_screen(str(temp_path), "What is shown in this image? Describe the content in detail.")

        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass

        emit("image_result", {"result": result})

    except Exception as e:
        log.warning(f"Image analysis error: {e}")
        emit("image_result", {"result": f"Could not analyze image: {e}", "error": True})

    emit("thinking", {"status": False})


# ── Self-Coding SocketIO Events ─────────────────────────

@socketio.on("modify_file")
def handle_modify_file(data):
    """
    Handle direct file modification requests from the UI.
    This enables self-coding capability from the web interface.
    """
    path = data.get("path", "").strip()
    content = data.get("content", None)
    search = data.get("search", None)
    replace = data.get("replace", None)

    if not path:
        emit("file_modified", {"success": False, "error": "No file path provided"})
        return

    log.info(f"[SELF-MODIFY] Request to edit: {path}")

    try:
        from control.file_operations import edit_file
        
        if content is not None:
            result = edit_file(path, content=content)
        elif search is not None and replace is not None:
            result = edit_file(path, search=search, replace=replace)
        else:
            result = edit_file(path)

        emit("file_modified", {
            "success": "File updated" in result or "File edited" in result,
            "result": result,
            "path": path
        })

    except Exception as e:
        log.warning(f"File modification error: {e}")
        emit("file_modified", {"success": False, "error": str(e)})


@socketio.on("read_file_request")
def handle_read_file_request(data):
    """
    Handle file read requests from the UI.
    Allows viewing any file in the project.
    """
    path = data.get("path", "").strip()

    if not path:
        emit("file_content", {"success": False, "error": "No file path provided"})
        return

    log.info(f"[SELF-MODIFY] Request to read: {path}")

    try:
        from control.file_operations import read_file
        content = read_file(path)
        emit("file_content", {
            "success": True,
            "path": path,
            "content": content
        })

    except Exception as e:
        log.warning(f"File read error: {e}")
        emit("file_content", {"success": False, "error": str(e)})


@socketio.on("ui_change_request")
def handle_ui_change_request(data):
    """
    Handle UI change requests - a simplified interface for common UI modifications.
    Supports: theme change, color changes
    """
    change_type = data.get("type", "").strip()
    value = data.get("value", "")
    
    log.info(f"[UI CHANGE] Request: {change_type} = {value}")
    
    try:
        from control.file_operations import edit_file, read_file
        
        if change_type == "theme":
            # Change color scheme in CSS
            theme_map = {
                "blue": ("#007bff", "#0056b3"),
                "green": ("#28a745", "#1e7e34"),
                "purple": ("#6f42c1", "#4a2c81"),
                "red": ("#dc3545", "#a71d2a"),
                "dark": ("#343a40", "#212529"),
            }
            
            if value.lower() not in theme_map:
                emit("ui_changed", {"success": False, "error": f"Unknown theme: {value}. Try: blue, green, purple, red, dark"})
                return
            
            primary, darker = theme_map[value.lower()]
            
            # Read current CSS
            css_path = "Zerith/static/style.css"
            css_content = read_file(css_path)
            
            # Simple replacement for primary color
            if "--primary-color" in css_content:
                result = edit_file(css_path, search="--primary-color: #007bff;", replace=f"--primary-color: {primary};")
            else:
                result = edit_file(css_path, search="#007bff", replace=primary)
            
            emit("ui_changed", {
                "success": True,
                "message": f"Theme changed to {value}. Refresh browser to see changes.",
                "refresh": True
            })
            
        elif change_type == "background":
            # Change background color
            css_path = "Zerith/static/style.css"
            bg_color = value if value.startswith("#") else f"#{value}"
            
            if "background-color: #f5f5f5;" in read_file(css_path):
                result = edit_file(css_path, search="background-color: #f5f5f5;", replace=f"background-color: {bg_color};")
            
            emit("ui_changed", {
                "success": True,
                "message": f"Background color changed. Refresh browser to see changes.",
                "refresh": True
            })
            
        else:
            emit("ui_changed", {"success": False, "error": f"Unknown change type: {change_type}"})
            
    except Exception as e:
        log.warning(f"UI change error: {e}")
        emit("ui_changed", {"success": False, "error": str(e)})


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
