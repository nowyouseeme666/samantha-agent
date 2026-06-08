"""FastAPI backend for Samantha Agent."""

from __future__ import annotations

import os
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
import json, uuid, datetime, asyncio
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.schemas.memory import MemoryCategory, MemoryEntry

class ChatRequest(BaseModel):
    message: str

class EmotionResponse(BaseModel):
    valence: float
    arousal: float
    label: str

class ChatResponse(BaseModel):
    reply: str
    emotion: EmotionResponse
    memories_used: list[str]
    safety_flag: str

class MemoryResponse(BaseModel):
    short_term: list[str]
    long_term: list[str]

class HealthResponse(BaseModel):
    status: str
    model: str

@dataclass
class AgentRuntime:
    settings: Any
    persona: Any
    rules: Any
    tools_cfg: Any
    llm: Any
    prompt_builder: Any
    short_term: Any
    long_term: Any
    immutable: Any
    guard: Any
    monitor: Any
    emotion: Any
    detector: Any
    tool_executor: Any = field(default=None)
    conv_store: Any = field(default=None)
    _turn: int = field(default=0, init=False)
    _last_user_msg: str = field(default="", init=False)
    _last_reply: str = field(default="", init=False)

    def process_message(self, user_message: str) -> dict[str, Any]:
        self._turn += 1
        turn = self._turn
        self.emotion = self.detector.detect(user_message)
        safety_result = self.guard.check(user_message)
        if safety_result == "blocked":
            return {
                "reply": self.guard.get_blocked_response(),
                "emotion": self.emotion.to_dict(),
                "memories_used": [],
                "safety_flag": "blocked",
            }
        self.short_term.add(MemoryEntry(
            id=f"turn-{turn}-user", content=user_message,
            summary=user_message[:100], category=MemoryCategory.EVENT,
        ))
        enabled_tools = self.tools_cfg.enabled_tools()
        system_msg = self.prompt_builder.build_system(emotion_state=self.emotion.to_dict(), tools=enabled_tools)
        short_history = []
        for e in self.short_term.get(query="", k=6):
            role = "User" if "user" in (e.id or "") else "Samantha"
            short_history.append(f"{role}: {e.content}")
        short_history = list(reversed(short_history))
        user_msg = self.prompt_builder.build_user(
            long_term_memories=[e.summary for e in self.long_term.get(query=user_message, k=5)],
            recent_history=short_history, current_message=user_message,
        )
        try:
            response = self.llm.chat_with_tools(
                message=user_msg, system_prompt=system_msg,
                tools=enabled_tools, tool_executor=self.tool_executor,
            )
        except Exception:
            traceback.print_exc()
            response = self.settings.dialogue_fallback_message
        output_safety = self.guard.check(response)
        safety_flag = "normal"
        if output_safety == "blocked":
            response = self.guard.get_blocked_response()
            safety_flag = "blocked"
        elif output_safety == "warning" or safety_result == "warning":
            safety_flag = "warning"
        self.short_term.add(MemoryEntry(
            id=f"turn-{turn}-samantha", content=response,
            summary=response[:100], category=MemoryCategory.EVENT,
        ))
        self.long_term.add(MemoryEntry(
            id=f"lt-{turn}", content=f"User: {user_message}\nSamantha: {response}",
            summary=f"User[{user_message[:50]}], Sam[{response[:50]}]", category=MemoryCategory.EVENT,
        ))
        risk = self.monitor.update(self.emotion)
        if risk == "warning" and safety_flag == "normal":
            safety_flag = "warning"
        memories_used = [e.summary for e in self.long_term.get(query=user_message, k=5)]
        return {
            "reply": response, "emotion": self.emotion.to_dict(),
            "memories_used": memories_used, "safety_flag": safety_flag,
        }

    def get_memory_snapshot(self) -> dict[str, list[str]]:
        return {
            "short_term": [e.content for e in self.short_term.get(query="", k=20)],
            "long_term": [e.summary for e in self.long_term.get(query="", k=20)],
        }

_runtime: AgentRuntime | None = None
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

