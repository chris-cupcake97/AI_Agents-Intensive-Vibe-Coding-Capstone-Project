"""Application services used by the FastAPI routes and smoke tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fundmydegree.core.destination import destination_supported
from fundmydegree.core.fixture_flow import verify_fixture_case
from fundmydegree.core.models import utc_now_iso

from .store import InMemoryStore, store


ROOT = Path(__file__).resolve().parents[2]
EVAL_CASES_PATH = ROOT / "evals" / "eval_cases.json"


class ApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _load_eval_cases() -> list[dict[str, Any]]:
    return json.loads(EVAL_CASES_PATH.read_text(encoding="utf-8"))


def _profile_id(profile: dict[str, Any]) -> str:
    profile_id = str(profile.get("id", "")).strip()
    if profile_id:
        return profile_id
    return f"profile_{uuid4().hex[:8]}"


def _find_case(fixture_id: str | None = None, candidate_id: str | None = None) -> dict[str, Any]:
    for case in _load_eval_cases():
        candidate = case.get("candidate", {})
        if fixture_id and case.get("id") == fixture_id:
            return case
        if candidate_id and candidate.get("id") == candidate_id:
            return case
    lookup = fixture_id or candidate_id or "<missing>"
    raise ApiError(404, f"No fixture scholarship found for {lookup}.")


def _verification_or_404(verification_id: str, data_store: InMemoryStore = store) -> dict[str, Any]:
    verification = data_store.verifications.get(verification_id)
    if not verification:
        raise ApiError(404, f"Verification not found: {verification_id}.")
    return verification


def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "fundmydegree-api",
        "mode": "fixture",
        "verdict_policy": "conservative",
    }


def create_profile(profile_data: dict[str, Any], data_store: InMemoryStore = store) -> dict[str, Any]:
    profile = dict(profile_data)
    profile["id"] = _profile_id(profile)
    data_store.profiles[profile["id"]] = profile
    return {"profile": profile, "created": True}


def get_profile(profile_id: str, data_store: InMemoryStore = store) -> dict[str, Any]:
    profile = data_store.profiles.get(profile_id)
    if not profile:
        raise ApiError(404, f"Profile not found: {profile_id}.")
    return {"profile": profile}


def search_scholarships(
    request: dict[str, Any],
    data_store: InMemoryStore = store,
) -> dict[str, Any]:
    profile_id = str(request.get("profile_id", "")).strip()
    profile = None
    if profile_id and profile_id not in data_store.profiles:
        raise ApiError(404, f"Profile not found: {profile_id}.")
    if profile_id:
        profile = data_store.profiles[profile_id]

    query = str(request.get("query", "")).strip().lower()
    candidates: list[dict[str, Any]] = []

    for case in _load_eval_cases():
        candidate = dict(case["candidate"])
        searchable = " ".join(
            [
                candidate.get("name", ""),
                candidate.get("provider", ""),
                candidate.get("country", ""),
                candidate.get("candidate_url", ""),
            ]
        ).lower()
        if query and query not in searchable:
            continue
        if profile and not destination_supported(
            candidate.get("country", ""),
            list(profile.get("target_regions", [])),
        ):
            continue

        candidate["fixture_id"] = case["id"]
        candidate["fixture"] = case["fixture"]
        candidate["mode"] = "fixture"
        candidates.append(candidate)

    return {
        "mode": "fixture",
        "profile_id": profile_id or None,
        "query": request.get("query", ""),
        "count": len(candidates),
        "candidates": candidates,
    }


def verify_scholarship(
    request: dict[str, Any],
    data_store: InMemoryStore = store,
) -> dict[str, Any]:
    fixture_id = request.get("fixture_id") or request.get("case_id")
    candidate_id = request.get("candidate_id")
    case = copy.deepcopy(_find_case(fixture_id=fixture_id, candidate_id=candidate_id))

    profile_id = str(request.get("profile_id", "")).strip()
    if profile_id:
        profile = data_store.profiles.get(profile_id)
        if not profile:
            raise ApiError(404, f"Profile not found: {profile_id}.")
        case["profile"] = profile
    elif request.get("profile"):
        profile = dict(request["profile"])
        profile["id"] = _profile_id(profile)
        data_store.profiles[profile["id"]] = profile
        case["profile"] = profile

    result = verify_fixture_case(case, ROOT).to_dict()
    verification_id = result["id"]
    data_store.verifications[verification_id] = result
    data_store.verification_context[verification_id] = {
        "fixture_id": case["id"],
        "fixture": case["fixture"],
        "candidate": case["candidate"],
        "profile": case["profile"],
    }
    return {"verification": result}


def get_evidence(verification_id: str, data_store: InMemoryStore = store) -> dict[str, Any]:
    verification = _verification_or_404(verification_id, data_store)
    return {
        "verification_id": verification_id,
        "candidate_id": verification["candidate_id"],
        "profile_id": verification["profile_id"],
        "status": verification["status"],
        "student_facing_status": verification["student_facing_status"],
        "source": {
            "url": verification["source_url"],
            "official": verification["source_official"],
            "type": verification["source_type"],
            "reason": verification["source_reason"],
        },
        "verdict_reason": verification["verdict_reason"],
        "matched_rules": verification["matched_rules"],
        "blocking_rules": verification["blocking_rules"],
        "unclear_rules": verification["unclear_rules"],
        "missing_required_rules": verification["missing_required_rules"],
        "security_flags": verification["security_flags"],
    }


def draft_email(request: dict[str, Any], data_store: InMemoryStore = store) -> dict[str, Any]:
    verification_id = str(request.get("verification_id", "")).strip()
    if not verification_id:
        raise ApiError(400, "verification_id is required.")

    verification = _verification_or_404(verification_id, data_store)
    if verification["status"] != "unclear":
        raise ApiError(400, "Clarification email drafts are only available for unclear cases.")

    context = data_store.verification_context.get(verification_id, {})
    candidate = context.get("candidate", {})
    profile = context.get("profile", {})
    student_name = str(request.get("student_name") or "Prospective international student")
    recipient = str(request.get("recipient") or "Scholarship Office")
    unclear_types = [
        rule.get("rule_type", "eligibility rule")
        for rule in verification.get("unclear_rules", [])
    ] + list(verification.get("missing_required_rules", []))
    unclear_summary = ", ".join(sorted(set(unclear_types))) or "eligibility requirements"

    subject = f"Clarification request: {candidate.get('name', verification['candidate_id'])}"
    body = (
        f"Dear {recipient},\n\n"
        f"My name is {student_name}. I am reviewing "
        f"{candidate.get('name', 'this scholarship')} for {profile.get('degree_level', 'my intended degree')} "
        f"study in {profile.get('field', 'my field')}.\n\n"
        "Could you please clarify the following eligibility details for an international applicant "
        f"from {profile.get('nationality', 'my country')}: {unclear_summary}?\n\n"
        "I am not asking you to assess my full application by email. I only want to confirm the "
        "official eligibility rules before applying.\n\n"
        "Kind regards,\n"
        f"{student_name}"
    )

    return {
        "verification_id": verification_id,
        "status": "drafted",
        "send_allowed": False,
        "subject": subject,
        "body": body,
    }


def save_result(request: dict[str, Any], data_store: InMemoryStore = store) -> dict[str, Any]:
    verification_id = str(request.get("verification_id", "")).strip()
    if not verification_id:
        raise ApiError(400, "verification_id is required.")
    verification = _verification_or_404(verification_id, data_store)
    profile_id = str(request.get("profile_id") or verification["profile_id"])
    saved_result = {
        "id": f"saved_{uuid4().hex[:8]}",
        "profile_id": profile_id,
        "verification_id": verification_id,
        "candidate_id": verification["candidate_id"],
        "status": verification["status"],
        "student_facing_status": verification["student_facing_status"],
        "notes": request.get("notes", ""),
        "saved_at": utc_now_iso(),
    }
    data_store.saved_results.setdefault(profile_id, []).append(saved_result)
    return {"saved_result": saved_result}


def get_saved_results(profile_id: str, data_store: InMemoryStore = store) -> dict[str, Any]:
    if profile_id not in data_store.profiles:
        raise ApiError(404, f"Profile not found: {profile_id}.")
    results = data_store.saved_results.get(profile_id, [])
    return {"profile_id": profile_id, "count": len(results), "saved_results": results}


def get_audit(verification_id: str, data_store: InMemoryStore = store) -> dict[str, Any]:
    verification = _verification_or_404(verification_id, data_store)
    return {
        "verification_id": verification_id,
        "audit_log": verification["audit_log"],
    }

