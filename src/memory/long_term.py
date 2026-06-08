"""LongTermMemory -- RAG-backed persistent memory (ChromaDB)."""
from __future__ import annotations
import os
from datetime import datetime
from src.memory.base import BaseMemory
from src.schemas.memory import MemoryCategory, MemoryEntry
import chromadb
from chromadb.utils import embedding_functions

class LongTermMemory(BaseMemory):
    def __init__(self, chroma_dir="./data/chroma", collection_name="samantha_memory"):
        self._chroma_dir = chroma_dir
        os.makedirs(chroma_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=chroma_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        self._entries: list[MemoryEntry] = []
        self._load_from_chroma()

    def _load_from_chroma(self) -> None:
        """Reconstruct self._entries from persisted ChromaDB data.

        Called once during __init__ so that restarted processes can still
        retrieve long-term memories.  If the collection is empty (first run)
        this is a no-op.
        """
        try:
            existing = self._collection.get()
            ids = existing.get("ids", [])
            if not ids:
                return
            documents = existing.get("documents") or [""] * len(ids)
            metadatas = existing.get("metadatas") or [{}] * len(ids)
            for i, doc_id in enumerate(ids):
                meta = metadatas[i] if i < len(metadatas) else {}
                created_at_str = meta.get("created_at", "")
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except (ValueError, TypeError):
                    created_at = datetime.now()
                self._entries.append(MemoryEntry(
                    id=doc_id,
                    content=documents[i] if i < len(documents) else "",
                    summary=meta.get("summary", ""),
                    category=MemoryCategory(meta.get("category", "event")),
                    importance=float(meta.get("importance", 0.5)),
                    created_at=created_at,
                    decay_rate=float(meta.get("decay_rate", 0.01)),
                ))
        except Exception:
            # If ChromaDB is unreachable, leave entries empty —
            # the keyword fallback in get() will also be empty, which is the
            # best we can do.
            pass

    def add(self, entry: MemoryEntry) -> None:
        if not entry.content.strip():
            return
        try:
            self._collection.add(
                ids=[entry.id],
                documents=[entry.content],
                metadatas=[{
                    "summary": entry.summary,
                    "category": entry.category.value,
                    "importance": entry.importance,
                    "created_at": entry.created_at.isoformat()
                }]
            )
            self._entries.append(entry)
        except Exception:
            self._entries.append(entry)

    def get(self, query: str = "", k: int = 5) -> list[MemoryEntry]:
        if not query or not self._entries:
            return self._entries[-k:] if self._entries else []
        try:
            results = self._collection.query(query_texts=[query], n_results=k)
            ids = results.get("ids", [[]])[0]
            return [e for e in self._entries if e.id in ids][:k]
        except Exception:
            query_lower = query.lower()
            scored = [(e, e.summary.lower().count(query_lower) or e.content.lower().count(query_lower)) for e in self._entries]
            scored.sort(key=lambda x: x[1], reverse=True)
            return [e for e, s in scored if s > 0][:k]

    def clear(self) -> None:
        self._entries.clear()
        try:
            all_ids = self._collection.get()["ids"]
            if all_ids:
                self._collection.delete(ids=all_ids)
        except Exception:
            pass
