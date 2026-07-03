"""Smoke test the ADK-style ScholarProof agent layer."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scholarproof.agents import (  # noqa: E402
    ClarificationEmailSkillWrapper,
    FinderAgent,
    RootOrchestratorAgent,
    VerifierAgent,
)
from scholarproof.agents.verifier import EXPECTED_TOOL_SEQUENCE  # noqa: E402
from scholarproof.api.store import store  # noqa: E402


def _load_case(case_id: str) -> dict:
    cases = json.loads((ROOT / "evals" / "eval_cases.json").read_text(encoding="utf-8"))
    for case in cases:
        if case["id"] == case_id:
            return case
    raise AssertionError(f"Missing fixture case: {case_id}")


def _tool_names(verifier_result: dict) -> list[str]:
    return [step["tool"] for step in verifier_result["tool_trace"]]


def _assert_no_false_eligible(verification: dict) -> None:
    if verification["status"] != "eligible":
        return
    assert verification["source_url"]
    assert verification["source_official"] is True
    assert not verification["missing_required_rules"]
    assert not verification["blocking_rules"]
    assert not verification["unclear_rules"]


def main() -> int:
    store.reset()

    finder = FinderAgent()
    verifier = VerifierAgent()
    orchestrator = RootOrchestratorAgent(finder=finder, verifier=verifier)
    email_skill = ClarificationEmailSkillWrapper()

    unclear_case = _load_case("unclear_01")
    eligible_case = _load_case("eligible_01")
    unverified_case = _load_case("unverified_01")
    not_eligible_case = _load_case("not_eligible_01")

    finder_result = finder.search(query="Bristol", limit=3)
    assert finder_result["count"] >= 1
    assert finder_result["decides_eligibility"] is False
    for candidate in finder_result["candidates"]:
        assert "status" not in candidate
        assert "student_facing_status" not in candidate

    orchestrated = orchestrator.run(
        profile=unclear_case["profile"],
        search_query="Bristol",
        max_candidates=3,
    )
    assert orchestrated["finder_result"]["count"] >= 1
    assert orchestrated["verifications"]
    assert set(orchestrated["grouped_results"]) == {
        "eligible",
        "unclear",
        "not_eligible",
        "unverified",
    }
    for verifier_result in orchestrated["verifications"]:
        assert _tool_names(verifier_result) == EXPECTED_TOOL_SEQUENCE
        _assert_no_false_eligible(verifier_result["verification"])

    unclear_verification = verifier.verify(
        candidate=unclear_case["candidate"],
        profile=unclear_case["profile"],
        fixture_id=unclear_case["id"],
    )
    assert _tool_names(unclear_verification) == EXPECTED_TOOL_SEQUENCE
    assert unclear_verification["verification"]["status"] == "unclear"

    unclear_draft = email_skill.draft(
        unclear_verification["verification"],
        student_name="Demo Student",
    )
    assert unclear_draft["ok"] is True
    assert unclear_draft["draft"]["send_allowed"] is False

    eligible_verification = verifier.verify(
        candidate=eligible_case["candidate"],
        profile=eligible_case["profile"],
        fixture_id=eligible_case["id"],
    )
    assert eligible_verification["verification"]["status"] == "eligible"
    _assert_no_false_eligible(eligible_verification["verification"])
    eligible_draft = email_skill.draft(eligible_verification["verification"])
    assert eligible_draft["ok"] is False
    assert eligible_draft["send_allowed"] is False

    unverified = verifier.verify(
        candidate=unverified_case["candidate"],
        profile=unverified_case["profile"],
        fixture_id=unverified_case["id"],
    )["verification"]
    assert unverified["status"] == "unverified"
    assert unverified["source_type"] == "aggregator_lead"
    assert unverified["source_official"] is False

    not_eligible = verifier.verify(
        candidate=not_eligible_case["candidate"],
        profile=not_eligible_case["profile"],
        fixture_id=not_eligible_case["id"],
    )["verification"]
    assert not_eligible["status"] == "not_eligible"
    assert not_eligible["blocking_rules"]

    print("ScholarProof agent smoke")
    print("orchestrator_fixture_search: ok")
    print("finder_returns_candidates_without_verdicts: ok")
    print("verifier_tool_sequence: ok")
    print("unclear_email_draft: ok")
    print("eligible_email_rejected: ok")
    print("aggregator_unverified: ok")
    print("blocking_not_eligible: ok")
    print("false_eligible_protection: ok")
    print("passed: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

