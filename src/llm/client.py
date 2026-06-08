"""LLMClient — DeepSeek Chat API wrapper via LangChain."""

from __future__ import annotations

from typing import Any

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage


class LLMClient:
    """Thin wrapper around LangChain's ChatDeepSeek."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        if not api_key:
            raise ValueError("API key is required. Set DEEPSEEK_API_KEY env var.")

        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._llm = ChatDeepSeek(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(self, message: str, system_prompt: str = "") -> str:
        """Simple text-in/text-out chat (no tool calling)."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))
        result = self._llm.invoke(messages)
        return result.content

    def chat_with_tools(
        self,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_executor: Any | None = None,
    ) -> str:
        """Chat with tool calling support.

        Binds tools to the LLM, lets the LLM decide whether to call tools,
        executes any tool calls via *tool_executor*, and returns the final
        text response.  Supports up to 3 tool-calling rounds to prevent
        infinite loops.

        Args:
            message: The user message text.
            system_prompt: Optional system prompt.
            tools: Tool definitions in our internal dict format
                   (name / description / parameters / function / enabled).
            tool_executor: A ``ToolExecutor`` instance with ``run_one(name, args)``.
        """
        if not tools:
            return self.chat(message, system_prompt)

        # Convert our tool dicts to LangChain-compatible OpenAI function format.
        # Our dicts have extra keys (function, enabled) that LangChain doesn't expect.
        langchain_tools = []
        for t in tools:
            params = t.get("parameters", {}) or {}
            properties = {
                k: {"type": v.get("type", "string"), "description": v.get("description", "")}
                for k, v in params.items()
            }
            langchain_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": list(properties.keys()),
                    } if properties else {"type": "object", "properties": {}},
                },
            })

        llm_with_tools = self._llm.bind_tools(langchain_tools, tool_choice="auto")

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))

        # Up to 3 rounds of tool calling
        for _round in range(3):
            result = llm_with_tools.invoke(messages)

            if not hasattr(result, "tool_calls") or not result.tool_calls:
                # No more tool calls — return final text
                return result.content if result.content else ""

            # Append the AI message BEFORE tool results so the LLM sees its
            # own tool-calling decision in subsequent rounds.
            messages.append(result)

            # Execute tool calls
            for tc in result.tool_calls:
                tool_name = tc.get("name", "")
                tool_args = tc.get("args", {})
                try:
                    if tool_executor and hasattr(tool_executor, "run_one"):
                        tool_result = tool_executor.run_one(tool_name, tool_args)
                    else:
                        tool_result = f"Tool '{tool_name}' not available"
                except Exception as exc:
                    tool_result = f"Tool error: {exc}"
                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tc.get("id", ""))
                )

        # If we hit max rounds, return whatever the LLM last said
        last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        return last_ai.content if last_ai else ""

    def stream(self, message: str, system_prompt: str = ""):
        """Stream tokens from the LLM for SSE output."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=message))
        for chunk in self._llm.stream(messages):
            if chunk.content:
                yield chunk.content
