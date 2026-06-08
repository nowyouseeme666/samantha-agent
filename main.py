#!/usr/bin/env python3
"""Samantha Agent -- CLI entry point.

Usage:
    python main.py --mode cli
    echo "quit" | python main.py --mode cli

Phase 1 provides a basic conversational loop that wires together all
six infrastructure layers: config -> schemas -> memory -> llm -> graph -> safety.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger

# -- Project root (so imports work when run as script) --
_PROJECT_ROOT = Path(__file__).resolve().parent
_CONFIG_DIR = _PROJECT_ROOT / "config"


def run_cli(api_key: str) -> None:
    """Interactive conversational loop (CLI mode)."""
    from src.config import SamanthaSettings, PersonaConfig, RulesConfig, ToolsConfig
    from src.llm.client import LLMClient
    from src.llm.prompt_builder import PromptBuilder
    from src.memory.short_term import ShortTermMemory
    from src.memory.long_term import LongTermMemory
    from src.memory.immutable import ImmutableMemory
    from src.safety.guard import SafetyGuard
    from src.safety.monitor import EmotionMonitor
    from src.schemas.emotion import EmotionState
    from src.schemas.memory import MemoryEntry, MemoryCategory
    from src.tools.executor import ToolExecutor
    from src.tools.registry import ALL_TOOLS

    # ---- Load configuration ----
    settings = SamanthaSettings(
        _yaml_config=_CONFIG_DIR / "settings.yaml",
        _persona_dir=_CONFIG_DIR,
        deepseek_api_key=api_key,
    )
    logger.info("Settings loaded (model={})", settings.llm_model)

    persona = PersonaConfig.from_yaml(_CONFIG_DIR / "persona.yaml")
    rules = RulesConfig.from_yaml(_CONFIG_DIR / "rules.yaml")
    tools_cfg = ToolsConfig.from_yaml(_CONFIG_DIR / "tools.yaml")

    # ---- Initialise LLM ----
    llm = LLMClient(
        api_key=api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )

    # ---- Initialise prompt builder ----
    prompt_builder = PromptBuilder(
        persona_path=_CONFIG_DIR / "persona.yaml",
        rules_path=_CONFIG_DIR / "rules.yaml",
    )

    # ---- Initialise memory layers ----
    short_term = ShortTermMemory(max_rounds=settings.memory_short_term_max_rounds)
    long_term = LongTermMemory(chroma_dir=settings.memory_long_term_chroma_dir)
    immutable = ImmutableMemory.from_yaml(_CONFIG_DIR / "persona.yaml")

    # ---- Initialise safety ----
    guard = SafetyGuard(
        blocked_keywords=settings.safety_blocked_keywords,
        warning_keywords=settings.safety_warning_keywords,
    )
    monitor = EmotionMonitor(risk_threshold=settings.safety_emotion_risk_threshold)

    # ---- Initialise tool executor ----
    tool_executor = ToolExecutor(tools=ALL_TOOLS, context={"memory": long_term})

    # ---- Current emotion state ----
    emotion = EmotionState()

    # ---- Greeting ----
    greeting_lines = rules._data.get("greeting", {})
    greeting = greeting_lines.get("default", "嗨，我在呢~")
    logger.info("Samantha CLI started. Type 'quit' to exit, 'help' for commands.")
    print(f"\nSamantha: {greeting}\n")

    # ---- Conversation loop ----
    turn = 0

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！保重。")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("再见！保重。")
            break

        if user_input.lower() == "help":
            print("Commands: quit/exit/q to exit, help, stats")
            continue

        if user_input.lower() == "stats":
            print(f"  Short-term rounds: {len(short_term)}")
            print(f"  Long-term entries: {len(long_term._entries)}")
            print(f"  Current emotion: {emotion.label} (valence={emotion.valence:+.1f})")
            print(f"  Risk level: {monitor.current_risk}")
            continue

        turn += 1

        # -- Safety check: input --
        safety_result = guard.check(user_input)
        if safety_result == "blocked":
            print(f"Samantha: {guard.get_blocked_response()}\n")
            continue

        # -- Store in short-term memory --
        short_term.add(MemoryEntry(
            id=f"turn-{turn}-user",
            content=user_input,
            summary=user_input[:100],
            category=MemoryCategory.EVENT,
        ))

        # -- Build prompt --
        enabled_tools = tools_cfg.enabled_tools()
        system_msg = prompt_builder.build_system(
            emotion_state=emotion.to_dict(),
            tools=enabled_tools,
        )

        short_history = [
            f"User: {e.content}" if "turn-" in e.id and "user" in e.id
            else f"Samantha: {e.content}"
            for e in short_term.get(query="", k=6)
        ]
        short_history = list(reversed(short_history))  # chronological

        user_msg = prompt_builder.build_user(
            long_term_memories=[
                e.summary for e in long_term.get(query=user_input, k=5)
            ],
            recent_history=short_history,
            current_message=user_input,
        )

        # -- Call LLM with tool support --
        try:
            response = llm.chat_with_tools(
                message=user_msg,
                system_prompt=system_msg,
                tools=enabled_tools,
                tool_executor=tool_executor,
            )
        except Exception as exc:
            logger.error("LLM call failed: {}", exc)
            print(f"Samantha: {settings.dialogue_fallback_message}\n")
            continue

        # -- Safety check: output --
        output_safety = guard.check(response)
        if output_safety == "blocked":
            response = guard.get_blocked_response()

        # -- Store response in short-term memory --
        short_term.add(MemoryEntry(
            id=f"turn-{turn}-samantha",
            content=response,
            summary=response[:100],
            category=MemoryCategory.EVENT,
        ))

        # -- Also store in long-term memory for future RAG --
        long_term.add(MemoryEntry(
            id=f"lt-{turn}",
            content=f"User: {user_input}\nSamantha: {response}",
            summary=f"User['{user_input[:50]}'], Samantha['{response[:50]}']",
            category=MemoryCategory.EVENT,
        ))

        # -- Placeholder emotion update --
        # In Phase 2 this will use a real emotion detector.
        # For now, update the monitor with a neutral state.
        monitor.update(emotion)

        print(f"Samantha: {response}\n")

    logger.info("CLI session ended. {} turns processed.", turn)


# ======================================================================
# Argument parsing
# ======================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Samantha - Emotional Companion Agent")
    parser.add_argument(
        "--mode",
        choices=("cli",),
        default="cli",
        help="Run mode (Phase 1: cli only)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="DeepSeek API key (falls back to DEEPSEEK_API_KEY env var)",
    )
    args = parser.parse_args()

    api_key = args.api_key or None

    # Try loading from .env via pydantic-settings
    if not api_key:
        try:
            from src.config import SamanthaSettings
            settings = SamanthaSettings(
                _yaml_config=_CONFIG_DIR / "settings.yaml",
                _persona_dir=_CONFIG_DIR,
            )
            api_key = settings.deepseek_api_key
        except Exception:
            pass

    if args.mode == "cli":
        if not api_key:
            print("[Info] Set DEEPSEEK_API_KEY in .env or environment, or use --api-key")
            print("       Entering demo mode (no LLM connection)\n")
            run_cli_demo()
        else:
            run_cli(api_key)


def run_cli_demo() -> None:
    """Demo mode: runs without a real LLM, just echoes the pipeline."""
    from src.config import PersonaConfig, RulesConfig
    from src.safety.guard import SafetyGuard
    from src.safety.monitor import EmotionMonitor
    from src.schemas.emotion import EmotionState

    print("Demo mode -- LLM calls are simulated.")
    print("   Type 'quit' to exit, 'help' for commands.\n")

    persona = PersonaConfig.from_yaml(_CONFIG_DIR / "persona.yaml")
    guard = SafetyGuard()
    monitor = EmotionMonitor()
    emotion = EmotionState()
    turn = 0

    echo_responses = [
        "Sounds interesting, tell me more?",
        "I understand how you feel.",
        "Thanks for sharing, I'm listening.",
        "That's totally normal, you're not alone.",
        "Go on, I'm here for you.",
    ]

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Take care.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye! Take care.")
            break
        if user_input.lower() == "help":
            print("Demo mode -- no LLM connected, responses from preset list.")
            continue

        turn += 1

        safety = guard.check(user_input)
        if safety == "blocked":
            print(f"Samantha: {guard.get_blocked_response()}\n")
            continue

        monitor.update(emotion)
        response = echo_responses[turn % len(echo_responses)]
        print(f"Samantha: {response}\n")


if __name__ == "__main__":
    main()
