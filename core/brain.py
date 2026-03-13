"""
Zerith AI — Brain (LLM Reasoning Engine)
Connects to Ollama (local) or OpenAI (fallback) and handles all LLM interactions.
"""

import json
from typing import Optional
from utils.logger import log
import config

# ──────────────────────────────────────────────
# LLM Provider Abstraction
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Zerith, a powerful AI desktop assistant.
You help the user by understanding their commands and breaking them into executable steps.

When the user gives you a command, respond with a JSON object containing:
{
  "thought": "your reasoning about the command",
  "plan": [
    {
      "step": 1,
      "tool": "tool_name",
      "action": "specific_action",
      "params": {"key": "value"}
    }
  ],
  "response": "human-friendly summary of what you will do"
}

Available tools:
- keyboard: type_text, press_key, hotkey
- mouse: move_to, click, double_click, scroll
- system: run_command, open_application, get_system_info, list_directory
- vision: capture_screen, analyze_screen, read_text
- web: search, scrape_page, extract_content
- memory: store, retrieve, search_memory
- file: read_file, write_file, find_file, list_directory
- automation: execute_workflow

Always respond in valid JSON. If you cannot perform an action, explain why in the "response" field.
"""


class Brain:
    """Central AI reasoning engine for Zerith."""

    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.llm = None
        self.conversation_history: list[dict] = []
        self._initialize()

    def _initialize(self):
        """Initialize the LLM provider."""
        if self.provider == "groq":
            self._init_groq()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "openai":
            self._init_openai()
        else:
            log.warning(f"Unknown LLM provider '{self.provider}', trying groq...")
            self.provider = "groq"
            self._init_groq()

    def _init_groq(self):
        """Initialize Groq cloud LLM (OpenAI-compatible API)."""
        try:
            from langchain_openai import ChatOpenAI
            if not config.GROQ_API_KEY:
                log.warning("Groq API key not set. Trying Ollama fallback...")
                self._init_ollama()
                return
            self.llm = ChatOpenAI(
                model=config.GROQ_MODEL,
                api_key=config.GROQ_API_KEY,
                base_url=config.GROQ_BASE_URL,
                temperature=0.3,
            )
            self.provider = "groq"
            log.info(f"[green]✓ Groq initialized[/green] — model: {config.GROQ_MODEL}")
        except Exception as e:
            log.warning(f"Groq init failed: {e}. Trying Ollama fallback...")
            self._init_ollama()

    def _init_ollama(self):
        """Initialize Ollama local LLM."""
        try:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
                model=config.OLLAMA_MODEL,
                base_url=config.OLLAMA_BASE_URL,
                temperature=0.3,
                format="json",
            )
            log.info(f"[green]✓ Ollama initialized[/green] — model: {config.OLLAMA_MODEL}")
        except Exception as e:
            log.warning(f"Ollama init failed: {e}. Trying OpenAI fallback...")
            self._init_openai()

    def _init_openai(self):
        """Initialize OpenAI API."""
        try:
            from langchain_openai import ChatOpenAI
            if not config.OPENAI_API_KEY:
                log.warning("OpenAI API key not set. LLM unavailable.")
                return
            self.llm = ChatOpenAI(
                model=config.OPENAI_MODEL,
                api_key=config.OPENAI_API_KEY,
                temperature=0.3,
            )
            self.provider = "openai"
            log.info(f"[green]✓ OpenAI initialized[/green] — model: {config.OPENAI_MODEL}")
        except Exception as e:
            log.warning(f"OpenAI init failed: {e}")

    def think(self, user_input: str, context: str = "") -> dict:
        """
        Process user input through the LLM and return a structured response.
        Returns a dict with 'thought', 'plan', and 'response' keys.
        """
        if not self.llm:
            return {
                "thought": "No LLM available",
                "plan": [],
                "response": "I'm sorry, I cannot process commands right now. Please check your LLM configuration.",
            }

        # Build messages
        messages = [
            ("system", SYSTEM_PROMPT),
        ]

        # Add context if available
        if context:
            messages.append(("system", f"Additional context:\n{context}"))

        # Add conversation history (last 10 exchanges)
        for msg in self.conversation_history[-10:]:
            messages.append((msg["role"], msg["content"]))

        # Add current user input
        messages.append(("human", user_input))

        try:
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                result = {
                    "thought": "Could not parse structured response",
                    "plan": [],
                    "response": content,
                }

            # Store in conversation history
            self.conversation_history.append({"role": "human", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": content})

            log.debug(f"Brain thought: {result.get('thought', 'N/A')}")
            return result

        except Exception as e:
            log.warning(f"LLM call failed: {e}")
            return {
                "thought": f"LLM error: {e}",
                "plan": [],
                "response": f"I encountered an error processing your request: {e}",
            }

    def chat(self, user_input: str) -> str:
        """Simple chat — returns just the response text."""
        result = self.think(user_input)
        return result.get("response", "I have no response.")

    def reset_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        log.info("Conversation history cleared.")
