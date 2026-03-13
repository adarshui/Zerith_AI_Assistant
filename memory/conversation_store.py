"""
Zerith AI — Conversation Store
SQLite-based persistent storage for all conversations with semantic search.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from utils.logger import log
import config


class ConversationStore:
    """SQLite-backed conversation storage with semantic search via ChromaDB."""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path or config.CONVERSATION_DB_FILE)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Main conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                context TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster searching
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_message ON conversations(user_message)
        """)
        
        conn.commit()
        conn.close()
        
        log.debug(f"Conversation store initialized: {self.db_path}")

    def _get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(str(self.db_path))

    def add_conversation(
        self,
        user_message: str,
        ai_response: str,
        context: str = None,
        tags: List[str] = None
    ) -> int:
        """
        Store a conversation (user message + AI response).
        Returns the conversation ID.
        """
        timestamp = datetime.utcnow().isoformat()
        tags_json = json.dumps(tags) if tags else None
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO conversations 
               (timestamp, user_message, ai_response, context, tags) 
               VALUES (?, ?, ?, ?, ?)""",
            (timestamp, user_message, ai_response, context, tags_json)
        )
        
        conv_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Also add to vector memory for semantic search
        self._add_to_vector(user_message, ai_response, conv_id, tags)
        
        log.debug(f"Conversation stored: id={conv_id}")
        return conv_id

    def _add_to_vector(self, user_message: str, ai_response: str, conv_id: int, tags: List[str] = None):
        """Add conversation to vector store for semantic search."""
        try:
            from memory.vector_memory import _get_vmem
            
            # Combine user message and AI response for indexing
            combined_text = f"User: {user_message}\nAI: {ai_response}"
            metadata = {
                "conversation_id": str(conv_id),
                "type": "conversation",
                "tags": json.dumps(tags) if tags else "[]"
            }
            
            vmem = _get_vmem()
            if vmem and vmem.collection:
                vmem.add(combined_text, metadata=metadata, doc_id=f"conv_{conv_id}")
        except Exception as e:
            log.warning(f"Failed to add conversation to vector store: {e}")

    def get_conversation(self, conv_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific conversation by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, timestamp, user_message, ai_response, context, tags 
               FROM conversations WHERE id = ?""",
            (conv_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "timestamp": row[1],
                "user_message": row[2],
                "ai_response": row[3],
                "context": row[4],
                "tags": json.loads(row[5]) if row[5] else []
            }
        return None

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent conversations."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, timestamp, user_message, ai_response, context, tags 
               FROM conversations ORDER BY timestamp DESC LIMIT ?""",
            (limit,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "user_message": row[2],
                "ai_response": row[3],
                "context": row[4],
                "tags": json.loads(row[5]) if row[5] else []
            }
            for row in rows
        ]

    def search_conversations(self, query: str, limit: int = 5) -> str:
        """Search conversations using vector similarity."""
        try:
            from memory.vector_memory import _get_vmem
            
            vmem = _get_vmem()
            if not vmem or not vmem.collection:
                return self._text_search(query, limit)
            
            results = vmem.search(query, n_results=limit)
            
            # Parse results to get conversation IDs and format output
            if "No matching memories" in results or "not available" in results:
                return self._text_search(query, limit)
            
            return results
            
        except Exception as e:
            log.warning(f"Vector search failed: {e}, falling back to text search")
            return self._text_search(query, limit)

    def _text_search(self, query: str, limit: int = 5) -> str:
        """Simple text search fallback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query_pattern = f"%{query}%"
        cursor.execute(
            """SELECT id, timestamp, user_message, ai_response 
               FROM conversations 
               WHERE user_message LIKE ? OR ai_response LIKE ?
               ORDER BY timestamp DESC LIMIT ?""",
            (query_pattern, query_pattern, limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No matching conversations found"
        
        output_lines = []
        for row in rows:
            output_lines.append(
                f"[{row[1][:19]}] User: {row[2][:100]}...\n    AI: {row[3][:100]}..."
            )
        
        return "\n\n".join(output_lines)

    def get_context_for_query(self, query: str, limit: int = None) -> str:
        """
        Get relevant conversation context for a new query.
        Used to load memories before AI response generation.
        """
        limit = limit or config.MAX_CONTEXT_MEMORIES
        
        # First try semantic search
        try:
            from memory.vector_memory import _get_vmem
            
            vmem = _get_vmem()
            if vmem and vmem.collection:
                results = vmem.search(query, n_results=limit)
                
                if "No matching" not in results and "not available" not in results:
                    # Extract relevant conversation text
                    context_parts = []
                    for line in results.split("\n"):
                        if line.strip():
                            # Clean up the result line
                            cleaned = line.strip()
                            if cleaned and not cleaned.startswith("[") or ":" in cleaned:
                                context_parts.append(cleaned)
                    
                    if context_parts:
                        return "Relevant past conversations:\n" + "\n".join(context_parts[:limit])
        except Exception as e:
            log.warning(f"Semantic context search failed: {e}")
        
        # Fallback to recent conversations
        recent = self.get_recent_conversations(limit)
        if not recent:
            return ""
        
        context_parts = []
        for conv in recent:
            context_parts.append(
                f"Past conversation: User asked '{conv['user_message'][:80]}...' "
                f"-> AI responded: '{conv['ai_response'][:100]}...'"
            )
        
        return "Relevant past conversations:\n" + "\n".join(context_parts)

    def delete_conversation(self, conv_id: int) -> str:
        """Delete a conversation by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            # Also remove from vector store
            try:
                from memory.vector_memory import _get_vmem
                vmem = _get_vmem()
                if vmem and vmem.collection:
                    vmem.collection.delete(ids=[f"conv_{conv_id}"])
            except Exception:
                pass
            
            return f"Deleted conversation {conv_id}"
        return f"Conversation {conv_id} not found"

    def clear_all(self) -> str:
        """Clear all conversations."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM conversations")
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        log.info(f"Cleared {count} conversations from store")
        return f"Cleared {count} conversations"

    def get_statistics(self) -> str:
        """Get statistics about stored conversations."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM conversations")
        row = cursor.fetchone()
        earliest = row[0][:19] if row[0] else "N/A"
        latest = row[1][:19] if row[1] else "N/A"
        
        conn.close()
        
        return (
            f"Conversation Store Statistics:\n"
            f"  Total conversations: {total}\n"
            f"  Earliest: {earliest}\n"
            f"  Latest: {latest}"
        )


# Singleton instance
_store = None


def _get_store() -> ConversationStore:
    global _store
    if _store is None:
        _store = ConversationStore()
    return _store


def add_conversation(user_message: str, ai_response: str, context: str = None, tags: List[str] = None) -> int:
    """Store a new conversation."""
    return _get_store().add_conversation(user_message, ai_response, context, tags)


def get_conversation(conv_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific conversation."""
    return _get_store().get_conversation(conv_id)


def get_recent_conversations(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversations."""
    return _get_store().get_recent_conversations(limit)


def search_conversations(query: str, limit: int = 5) -> str:
    """Search conversations."""
    return _get_store().search_conversations(query, limit)


def get_context_for_query(query: str, limit: int = None) -> str:
    """Get relevant context for a new query."""
    return _get_store().get_context_for_query(query, limit)


def delete_conversation(conv_id: int) -> str:
    """Delete a conversation."""
    return _get_store().delete_conversation(conv_id)


def clear_conversations() -> str:
    """Clear all conversations."""
    return _get_store().clear_all()


def get_conversation_stats() -> str:
    """Get conversation statistics."""
    return _get_store().get_statistics()


# Handler map for router registration
HANDLERS = {
    "add_conversation": lambda user_msg, ai_resp, ctx="", tags=None: str(add_conversation(user_msg, ai_resp, ctx, tags)),
    "search_conversations": search_conversations,
    "get_recent_conversations": lambda limit=10: "\n".join(str(c) for c in get_recent_conversations(limit)),
    "conversation_stats": get_conversation_stats,
    "clear_conversations": clear_conversations,
}
