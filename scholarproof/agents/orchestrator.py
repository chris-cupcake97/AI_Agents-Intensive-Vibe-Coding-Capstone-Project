"""Root Orchestrator Agent for ScholarProof fixture-mode workflows."""

from __future__ import annotations

from typing import Any

from scholarproof.api import services

from .finder import FinderAgent
from .verifier import VerifierAgent


class RootOrchestratorAgent:
    """Coordinates discovery and verification without producing its own verdicts."""

    name = "Root Orchestrator Agent"

    def __init__(
        self,
        finder: FinderAgent | None = None,
        verifier: VerifierAgent | None = None,
    ) -> None:
        self.finder = finder or FinderAgent()
        self.verifier = verifier or VerifierAgent()

    def run(
        self,
        *,
        profile: dict[str, Any],
        search_query: str = "",
        max_candidates: int = 3,
    ) -> dict[str, Any]:
        profile_result = services.create_profile(profile)
        profile_data = profile_result["profile"]

        finder_result = self.finder.search(
            profile_id=profile_data["id"],
            query=search_query,
            limit=max_candidates,
        )

        verifications: list[dict[str, Any]] = []
        grouped_results: dict[str, list[dict[str, Any]]] = {
            "eligible": [],
            "unclear": [],
            "not_eligible": [],
            "unverified": [],
        }

        for candidate in finder_result["candidates"]:
            verifier_result = self.verifier.verify(
                candidate=candidate,
                profile=profile_data,
                fixture_id=candidate.get("fixture_id"),
            )
            verification = verifier_result["verification"]
            verifications.append(verifier_result)
            grouped_results[verification["status"]].append(
                {
                    "candidate": candidate,
                    "verification": verification,
                    "verdict_source": self.verifier.name,
                }
            )

        return {
            "agent": self.name,
            "mode": "fixture",
            "profile": profile_data,
            "query": search_query,
            "finder_result": finder_result,
            "verifications": verifications,
            "grouped_results": grouped_results,
            "verdict_policy": "verdicts are produced only by the Verifier Agent",
        }

