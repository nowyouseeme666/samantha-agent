# Samantha V2 — Design Document

> Source of changes: merging Samantha's three-layer memory orchestration + safety guard + tool calling architecture onto a Giftia-level full frontend + streaming experience.
> All modifications confined to the Samantha project; Giftia project untouched.

**Date:** 2026-06-08
**Status:** Approved

---

## Goal

Upgrade Samantha from a Phase 1 CLI prototype to a fully functional Web SPA application. Preserve Samantha's architectural strengths (three-layer memory, YAML-configured persona, Valence/Arousal emotion model, safety guard, tool calling) while adding Giftia-level product polish: complete React SPA, SSE streaming, conversation management, and one-click deployment.

---

## Architecture Overview

```
Frontend (React 18 + Zustand + react-markdown + Tailwind CSS)
  │
  │ HTTP/SSE (port 3000 → proxy → port 8000)
  │
Backend (FastAPI + Uvicorn + LangGraph)
  │
  ├── SafetyGuard (input)
  │
  ├── MemoryOrchestrator
  │   ├── ImmutableMemory  (persona.yaml — always present)
  │   ├── LongTermMemory   (ChromaDB vector search)
  │   └── ShortTermMemory  (current conversation rounds)
  │
  ├── EmotionDetector (LLM → Valence/Arousal state)
  │
  ├── PromptBuilder (persona + rules + memory context + emotion → system prompt)
  │
  ├── Agent Graph (LangGraph — LLM + tool_calls loop, streaming tokens)
  │
  ├── SafetyGuard (output)
  │
  └── SSE Response (token-level streaming to frontend)
```

**Data flow per turn:**
SafetyGuard(input) → MemoryOrchestrator.gather() ∥ EmotionDetector.detect() → PromptBuilder.build() → LLM.stream(tools) → SafetyGuard(output) → SSE tokens → Memory.save()

---

## Module Breakdown

### Module 1: Project Setup & Dependencies

**Files:**
- Modify: `requirements.txt` (add `sse-starlette`, `python-multipart`, `python-dotenv`, `httpx`)
- Modify: `frontend/package.json` (add `zustand`, `react-markdown`, `remark-gfm`)
- Modify: `config/settings.yaml` (add SSE and frontend sections)

### Module 2: Frontend SPA

**New files:**
- `frontend/src/store.ts` — Zustand global state
- `frontend/src/api.ts` — SSE stream client
- `frontend/src/types.ts` — TypeScript type definitions
- `frontend/src/App.tsx` — Main layout (sidebar + chat area)
- `frontend/src/main.tsx` — React entry point
- `frontend/src/index.css` — Design tokens + global styles
- `frontend/src/components/ChatBubble.tsx` — User/Samantha message bubbles
- `frontend/src/components/ChatInput.tsx` — Input box with send button
- `frontend/src/components/ChatArea.tsx` — Message list container
- `frontend/src/components/ConversationList.tsx` — Sidebar conversation list
- `frontend/src/components/Sidebar.tsx` — Left drawer with conversations + config
- `frontend/src/components/EmotionPanel.tsx` — Right panel: valence/arousal ring
- `frontend/src/components/MemoryPanel.tsx` — Right panel: memory cards
- `frontend/src/components/StatsCard.tsx` — Memory stats summary

**Visual rules (follow DESIGN.md strictly):**
- Color: `--bg-primary` #faf9f7→#faf7f2 warm gradient, `--accent` #c4956a amber
- Typography: Source Han Sans CN, 16px body, 1.6 line-height
- Bubbles: user #e8e4dc fog, Sam white+double shadow, asymmetric radius (16px/4px)
- EmotionPanel: valence/arousal dual-axis ring (SVG), label+color indicator
- Motion: 200ms ease-out bubbles, 400ms ease-out emotion pointer, respects prefers-reduced-motion

### Module 3: Backend — Graph Streaming Workflow

**New file:** `src/graph/streaming.py`

Async generator that yields SSE event dicts:
- `{type: 'status', text: '...'}`
- `{type: 'emotion', state: EmotionState}`
- `{type: 'memory', entries: [...]}`
- `{type: 'token', text: '...'}`
- `{type: 'reply', text: '...'}`
- `{type: 'done', conversation_id: '...'}`
- `{type: 'blocked', text: '...'}`
- `{type: 'error', text: '...'}`

**Modify:** `src/graph/graph.py` — Real LLM + tool_calls loop

Workflow: safety(input) → memory+emotion(parallel) → prompt → agent(tools) → safety(output) → respond → memory_save

