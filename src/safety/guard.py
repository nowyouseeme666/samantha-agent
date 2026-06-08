"""SafetyGuard — input/output content safety filter.

Checks messages against blocked and warning keyword lists.  Returns
one of three verdicts:

    normal  — no keywords matched
    warning — matched a warning keyword (but not blocked)
    blocked — matched a blocked keyword (response suppressed)
"""

from __future__ import annotations


class SafetyGuard:
    """Checks user and agent messages against keyword blocklists."""

    def __init__(
        self,
        blocked_keywords: list[str] | None = None,
        warning_keywords: list[str] | None = None,
    ) -> None:
        self.blocked_keywords = list(blocked_keywords or [])
        self.warning_keywords = list(warning_keywords or [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, text: str) -> str:
        """Evaluate *text* and return 'normal', 'warning', or 'blocked'.

        Blocked keywords take priority over warning keywords.
        Matching is case-insensitive.
        """
        lower = text.lower()

        for kw in self.blocked_keywords:
            if kw.lower() in lower:
                return "blocked"

        for kw in self.warning_keywords:
            if kw.lower() in lower:
                return "warning"

        return "normal"

    def get_blocked_response(self) -> str:
        """Return a safe fallback message for blocked content."""
        return "抱歉，我无法对此作出回应。如果你需要帮助，可以拨打心理援助热线。"
