"""
Zerith AI — Vector Memory
Semantic search memory using ChromaDB for embedding-based retrieval.
"""

from typing import Optional
from utils.logger import log
import config


class VectorMemory:
    """ChromaDB-backed vector memory for semantic search."""

    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        self.client = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings

            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="zerith_memory",
                metadata={"description": "Zerith AI long-term memory"},
            )
            count = self.collection.count()
            log.info(f"[green]✓ Vector memory initialized[/green] — {count} memories stored")
        except Exception as e:
            log.warning(f"ChromaDB init failed: {e}")

    def add(self, text: str, metadata: Optional[dict] = None, doc_id: str = None) -> str:
        """Add a memory to the vector store."""
        if not self.collection:
            return "Vector memory not available"

        import hashlib
        if not doc_id:
            doc_id = hashlib.md5(text.encode()).hexdigest()[:12]

        try:
            self.collection.upsert(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
            log.info(f"Vector memory added: {doc_id}")
            return f"Memory stored (id: {doc_id})"
        except Exception as e:
            log.warning(f"Vector add failed: {e}")
            return f"Failed to store memory: {e}"

    def search(self, query: str, n_results: int = 5) -> str:
        """Search memories by semantic similarity."""
        if not self.collection:
            return "Vector memory not available"

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )

            if not results["documents"] or not results["documents"][0]:
                return "No matching memories found"

            output_lines = []
            for i, (doc, dist) in enumerate(
                zip(results["documents"][0], results["distances"][0]), 1
            ):
                similarity = round(1 - dist, 3)
                output_lines.append(f"{i}. [{similarity}] {doc[:200]}")

            return "\n".join(output_lines)

        except Exception as e:
            log.warning(f"Vector search failed: {e}")
            return f"Search failed: {e}"

    def count(self) -> int:
        """Return number of stored memories."""
        if not self.collection:
            return 0
        return self.collection.count()

    def clear(self) -> str:
        """Delete all memories."""
        if not self.collection or not self.client:
            return "Vector memory not available"
        try:
            self.client.delete_collection("zerith_memory")
            self._initialize()
            return "All vector memories cleared"
        except Exception as e:
            return f"Clear failed: {e}"


# Singleton
_vmem = None


def _get_vmem() -> VectorMemory:
    global _vmem
    if _vmem is None:
        _vmem = VectorMemory()
    return _vmem


def store_memory(text: str, metadata: str = "") -> str:
    meta = {"note": metadata} if metadata else {}
    return _get_vmem().add(text, metadata=meta)


def search_memory(query: str, n_results: int = 5) -> str:
    return _get_vmem().search(query, n_results=n_results)


def memory_count() -> str:
    return f"Vector memory contains {_get_vmem().count()} entries"


# Handler map for router registration
HANDLERS = {
    "store_vector": store_memory,
    "search_vector": search_memory,
    "count": memory_count,
}
