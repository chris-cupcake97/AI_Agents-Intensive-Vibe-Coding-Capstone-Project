"""Clarification Email Skill wrapper for unclear verification results."""

from __future__ import annotations

from typing import Any

from scholarproof.api import services


class ClarificationEmailSkillWrapper:
    """Drafts clarification emails only for unclear cases and never sends them."""

    name = "Clarification Email Skill"

    def draft(
        self,
        verification: dict[str, Any],
        *,
        student_name: str | None = None,
        recipient: str | None = None,
    ) -> dict[str, Any]:
        status = verification.get("status")
        if status != "unclear":
            return {
                "ok": False,
                "agent": self.name,
                "status": "rejected",
                "reason": "Clarification email drafts are only available for unclear cases.",
                "send_allowed": False,
            }

        try:
            draft = services.draft_email(
                {
                    "verification_id": verification["id"],
                    "student_name": student_name,
                    "recipient": recipient,
                }
            )
        except services.ApiError as exc:
            return {
                "ok": False,
                "agent": self.name,
                "status": "rejected",
                "reason": exc.message,
                "send_allowed": False,
            }

        draft["send_allowed"] = False
        return {
            "ok": True,
            "agent": self.name,
            "status": "drafted",
            "draft": draft,
        }