def _build_runtime(api_key: str | None = None) -> AgentRuntime:
    from src.config import PersonaConfig, RulesConfig, SamanthaSettings, ToolsConfig
    from src.llm.client import LLMClient
    from src.llm.prompt_builder import PromptBuilder
    from src.memory.immutable import ImmutableMemory
    from src.memory.long_term import LongTermMemory
    from src.memory.short_term import ShortTermMemory
    from src.safety.guard import SafetyGuard
    from src.safety.monitor import EmotionMonitor
    from src.schemas.emotion import EmotionState
    from src.emotion.detector import EmotionDetector
    from src.tools.executor import ToolExecutor
    from src.tools.registry import ALL_TOOLS
    from src.conversation_store import ConversationStore

    settings = SamanthaSettings(_yaml_config=_CONFIG_DIR / "settings.yaml", _persona_dir=_CONFIG_DIR)
    key = api_key or settings.deepseek_api_key
    if not key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY not set. Add it to .env or set the env var.")

    persona = PersonaConfig.from_yaml(_CONFIG_DIR / "persona.yaml")
    rules = RulesConfig.from_yaml(_CONFIG_DIR / "rules.yaml")
    tools_cfg = ToolsConfig.from_yaml(_CONFIG_DIR / "tools.yaml")
    llm = LLMClient(api_key=key, model=settings.llm_model, temperature=settings.llm_temperature)
    prompt_builder = PromptBuilder(persona_path=_CONFIG_DIR / "persona.yaml", rules_path=_CONFIG_DIR / "rules.yaml")
    short_term = ShortTermMemory(max_rounds=settings.memory_short_term_max_rounds)
    long_term = LongTermMemory(chroma_dir=settings.memory_long_term_chroma_dir)
    immutable = ImmutableMemory.from_yaml(_CONFIG_DIR / "persona.yaml")
    guard = SafetyGuard(blocked_keywords=settings.safety_blocked_keywords, warning_keywords=settings.safety_warning_keywords)
    monitor = EmotionMonitor(risk_threshold=settings.safety_emotion_risk_threshold)
    emotion = EmotionState()
    detector = EmotionDetector(llm_client=llm)
    tool_executor = ToolExecutor(tools=ALL_TOOLS, context={"memory": long_term})
    conv_store = ConversationStore()

    rt = AgentRuntime(
        settings=settings, persona=persona, rules=rules, tools_cfg=tools_cfg,
        llm=llm, prompt_builder=prompt_builder, short_term=short_term,
        long_term=long_term, immutable=immutable, guard=guard,
        monitor=monitor, emotion=emotion, detector=detector,
        tool_executor=tool_executor, conv_store=conv_store,
    )
    return rt

def get_runtime() -> AgentRuntime:
    global _runtime
    if _runtime is None:
        _runtime = _build_runtime()
    return _runtime

app = FastAPI(title="Samantha Agent", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Serve static frontend
_fe_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_fe_ok = _fe_dist.exists()
if _fe_dist.exists():
    _assets = _fe_dist / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="fe_assets")

@app.exception_handler(404)
async def _fe_fallback(_r, _e):
    if _fe_ok and not str(_r.url.path).startswith("/api/"):
        _x = _fe_dist / "index.html"
        if _x.exists():
            return FileResponse(str(_x))
    return JSONResponse({"detail": "Not Found"}, status_code=404)

# -- V1 routes (backward compat) --
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict[str, Any]:
    if not request.message or not request.message.strip():
        return {"reply": "", "emotion": {"valence": 0.0, "arousal": 0.0, "label": ""}, "memories_used": [], "safety_flag": "normal"}
    return get_runtime().process_message(request.message.strip())

@app.get("/api/memory", response_model=MemoryResponse)
async def memory() -> dict[str, Any]:
    return get_runtime().get_memory_snapshot()

@app.get("/api/emotion", response_model=EmotionResponse)
async def emotion() -> dict[str, Any]:
    return get_runtime().emotion.to_dict()

@app.get("/api/health", response_model=HealthResponse)
async def health() -> dict[str, Any]:
    try:
        model = get_runtime().settings.llm_model
    except Exception:
        model = "deepseek-chat"
    return {"status": "ok", "model": model}

# -- V2 SSE chat + conversation routes --
class SSEChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    conversation_history: list[dict] = []

class RenameRequest(BaseModel):
    title: str