### Module 4: Backend — ChromaDB Long-Term Memory

**Modify:** `src/memory/long_term.py` — Replace in-memory list with real ChromaDB:
- `chromadb.PersistentClient` for local persistence
- Embedding via DeepSeek API
- Similarity search with cosine distance

### Module 5: Backend — LLM Client Streaming

**Modify:** `src/llm/client.py` — Add `stream()` method using `langchain ChatOpenAI.stream()`

### Module 6: Backend — Safety Guard Integration

**Modify:** `src/safety/guard.py` — Wire into workflow at two points (input check before processing, output check before sending)
**Modify:** `src/safety/monitor.py` — Real negative streak detection based on EmotionState.valence

### Module 7: Backend — Emotion Detection

**Modify:** `src/emotion/detector.py` — From placeholder to real LLM call:
- Single LLM call produces Valence (-1~1), Arousal (0~1), Label
- Run in parallel with MemoryOrchestrator.gather()

### Module 8: Backend — FastAPI Server

**New file:** `server.py`
- FastAPI + Uvicorn entry point
- Lifespan: init ChromaDB, SafetyGuard, EmotionDetector, ToolExecutor, load YAML configs
- CORS middleware for localhost:3000
- Routes: POST /api/chat/{user_id} (SSE), conversation CRUD, memory stats

**Modify:** `src/api.py` — Expand route definitions

### Module 9: Backend — Prompt Builder

**Modify:** `src/llm/prompt_builder.py` — Complete implementation:
- Assemble system prompt from persona + rules + memory context + emotion state
- Format tools into function-calling schema
- Build user message with long-term memories and recent history

### Module 10: Backend — Conversation Storage

Add SQLite-based conversation persistence (conversation_store.py) for multi-session support.

### Module 11: Configuration

**Modify:** `src/config.py` — Add SSE, frontend, conversation fields to SamanthaSettings
**Modify:** `config/settings.yaml` — Add new sections

### Module 12: Tests

**Modify** all existing test files from placeholder to real tests:
- `test_config.py`: YAML loading, Settings validation
- `test_schemas.py`: EmotionState/MemoryEntry serialization
- `test_memory.py`: Three-layer memory CRUD
- `test_orchestrator.py`: Decay scoring + dedup logic
- `test_emotion.py`: Detector with mocked LLM
- `test_guard.py`: Keyword filtering (normal/warning/blocked)
- `test_monitor.py`: Negative streak escalation
- `test_prompt_builder.py`: Prompt assembly correctness
- `test_llm.py`: Streaming client (mocked)
- `test_tools.py`: Tool registry + executor
- `test_graph.py`: LangGraph flow integrity (mocked LLM)
- `test_api.py`: FastAPI routes via TestClient
- `test_integration.py`: End-to-end conversation simulation

### Module 13: Deployment

**New files:** `start.bat`, `start.sh` — One-click start scripts

---

## Files Changed Summary

**New (14 files):**
server.py, src/graph/streaming.py, frontend/src/store.ts, frontend/src/api.ts, frontend/src/types.ts,
frontend/src/components/ChatBubble.tsx, frontend/src/components/ChatInput.tsx, frontend/src/components/ChatArea.tsx,
frontend/src/components/ConversationList.tsx, frontend/src/components/Sidebar.tsx,
frontend/src/components/EmotionPanel.tsx, frontend/src/components/MemoryPanel.tsx,
frontend/src/components/StatsCard.tsx, start.bat

**Modified (14 files):**
src/graph/graph.py, src/graph/state.py, src/memory/long_term.py, src/llm/client.py,
src/llm/prompt_builder.py, src/emotion/detector.py, src/safety/guard.py, src/safety/monitor.py,
src/api.py, src/config.py, config/settings.yaml, frontend/src/App.tsx, frontend/src/main.tsx,
frontend/src/index.css, frontend/tailwind.config.js, frontend/vite.config.ts, requirements.txt,
frontend/package.json

**Untouched (preserved):**
config/persona.yaml, config/rules.yaml, config/tools.yaml, src/tools/*, src/memory/base.py,
src/memory/short_term.py, src/memory/immutable.py, src/memory/orchestrator.py, src/schemas/*,
src/emotion/rules.py, main.py, DESIGN.md, PRODUCT.md

---

## Non-Goals (deferred)

- Multi-model support (DeepSeek only for now)
- User authentication system
- Image/multimodal support
- Mem0 cloud memory integration
- Customizable system prompt via web UI
