"""Shared helpers for the ADK-style agent layer."""

from __future__ import annotations

from typing import Any

from scholarproof.mcp_server.registry import call_tool


class AgentError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def call_structured_tool(name: str, input_data: dict[str, Any]) -> dict[str, Any]:
    result = call_tool(name, input_data)
    if not result["ok"]:
        error = result["error"]
        raise AgentError(str(error["code"]), str(error["message"]))
    output = result["output"]
    if not isinstance(output, dict):
        raise AgentError("invalid_tool_output", f"{name} returned non-object output.")
    return output


def summarize_tool_output(tool_name: str, output: dict[str, Any]) -> str:
    if tool_name == "search_scholarships":
        return f"count={output.get('count', 0)}"
    if tool_name == "fetch_page":
        return f"fixture={output.get('fixture')}; url={output.get('url') or '<missing>'}"
    if tool_name == "classify_source":
        source = output.get("source", {})
        return f"type={source.get('source_type')}; official={source.get('is_official')}"
    if tool_name == "detect_prompt_injection":
        return f"flags={len(output.get('security_flags', []))}"
    if tool_name == "extract_rules":
        return f"rules={output.get('count', 0)}"
    if tool_name == "match_profile":
        return (
            f"matched={output.get('matched_count', 0)}; "
            f"blocking={output.get('blocking_count', 0)}; "
            f"unclear={output.get('unclear_count', 0)}"
        )
    if tool_name == "generate_verdict":
        verification = output.get("verification", {})
        return f"status={verification.get('status')}"
    if tool_name == "write_audit_log":
        return f"persisted={output.get('persisted')}"
    return "ok"


def ensure_no_false_eligible(verification: dict[str, Any]) -> None:
    if verification.get("status") != "eligible":
        return
    if not verification.get("source_url") or not verification.get("source_official"):
        raise AgentError(
            "false_eligible_guard",
            "Verifier refused eligible without official source URL and official source classification.",
        )
    if verification.get("missing_required_rules"):
        raise AgentError(
            "false_eligible_guard",
            "Verifier refused eligible with missing required rule evidence.",
        )
    if verification.get("blocking_rules") or verification.get("unclear_rules"):
        raise AgentError(
            "false_eligible_guard",
            "Verifier refused eligible with blocking or unclear rules.",
        )

