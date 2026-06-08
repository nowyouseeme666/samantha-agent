"""ToolExecutor — whitelist-validated, fault-tolerant tool execution.

Responsibilities:
    1. Whitelist validation — only registered tools can be called.
    2. Fault tolerance — one failing tool does not crash the executor.
    3. Context injection — passes shared state (memory, etc.) to tools.
    4. Result formatting — every result is a string suitable for the LLM.
"""

from __future__ import annotations

from typing import Any


class ToolExecutor:
    """Executes tool calls against a registered tool whitelist.

    Supports both batch execution (``execute()``) and single-tool
    execution (``run_one()``) for integration with LLM tool-calling loops.
    """

    def __init__(
        self,
        tools: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> None:
        """*tools* is a list of tool definitions from the registry.
        *context* is an optional shared context dict (e.g. memory, diary_path)
        that is merged into every tool call's arguments.
        """
        self._tools_by_name: dict[str, dict[str, Any]] = {}
        self._context: dict[str, Any] = context or {}
        for t in tools:
            if t.get("enabled", True):
                self._tools_by_name[t["name"]] = t

    # ------------------------------------------------------------------
    def execute(
        self,
        tool_calls: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a batch of tool calls sequentially.

        Args:
            tool_calls: [{"name": "...", "args": {...}}, ...]
            context: Per-call context dict merged on top of the executor's
                     stored context (e.g. {"memory": LongTermMemory, ...}).

        Returns:
            [{"name": "...", "result": "..."}, ...] — ordered list of results.
        """
        ctx = {**self._context, **(context or {})}
        results: list[dict[str, Any]] = []

        for call in tool_calls:
            name = call.get("name", "")
            args = call.get("args", {}) or {}

            tool = self._tools_by_name.get(name)
            if tool is None:
                results.append({
                    "name": name,
                    "result": f"[error] 未找到工具 '{name}'，请检查工具名称是否正确。",
                })
                continue

            try:
                func = tool["function"]
                # Merge args with context — context keys not overridden by args
                merged = {**ctx, **args}
                result_str = func(**merged)
                results.append({
                    "name": name,
                    "result": str(result_str),
                })
            except Exception as exc:
                results.append({
                    "name": name,
                    "result": f"[error] 工具 '{name}' 执行失败：{exc}",
                })

        return results

    def run_one(self, name: str, args: dict[str, Any] | None = None) -> str:
        """Execute a single tool call — compatible with LLM tool-calling loops.

        Args:
            name: Tool name (must be registered and enabled).
            args: Tool arguments dict (merged with executor context).

        Returns:
            The tool's result string, or an error message.
        """
        results = self.execute(
            tool_calls=[{"name": name, "args": args or {}}],
            context=self._context,
        )
        if not results:
            return f"[error] 工具 '{name}' 未返回任何结果。"
        return results[0]["result"]

    @property
    def available_tools(self) -> list[str]:
        """Return names of all registered (enabled) tools."""
        return list(self._tools_by_name.keys())
