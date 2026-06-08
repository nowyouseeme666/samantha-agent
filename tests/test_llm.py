"""Tests for LLM client and PromptBuilder."""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ======================================================================
# PromptBuilder
# ======================================================================

class TestPromptBuilder:
    @pytest.fixture
    def persona_path(self):
        return Path(__file__).parent.parent / "config" / "persona.yaml"

    @pytest.fixture
    def rules_path(self):
        return Path(__file__).parent.parent / "config" / "rules.yaml"

    def test_build_system_non_empty(self, persona_path, rules_path):
        """build_system should return a non-empty string."""
        from src.llm.prompt_builder import PromptBuilder

        builder = PromptBuilder(persona_path=persona_path, rules_path=rules_path)
        system_msg = builder.build_system()

        assert isinstance(system_msg, str)
        assert len(system_msg) > 0
        # Should contain persona name
        assert "Samantha" in system_msg

    def test_build_system_includes_tools(self, persona_path, rules_path):
        """build_system should list tool names when tools are provided."""
        from src.llm.prompt_builder import PromptBuilder

        tools = [
            {"name": "memory_search", "description": "搜索记忆"},
            {"name": "chat", "description": "对话"},
        ]
        builder = PromptBuilder(persona_path=persona_path, rules_path=rules_path)
        system_msg = builder.build_system(tools=tools)

        assert "memory_search" in system_msg
        assert "chat" in system_msg

    def test_build_user_concatenates_parts(self, persona_path, rules_path):
        """build_user should include long-term memories, recent history, and current message."""
        from src.llm.prompt_builder import PromptBuilder

        long_term = ["你之前说过你喜欢雨天。", "用户提到过在学吉他。"]
        history = ["用户: 你好", "Samantha: 嗨！今天过得怎么样？"]
        current = "我今天心情不太好"

        builder = PromptBuilder(persona_path=persona_path, rules_path=rules_path)
        user_msg = builder.build_user(
            long_term_memories=long_term,
            recent_history=history,
            current_message=current,
        )

        assert "雨天" in user_msg
        assert "吉他" in user_msg
        assert "你好" in user_msg
        assert "心情不太好" in user_msg

    def test_build_user_handles_empty_memories(self, persona_path, rules_path):
        """build_user should work with empty long-term memories."""
        from src.llm.prompt_builder import PromptBuilder

        builder = PromptBuilder(persona_path=persona_path, rules_path=rules_path)
        user_msg = builder.build_user(
            long_term_memories=[],
            recent_history=["用户: 嗨"],
            current_message="今天天气不错",
        )

        assert "今天天气不错" in user_msg
        assert "嗨" in user_msg


# ======================================================================
# LLMClient
# ======================================================================

class TestLLMClient:
    def test_client_requires_api_key(self):
        """LLMClient should raise ValueError without an API key."""
        from src.llm.client import LLMClient

        with pytest.raises(ValueError, match="API key"):
            LLMClient(api_key="")

    def test_client_initializes_with_key(self):
        """LLMClient should initialize successfully with a (fake) API key."""
        from src.llm.client import LLMClient

        client = LLMClient(api_key="sk-fake-test-key")
        assert client is not None
        assert client.api_key == "sk-fake-test-key"

    def test_client_default_model(self):
        """LLMClient should default to deepseek-chat model."""
        from src.llm.client import LLMClient

        client = LLMClient(api_key="sk-test")
        assert client.model == "deepseek-chat"

    def test_client_custom_model(self):
        """LLMClient should accept custom model names."""
        from src.llm.client import LLMClient

        client = LLMClient(api_key="sk-test", model="deepseek-reasoner")
        assert client.model == "deepseek-reasoner"

    @patch("src.llm.client.ChatDeepSeek")
    def test_chat_returns_response(self, mock_chat):
        """chat() should return a string response from the LLM."""
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="你好！有什么可以帮你的？")
        mock_chat.return_value = mock_instance

        from src.llm.client import LLMClient

        client = LLMClient(api_key="sk-test")
        response = client.chat("你好")

        assert response == "你好！有什么可以帮你的？"
        mock_instance.invoke.assert_called_once()
