# Samantha V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade Samantha from CLI prototype to full Web SPA with SSE streaming, three-layer memory orchestration, safety guard, and tool calling.

**Architecture:** Frontend (React 18 + Zustand + react-markdown + Tailwind CSS) communicates via SSE to FastAPI backend.

**Tech Stack:** Python 3.12+, FastAPI, LangChain/LangGraph, ChromaDB, React 18, Zustand, Tailwind CSS, react-markdown, remark-gfm

---

## Task 1: Dependencies

Update `requirements.txt` (add sse-starlette, python-multipart, python-dotenv, httpx).
Update `frontend/package.json` (add zustand, react-markdown, remark-gfm).
Run pip install + npm install.

## Task 2: settings.yaml

Append sse, conversation, frontend sections to `config/settings.yaml`.

## Task 3: LLM client streaming

Add `stream()` method to `src/llm/client.py` using langchain ChatOpenAI.stream().

## Task 4: ChromaDB long-term memory

Replace in-memory list in `src/memory/long_term.py` with chromadb.PersistentClient.

## Task 5: Conversation store

Create `src/conversation_store.py` — SQLite-backed multi-session persistence.

## Task 6: SSE streaming workflow

Create `src/graph/streaming.py` — async generator yielding SSE events.

## Task 7: Vite proxy

Update `frontend/vite.config.ts` with /api proxy to 127.0.0.1:8000.

## Task 8-17: Frontend SPA

Create/replace all frontend files:
- types.ts (TypeScript types)
- api.ts (SSE stream + REST client)
- store.ts (Zustand global state)
- index.css (design tokens + Tailwind)
- tailwind.config.js (Samantha color palette)
- App.tsx (main SPA layout — header, sidebar drawer, chat area, right panels)
- components/Sidebar.tsx (drawer overlay)
- components/ConversationList.tsx (conversation items)
- components/StatsCard.tsx (memory stats summary)
- components/ChatArea.tsx (message list + input, auto-scroll, empty state)
- components/ChatBubble.tsx (styled bubbles, react-markdown, streaming cursor)
- components/ChatInput.tsx (amber focus ring, Enter to send)
- components/EmotionPanel.tsx (Valence/Arousal progress bars)
- components/MemoryPanel.tsx (memory count display)
- main.tsx (React entry)

## Task 18: Backend API routes

Update `src/api.py` with new routes:
- POST /api/chat/{user_id} — SSE streaming
- GET/POST/DELETE /api/conversations/{user_id} — conversation CRUD
- GET /api/memory/{user_id}/stats — memory statistics

## Task 19: server.py

Create `server.py` — FastAPI entry point with uvicorn.

## Task 20: start.bat

Create one-click start script.

## Task 21: Verify

Start both servers, open browser, test chat, emotion panel, safety guard.
