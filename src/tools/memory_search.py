"""search_memories — search Samantha's long-term memory.

Used when the user references past events, preferences, or profile info.
Matches against entry summaries via keyword search (Phase 2; Phase 3 will
use ChromaDB embeddings).
"""

from __future__ import annotations

from typing import Any


def search_memories(
    query: str,
    memory: Any | None = None,
    k: int = 5,
) -> str:
    """Search the long-term memory for entries matching *query*.

    Args:
        query: The search string.
        memory: A LongTermMemory instance (injected by executor context).
        k: Maximum number of results.

    Returns:
        A formatted string of matching memories, or a not-found message.
    """
    if memory is None:
        return "[memory_search] 记忆系统未初始化，无法搜索。"

    if not query:
        return "[memory_search] 请提供搜索关键词。"

    entries = memory.get(query=query, k=k)

    if not entries:
        return f"[memory_search] 未找到与 '{query}' 相关的记忆。"

    lines = [f"[memory_search] 找到 {len(entries)} 条相关记忆："]
    for i, entry in enumerate(entries, start=1):
        lines.append(f"  {i}. {entry.summary}")
    return "\n".join(lines)
