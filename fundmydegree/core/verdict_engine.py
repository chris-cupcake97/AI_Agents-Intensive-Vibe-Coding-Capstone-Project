"""Conservative verdict generation for FundMyDegree."""

from __future__ import annotations

from .models import (
    REQUIRED_RULE_TYPES,
    AuditEvent,
    EligibilityRule,
    ScholarshipCandidate,
    SourceClassification,
    StudentProfile,
    VerificationResult,
    student_label_for,
    utc_now_iso,
)
from .destination import (
    destination_is_missing,
    destination_supported,
    target_regions_summary,
)


def _matched_required_rule_types(matched_rules: list[EligibilityRule]) -> set[str]:
    return {
        rule.rule_type
        for rule in matched_rules
        if rule.rule_type in REQUIRED_RULE_TYPES and rule.has_evidence
    }


def missing_required_rules(matched_rules: list[EligibilityRule]) -> list[str]:
    matched_types = _matched_required_rule_types(matched_rules)
    return [rule_type for rule_type in REQUIRED_RULE_TYPES if rule_type not in matched_types]


def generate_verdict(
    profile: StudentProfile,
    candidate: ScholarshipCandidate,
    source: SourceClassification,
    matched_rules: list[EligibilityRule],
    blocking_rules: list[EligibilityRule],
    unclear_rules: list[EligibilityRule],
    security_flags: list[str],
    audit_log: list[AuditEvent],
) -> VerificationResult:
    """Generate a conservative verdict with hard stops before `eligible`."""

    matched_rules = list(matched_rules)
    blocking_rules = list(blocking_rules)
    unclear_rules = list(unclear_rules)

    if profile.target_regions:
        target_summary = target_regions_summary(profile.target_regions)
        evidence_source = source.url or candidate.candidate_url
        if destination_is_missing(candidate.country):
            unclear_rules.append(
                EligibilityRule(
                    rule_type="study_destination",
                    requirement_text=(
                        "Scholarship destination must be clear before it can be treated "
                        f"as a fit for: {target_summary}."
                    ),
                    evidence_text="",
                    status="unclear",
                    source_url=evidence_source,
                    confidence=0.0,
                )
            )
        elif not destination_supported(candidate.country, profile.target_regions):
            blocking_rules.append(
                EligibilityRule(
                    rule_type="study_destination",
                    requirement_text=(
                        "Scholarship destination must match the student's selected "
                        f"study destination: {target_summary}."
                    ),
                    evidence_text=(
                        f"Candidate country is {candidate.country}; selected "
                        f"destination is {target_summary}."
                    ),
                    status="blocking",
                    source_url=evidence_source,
                    confidence=1.0,
                )
            )

    missing_rules = missing_required_rules(matched_rules)

    if not source.url or not source.is_official:
        status = "unverified"
        reason = "No acceptable official source proves the scholarship rules."
    elif blocking_rules:
        status = "not_eligible"
        if any(rule.rule_type == "study_destination" for rule in blocking_rules):
            reason = "The scholarship is outside the student's selected study destinations."
        else:
            reason = "An official source contains at least one blocking eligibility rule."
    elif security_flags:
        status = "unclear"
        reason = "Official source was found, but the page contains prompt-injection-like text."
    elif unclear_rules or missing_rules:
        status = "unclear"
        reason = "Official evidence is incomplete for required eligibility rules."
    else:
        status = "eligible"
        reason = "Official source evidence supports every required eligibility rule."

    return VerificationResult(
        id=f"verification_{candidate.id}_{profile.id}",
        candidate_id=candidate.id,
        profile_id=profile.id,
        status=status,  # type: ignore[arg-type]
        student_facing_status=student_label_for(status),
        source_url=source.url,
        source_official=source.is_official,
        source_type=source.source_type,
        source_reason=source.reason,
        last_checked=utc_now_iso(),
        matched_rules=matched_rules,
        blocking_rules=blocking_rules,
        unclear_rules=unclear_rules,
        missing_required_rules=missing_rules,
        verdict_reason=reason,
        security_flags=security_flags,
        audit_log=audit_log,
    )