@app.post("/api/chat/{user_id}")
async def chat_sse(user_id: str, req: SSEChatRequest):
    from src.graph.streaming import run_streaming_workflow
    runtime = get_runtime()
    cid = req.conversation_id
    async def _stream():
        nonlocal cid
        async for event in run_streaming_workflow(runtime, user_id, req.message):
            if event.get("type") == "reply":
                runtime._last_user_msg = req.message
                runtime._last_reply = event.get("text", "")
            if event.get("type") == "done" and runtime.conv_store:
                convs, current_id = runtime.conv_store.load(user_id)
                if not convs:
                    convs = {}
                if not cid or cid not in convs:
                    cid = str(uuid.uuid4())
                    convs[cid] = {"title": req.message[:20] or "", "messages": [], "created": datetime.datetime.now().strftime("%m/%d %H:%M")}
                conv = convs[cid]
                conv["messages"].append({"role": "user", "content": req.message})
                conv["messages"].append({"role": "assistant", "content": runtime._last_reply})
                if len(conv["messages"]) <= 2:
                    conv["title"] = req.message[:20] or ""
                runtime.conv_store.save(user_id, convs, cid)
                event["conversation_id"] = cid
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})

@app.get("/api/conversations/{user_id}")
async def get_conversations(user_id: str):
    runtime = get_runtime()
    convs, current_id = runtime.conv_store.load(user_id) if runtime.conv_store else (None, None)
    if not convs:
        cid = str(uuid.uuid4())
        convs = {cid: {"title": "", "messages": [], "created": datetime.datetime.now().strftime("%m/%d %H:%M")}}
        current_id = cid
        if runtime.conv_store:
            runtime.conv_store.save(user_id, convs, current_id)
    items = [{"id": cid, "title": c.get("title",""), "created": c.get("created",""), "message_count": len(c.get("messages",[])), "is_active": cid == current_id} for cid, c in convs.items()]
    return {"conversations": sorted(items, key=lambda x: x["created"], reverse=True), "current_id": current_id}

@app.get("/api/conversations/{user_id}/{conv_id}")
async def get_conversation(user_id: str, conv_id: str):
    runtime = get_runtime()
    convs, _ = runtime.conv_store.load(user_id) if runtime.conv_store else (None, None)
    if not convs or conv_id not in convs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convs[conv_id]

@app.post("/api/conversations/{user_id}")
async def create_conversation(user_id: str):
    runtime = get_runtime()
    convs_raw = runtime.conv_store.load(user_id) if runtime.conv_store else (None, None)
    convs = convs_raw[0] if convs_raw[0] is not None else {}
    cid = str(uuid.uuid4())
    convs[cid] = {"title": "", "messages": [], "created": datetime.datetime.now().strftime("%m/%d %H:%M")}
    if runtime.conv_store:
        runtime.conv_store.save(user_id, convs, cid)
    return {"id": cid, "title": "", "created": convs[cid]["created"]}

@app.patch("/api/conversations/{user_id}/{conv_id}")
async def rename_conversation(user_id: str, conv_id: str, req: RenameRequest):
    runtime = get_runtime()
    convs, current_id = runtime.conv_store.load(user_id) if runtime.conv_store else (None, None)
    if not convs or conv_id not in convs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convs[conv_id]["title"] = req.title.strip()
    if runtime.conv_store:
        runtime.conv_store.save(user_id, convs, current_id)
    return {"ok": True, "title": req.title.strip()}

@app.delete("/api/conversations/{user_id}/{conv_id}")
async def delete_conversation(user_id: str, conv_id: str):
    runtime = get_runtime()
    convs, current_id = runtime.conv_store.load(user_id) if runtime.conv_store else (None, None)
    if not convs or conv_id not in convs:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del convs[conv_id]
    if not convs:
        cid = str(uuid.uuid4())
        convs = {cid: {"title": "", "messages": [], "created": datetime.datetime.now().strftime("%m/%d %H:%M")}}
        current_id = cid
    elif current_id == conv_id:
        current_id = list(convs.keys())[-1]
    if runtime.conv_store:
        runtime.conv_store.save(user_id, convs, current_id)
    return {"ok": True, "current_id": current_id}

@app.get("/api/memory/{user_id}/stats")
async def get_memory_stats(user_id: str):
    runtime = get_runtime()
    lt = runtime.long_term
    return {"total": len(lt._entries), "avg_importance": sum(e.importance for e in lt._entries) / max(len(lt._entries), 1)}
