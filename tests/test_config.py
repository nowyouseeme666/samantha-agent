"""Tests for config module — pydantic Settings and YAML loader."""
import os
import pytest
from pathlib import Path


# ---- YAML loading ----

def test_load_yaml_single():
    """load_yaml should parse a YAML file into a dict."""
    from src.config import load_yaml

    config_dir = Path(__file__).parent.parent / "config"
    data = load_yaml(config_dir / "persona.yaml")

    assert isinstance(data, dict)
    assert data["name"] == "Samantha"
    assert data["identity"]["role"] == "情感陪伴助手"


def test_load_yaml_not_found():
    """load_yaml should raise FileNotFoundError for missing files."""
    from src.config import load_yaml

    with pytest.raises(FileNotFoundError):
        load_yaml(Path("nonexistent_file.yaml"))


# ---- SamanthaSettings ----

class TestSamanthaSettings:
    """Tests for the pydantic Settings model."""

    def test_settings_defaults(self):
        """SamanthaSettings should load defaults from settings.yaml."""
        from src.config import SamanthaSettings

        config_dir = Path(__file__).parent.parent / "config"
        settings = SamanthaSettings(
            _yaml_config=config_dir / "settings.yaml",
            _persona_dir=config_dir,
        )

        assert settings.llm_model == "deepseek-chat"
        assert settings.llm_temperature == 0.7

    def test_settings_memory_defaults(self):
        """Memory settings should load from YAML with correct defaults."""
        from src.config import SamanthaSettings

        config_dir = Path(__file__).parent.parent / "config"
        settings = SamanthaSettings(
            _yaml_config=config_dir / "settings.yaml",
            _persona_dir=config_dir,
        )

        assert settings.memory_short_term_max_rounds == 20
        assert settings.memory_long_term_chroma_dir == "./data/chroma"
        assert settings.memory_long_term_retrieval_k == 5

    def test_settings_env_override(self, monkeypatch):
        """Environment variable should override YAML default."""
        from src.config import SamanthaSettings

        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-override-key")

        config_dir = Path(__file__).parent.parent / "config"
        settings = SamanthaSettings(
            _yaml_config=config_dir / "settings.yaml",
            _persona_dir=config_dir,
        )

        assert settings.deepseek_api_key == "sk-test-override-key"

    def test_settings_safety_defaults(self):
        """Safety settings should load from YAML."""
        from src.config import SamanthaSettings

        config_dir = Path(__file__).parent.parent / "config"
        settings = SamanthaSettings(
            _yaml_config=config_dir / "settings.yaml",
            _persona_dir=config_dir,
        )

        assert settings.safety_emotion_risk_threshold == 3

    def test_settings_str_method(self):
        """SamanthaSettings should have a readable __str__ without leaking API key."""
        from src.config import SamanthaSettings

        config_dir = Path(__file__).parent.parent / "config"
        settings = SamanthaSettings(
            _yaml_config=config_dir / "settings.yaml",
            _persona_dir=config_dir,
            deepseek_api_key="sk-secret-123",
        )

        s = str(settings)
        assert "sk-secret-123" not in s
        assert "***" in s


# ---- PersonaConfig ----

class TestPersonaConfig:
    def test_persona_load(self):
        """PersonaConfig should parse persona.yaml correctly."""
        from src.config import PersonaConfig

        config_dir = Path(__file__).parent.parent / "config"
        persona = PersonaConfig.from_yaml(config_dir / "persona.yaml")

        assert persona.name == "Samantha"
        assert len(persona.traits) >= 3
        assert "温柔体贴" in persona.traits

    def test_persona_to_system_text(self):
        """to_system_text should format persona into prompt-ready text."""
        from src.config import PersonaConfig

        config_dir = Path(__file__).parent.parent / "config"
        persona = PersonaConfig.from_yaml(config_dir / "persona.yaml")
        text = persona.to_system_text()

        assert "Samantha" in text
        assert "温柔体贴" in text
        assert "不提供医疗诊断建议" in text


# ---- RulesConfig ----

class TestRulesConfig:
    def test_rules_load(self):
        """RulesConfig should parse rules.yaml correctly."""
        from src.config import RulesConfig

        config_dir = Path(__file__).parent.parent / "config"
        rules = RulesConfig.from_yaml(config_dir / "rules.yaml")

        assert len(rules.red_lines) >= 2
        assert any("自杀" in line for line in rules.red_lines)

    def test_rules_to_system_text(self):
        """to_system_text should include red lines in output."""
        from src.config import RulesConfig

        config_dir = Path(__file__).parent.parent / "config"
        rules = RulesConfig.from_yaml(config_dir / "rules.yaml")
        text = rules.to_system_text()

        assert "红线" in text or "规则" in text


# ---- ToolsConfig ----

class TestToolsConfig:
    def test_tools_load(self):
        """ToolsConfig should parse tools.yaml correctly."""
        from src.config import ToolsConfig

        config_dir = Path(__file__).parent.parent / "config"
        tools_cfg = ToolsConfig.from_yaml(config_dir / "tools.yaml")

        assert len(tools_cfg.tools) == 6
        tool_names = [t["name"] for t in tools_cfg.tools]
        assert "search_memories" in tool_names
        assert "get_weather" in tool_names

    def test_enabled_tools(self):
        """enabled_tools should return only tools with enabled=True."""
        from src.config import ToolsConfig

        config_dir = Path(__file__).parent.parent / "config"
        tools_cfg = ToolsConfig.from_yaml(config_dir / "tools.yaml")
        enabled = tools_cfg.enabled_tools()

        assert len(enabled) == 6
        enabled_names = [t["name"] for t in enabled]
        assert "get_weather" in enabled_names

    def test_get_tool_by_name(self):
        """get_tool should return correct tool definition or None."""
        from src.config import ToolsConfig

        config_dir = Path(__file__).parent.parent / "config"
        tools_cfg = ToolsConfig.from_yaml(config_dir / "tools.yaml")

        weather_tool = tools_cfg.get_tool("get_weather")
        assert weather_tool is not None
        assert weather_tool["name"] == "get_weather"
        assert weather_tool["enabled"] is True

        missing = tools_cfg.get_tool("nonexistent")
        assert missing is None
