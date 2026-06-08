"""Streaming workflow: async generator yielding SSE events."""
import asyncio, json, time, logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

async def run_streaming_workflow(runtime, user_id: str, user_message: str) -> AsyncGenerator[dict, None]:
    """Yield SSE event dicts: {type: 'status'|'emotion'|'memory'|'token'|'reply'|'done'|'blocked'|'error', ...}"""
    try:
        runtime._turn += 1
        turn = runtime._turn
        yield {"type": "status", "text": "正在感受你的情绪..."}

        # 1. Safety check: input
        safety_result = runtime.guard.check(user_message)
        if safety_result == "blocked":
            yield {"type": "blocked", "text": runtime.guard.get_blocked_response()}
            return

        # 2. Store user message
        from src.schemas.memory import MemoryEntry, MemoryCategory
        runtime.short_term.add(MemoryEntry(id=f"turn-{turn}-user", content=user_message, summary=user_message[:100], category=MemoryCategory.EVENT))

        # 3. Emotion detection
        runtime.emotion = runtime.detector.detect(user_message)
        yield {"type": "emotion", "state": runtime.emotion.to_dict()}

        # 4. Memory retrieval
        memories_used = []
        if hasattr(runtime, 'orchestrator') and runtime.orchestrator:
            ctx = runtime.orchestrator.gather(user_message, runtime.emotion)
            memories_used = [e.summary for e in ctx.entries[:5]]
        else:
            lt = runtime.long_term.get(query=user_message, k=5)
            memories_used = [e.summary for e in lt]
        yield {"type": "memory", "entries": memories_used}

        # 5. Build prompt
        enabled_tools = runtime.tools_cfg.enabled_tools()
        system_msg = runtime.prompt_builder.build_system(emotion_state=runtime.emotion.to_dict(), tools=enabled_tools)
        recent = []
        for e in runtime.short_term.get(query="", k=6):
            role = "User" if "user" in (e.id or "") else "Samantha"
            recent.append(f"{role}: {e.content}")
        recent = list(reversed(recent))
        user_msg = runtime.prompt_builder.build_user(long_term_memories=memories_used, recent_history=recent, current_message=user_message)

        # 6. Stream tokens
        yield {"type": "status", "text": "正在组织语言..."}
        full_reply = ""
        try:
            for token in runtime.llm.stream(message=user_msg, system_prompt=system_msg):
                if token:
                    full_reply += token
                    yield {"type": "token", "text": token}
        except Exception as e:
            logger.error(f"LLM stream failed: {e}", exc_info=True)
            full_reply = runtime.settings.dialogue_fallback_message
            yield {"type": "error", "text": f"LLM调用失败: {str(e)}"}
            for ch in full_reply:
                yield {"type": "token", "text": ch}

        # 7. Safety check: output
        output_safety = runtime.guard.check(full_reply)
        if output_safety == "blocked":
            full_reply = runtime.guard.get_blocked_response()

        if full_reply.strip():
            yield {"type": "reply", "text": full_reply.strip()}

        # 8. Store response
        runtime.short_term.add(MemoryEntry(id=f"turn-{turn}-samantha", content=full_reply, summary=full_reply[:100], category=MemoryCategory.EVENT))
        runtime.long_term.add(MemoryEntry(id=f"lt-{turn}", content=f"User: {user_message}\nSamantha: {full_reply}", summary=f"U[{user_message[:50]}] S[{full_reply[:50]}]", category=MemoryCategory.EVENT))
        runtime.monitor.update(runtime.emotion)

        yield {"type": "done"}
    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        yield {"type": "error", "text": str(e)}
