# Samantha Agent

Samantha 是一个情感陪伴 AI 助手，基于 RAG 记忆、情绪状态机和工具调用构建。

**Tech Stack:** Python 3.12 / LangChain / LangGraph / ChromaDB / DeepSeek | React 18 + TypeScript + Vite 5 + Tailwind CSS

## Architecture

```
samantha-agent/
├── config/              # YAML 配置 (persona, rules, tools, settings)
├── src/
│   ├── config.py        # pydantic Settings + YAML 加载器
│   ├── api.py           # FastAPI 后端 (Phase 2)
│   ├── schemas/         # MemoryEntry, EmotionState, AgentState
│   ├── memory/          # 三层记忆 (short-term, long-term, immutable)
│   │   └── orchestrator.py  # 记忆编排器 (Phase 2)
│   ├── emotion/         # 情绪检测器 — 规则 + LLM 混合 (Phase 2)
│   ├── llm/             # DeepSeek LLM 客户端 + Prompt 组装
│   ├── graph/           # LangGraph StateGraph 编排
│   ├── safety/          # 内容安全过滤 + 情绪风险监控
│   └── tools/           # Agent 工具实现 (Phase 2)
├── frontend/            # React 前端 (Phase 2)
│   └── src/components/  # ChatBox, ChatInput, EmotionPanel, MemoryPanel
├── tests/               # pytest 单元 + 集成测试
└── main.py              # CLI 入口
```

## Quick Start

```bash
# 安装依赖
pip install -r requirements.txt

# CLI 模式 (无需 API Key — 演示模式)
python main.py --mode cli

# CLI 模式 (使用真实 LLM)
export DEEPSEEK_API_KEY=sk-your-key
python main.py --mode cli

# --- 后端 API 模式 ---
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload

# --- 前端开发 ---
cd frontend
npm install
npm run dev        # → http://localhost:5173
```

## API Endpoints

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息，返回完整响应 |
| GET | `/api/memory` | 获取当前记忆上下文 |
| GET | `/api/emotion` | 获取当前情绪状态 |
| GET | `/api/health` | 健康检查 |

### POST /api/chat

```json
// Request
{ "message": "今天心情不太好" }

// Response
{
  "reply": "我在听，想跟我说说发生了什么吗？",
  "emotion": { "valence": -0.3, "arousal": 0.2, "label": "sad" },
  "memories_used": ["用户喜欢咖啡", "昨天提到工作压力大"],
  "safety_flag": "normal"
}
```

## Three-Layer Memory

| Layer | Implementation | Capacity | Purpose |
|-------|---------------|----------|---------|
| Short-term | Sliding window (deque) | 20 rounds | Conversation context |
| Long-term | RAG + ChromaDB (Phase 2: keyword search) | Unlimited | Historical recall |
| Immutable | persona.yaml injection | Fixed | Core identity |

## Emotion Detection

Hybrid approach: rule-based keyword matching (fast, high-confidence) → LLM fallback (subtle/implicit expressions).

| Keyword | valence | arousal | label |
|---------|---------|---------|-------|
| 开心/高兴/哈哈 | +0.7 | +0.6 | happy |
| 难过/伤心/哭 | -0.6 | -0.3 | sad |
| 生气/愤怒/烦 | -0.7 | +0.7 | angry |
| 焦虑/担心/紧张 | -0.5 | +0.6 | anxious |
| 累/疲惫/困 | -0.3 | -0.5 | tired |
| 平静/还好/没事 | 0.0 | -0.3 | neutral |

## Agent Tools

| Tool | Description |
|------|-------------|
| `search_memories` | Search long-term memory |
| `record_emotion` | Record emotion diary entry |
| `set_reminder` / `list_reminders` | Schedule reminders |
| `recommend_music` | Recommend music by emotion |
| `get_weather` | Query weather via wttr.in |

## LangGraph Flow

```
START → agent_node → tool_node (loop) → safety_guard → respond_node → END
```

## Running Tests

```bash
pytest tests/ -v          # 144 tests
```

## Phase 1

- [x] Project scaffold & config
- [x] Data schemas (MemoryEntry, EmotionState, AgentState)
- [x] Three-layer memory
- [x] LLM client (DeepSeek via LangChain)
- [x] Prompt builder
- [x] LangGraph skeleton
- [x] Safety modules
- [x] CLI entry point

## Phase 2

- [x] FastAPI backend (4 endpoints)
- [x] Emotion detector (rules + LLM)
- [x] Memory orchestrator (decay scoring + dedup)
- [x] Agent tools (5 tools + executor)
- [x] React frontend (ChatBox, EmotionPanel, MemoryPanel, ChatInput)
- [x] Integration tests (16 scenarios)
- [x] README update

## Design System

See [DESIGN.md](DESIGN.md) for the frontend visual design system.
See [../samantha-design.md](../samantha-design.md) for the overall architecture design.
