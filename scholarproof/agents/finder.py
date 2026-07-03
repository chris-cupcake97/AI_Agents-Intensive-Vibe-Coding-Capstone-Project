"""Finder Agent for fixture-mode scholarship discovery."""

from __future__ import annotations

from typing import Any

from .common import call_structured_tool


class FinderAgent:
    """Finds candidate scholarships without deciding eligibility."""

    name = "Finder Agent"

    def search(
        self,
        *,
        profile_id: str | None = None,
        query: str = "",
        limit: int | None = None,
    ) -> dict[str, Any]:
        tool_input: dict[str, Any] = {"query": query}
        if profile_id:
            tool_input["profile_id"] = profile_id

        output = call_structured_tool("search_scholarships", tool_input)

        candidates = []
        for candidate in output["candidates"]:
            safe_candidate = dict(candidate)
            safe_candidate.pop("status", None)
            safe_candidate.pop("student_facing_status", None)
            candidates.append(safe_candidate)

        if limit is not None:
            candidates = candidates[:limit]

        return {
            "agent": self.name,
            "decides_eligibility": False,
            "mode": output["mode"],
            "profile_id": output.get("profile_id"),
            "query": output.get("query", query),
            "count": len(candidates),
            "candidates": candidates,
        }
