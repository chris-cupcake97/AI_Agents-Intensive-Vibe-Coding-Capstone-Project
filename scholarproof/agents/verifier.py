"""Verifier Agent that executes the required tool trajectory."""

from __future__ import annotations

from typing import Any

from .common import call_structured_tool, ensure_no_false_eligible, summarize_tool_output


EXPECTED_TOOL_SEQUENCE = [
    "fetch_page",
    "classify_source",
    "detect_prompt_injection",
    "extract_rules",
    "match_profile",
    "generate_verdict",
    "write_audit_log",
]


class VerifierAgent:
    """Verifies one scholarship candidate using the MCP-style tools."""

    name = "Verifier Agent"

    def verify(
        self,
        *,
        candidate: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        fixture_id: str | None = None,
    ) -> dict[str, Any]:
        candidate_data = dict(candidate or {})
        fixture_lookup = {
            "fixture_id": fixture_id
            or candidate_data.get("fixture_id")
            or candidate_data.get("case_id"),
            "candidate_id": candidate_data.get("id"),
        }
        fixture_lookup = {key: value for key, value in fixture_lookup.items() if value}

        tool_trace: list[dict[str, Any]] = []
        audit_log: list[dict[str, Any]] = []

        def use_tool(name: str, input_data: dict[str, Any]) -> dict[str, Any]:
            output = call_structured_tool(name, input_data)
            summary = summarize_tool_output(name, output)
            tool_trace.append(
                {
                    "order": len(tool_trace) + 1,
                    "tool": name,
                    "ok": True,
                    "output_summary": summary,
                }
            )
            if name != "generate_verdict":
                audit_log.append(
                    {
                        "step": str(len(tool_trace)),
                        "tool": name,
                        "input_summary": ", ".join(sorted(input_data)) or "empty input",
                        "output_summary": summary,
                        "success": True,
                    }
                )
            return output

        page = use_tool("fetch_page", fixture_lookup)
        source = use_tool(
            "classify_source",
            {
                "url": page["url"],
                "provider": page["provider"],
            },
        )["source"]
        security = use_tool(
            "detect_prompt_injection",
            {
                "page_text": page["page_text"],
            },
        )
        rules = use_tool(
            "extract_rules",
            {
                "page_text": page["page_text"],
                "source_url": page["url"],
                "fixture_rules": page["fixture_rules"],
            },
        )

        profile_data = dict(profile or page["profile"])
        candidate_for_verdict = dict(candidate_data or page["candidate"])
        candidate_for_verdict.setdefault("candidate_url", page["url"])

        matched = use_tool(
            "match_profile",
            {
                "profile": profile_data,
                "rules": rules["rules"],
            },
        )
        verification = use_tool(
            "generate_verdict",
            {
                "profile": profile_data,
                "candidate": candidate_for_verdict,
                "source": source,
                "matched_rules": matched["matched_rules"],
                "blocking_rules": matched["blocking_rules"],
                "unclear_rules": matched["unclear_rules"],
                "security_flags": security["security_flags"],
                "audit_log": audit_log,
            },
        )["verification"]
        ensure_no_false_eligible(verification)

        use_tool(
            "write_audit_log",
            {
                "verification_id": verification["id"],
                "event": {
                    "step": "7",
                    "tool": "write_audit_log",
                    "input_summary": "Verifier Agent completed required tool trajectory.",
                    "output_summary": f"status={verification['status']}",
                    "success": True,
                },
            },
        )

        return {
            "agent": self.name,
            "verification": verification,
            "tool_trace": tool_trace,
            "expected_tool_sequence": EXPECTED_TOOL_SEQUENCE,
        }
