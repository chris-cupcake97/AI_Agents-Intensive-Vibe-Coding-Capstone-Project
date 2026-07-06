"""Deterministic fixture rule extraction and profile matching."""

from __future__ import annotations

import re
from dataclasses import replace

from .models import EligibilityRule, StudentProfile


EU_EEA_COUNTRIES = {
    "austria",
    "belgium",
    "bulgaria",
    "croatia",
    "cyprus",
    "czech republic",
    "denmark",
    "estonia",
    "finland",
    "france",
    "germany",
    "greece",
    "hungary",
    "iceland",
    "ireland",
    "italy",
    "latvia",
    "liechtenstein",
    "lithuania",
    "luxembourg",
    "malta",
    "netherlands",
    "norway",
    "poland",
    "portugal",
    "romania",
    "slovakia",
    "slovenia",
    "spain",
    "sweden",
}


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().replace("-", " ").split())


def _rule_text(rule: EligibilityRule) -> str:
    return _norm(f"{rule.requirement_text} {rule.evidence_text}")


def _downgrade(rule: EligibilityRule, status: str, note: str) -> EligibilityRule:
    return replace(
        rule,
        status=status,  # type: ignore[arg-type]
        requirement_text=f"{rule.requirement_text} Profile guard: {note}",
    )


def _mentions_any(text: str, values: tuple[str, ...]) -> bool:
    return any(value in text for value in values)


def _guard_degree(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    degree = _norm(profile.degree_level)
    wants_masters = "master" in degree
    wants_phd = "phd" in degree or "doctor" in degree
    wants_bachelors = "bachelor" in degree or "undergraduate" in degree
    mentions_masters = _mentions_any(text, ("master", "msc", "postgraduate taught"))
    mentions_phd = _mentions_any(text, ("phd", "doctoral", "doctorate"))
    mentions_bachelors = _mentions_any(text, ("bachelor", "undergraduate"))

    if wants_masters and (mentions_phd or mentions_bachelors) and not mentions_masters:
        return _downgrade(rule, "blocking", "degree level evidence does not support Master's study.")
    if wants_phd and (mentions_masters or mentions_bachelors) and not mentions_phd:
        return _downgrade(rule, "blocking", "degree level evidence does not support PhD study.")
    if wants_bachelors and (mentions_masters or mentions_phd) and not mentions_bachelors:
        return _downgrade(rule, "blocking", "degree level evidence does not support undergraduate study.")
    return rule


def _guard_nationality(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    nationality = _norm(profile.nationality)
    if not nationality:
        return _downgrade(rule, "unclear", "student nationality is missing.")
    if "any non uk country" in text and nationality in {"uk", "united kingdom"}:
        return _downgrade(rule, "blocking", "nationality evidence excludes UK applicants.")
    if "non eu/eea" in text or "non eu eea" in text:
        if nationality in EU_EEA_COUNTRIES:
            return _downgrade(rule, "blocking", "nationality evidence is for non-EU/EEA applicants.")
        return rule
    if "all nationalit" in text or "all countries" in text or "any country" in text:
        return rule
    explicit_countries = ("sri lanka", "india", "bangladesh", "nepal", "pakistan")
    mentioned = [country for country in explicit_countries if country in text]
    if mentioned and nationality not in mentioned:
        return _downgrade(rule, "unclear", "official evidence does not mention this nationality.")
    return rule


def _guard_residence(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    residence = _norm(profile.residence)
    if not residence:
        return _downgrade(rule, "unclear", "student residence is missing.")
    if "outside the uk" in text and residence in {"uk", "united kingdom"}:
        return _downgrade(rule, "blocking", "residence evidence is for applicants outside the UK.")
    return rule


def _guard_fee_status(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    fee_status = _norm(profile.fee_status)
    if not fee_status or fee_status == "unknown":
        return _downgrade(rule, "unclear", "fee status is missing or unknown.")
    if fee_status == "international" and _mentions_any(text, ("home fee", "home student")) and not _mentions_any(
        text,
        ("international", "overseas", "non eu", "fee liable"),
    ):
        return _downgrade(rule, "blocking", "fee status evidence supports home-fee applicants only.")
    if fee_status == "home" and _mentions_any(text, ("international", "overseas", "non eu", "fee liable")):
        return _downgrade(rule, "blocking", "fee status evidence supports international applicants.")
    return rule


def _guard_field(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    field = _norm(profile.field)
    if not field:
        return _downgrade(rule, "unclear", "field of study is missing.")
    if "business" in field and _mentions_any(
        text,
        ("artificial intelligence", " ai ", "computer science", "data science", "technology", "digital"),
    ):
        return _downgrade(rule, "unclear", "field evidence does not clearly support Business study.")
    if "artificial intelligence" in field or field == "ai":
        if _mentions_any(text, ("artificial intelligence", " ai ", "computer science", "data science", "technology", "digital")):
            return rule
    return rule


def _max_percent(text: str) -> int | None:
    values = [int(match) for match in re.findall(r"\b(\d{1,3})\s*(?:percent|%)\b", text)]
    values = [value for value in values if 0 <= value <= 100]
    return max(values) if values else None


def _guard_funding(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    need = profile.funding_need_percent
    if need <= 0:
        return rule
    if _mentions_any(text, ("full tuition", "full funding", "100 percent", "100%")):
        return rule
    percent = _max_percent(text)
    if percent is not None and percent < need:
        return _downgrade(rule, "blocking", "funding evidence is below the student's stated need.")
    if percent is None and need >= 100:
        return _downgrade(rule, "unclear", "funding evidence does not prove full funding.")
    return rule


def _guard_intake(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    text = _rule_text(rule)
    intake = _norm(profile.intake)
    if not intake:
        return _downgrade(rule, "unclear", "intake is missing.")
    cycle_matches = re.findall(r"\b20\d{2}/\d{2}\b", text)
    if cycle_matches and intake not in cycle_matches:
        return _downgrade(rule, "unclear", "cycle evidence does not match the student's intended intake.")
    return rule


def _apply_profile_guard(profile: StudentProfile, rule: EligibilityRule) -> EligibilityRule:
    if rule.status != "matched" or not rule.has_evidence:
        return rule
    if rule.rule_type == "degree_level":
        return _guard_degree(profile, rule)
    if rule.rule_type == "nationality":
        return _guard_nationality(profile, rule)
    if rule.rule_type == "residence":
        return _guard_residence(profile, rule)
    if rule.rule_type == "fee_status":
        return _guard_fee_status(profile, rule)
    if rule.rule_type == "field":
        return _guard_field(profile, rule)
    if rule.rule_type == "funding_amount":
        return _guard_funding(profile, rule)
    if rule.rule_type in {"current_cycle", "deadline"}:
        return _guard_intake(profile, rule)
    return rule


def extract_rules(
    page_text: str,
    source_url: str,
    fixture_rules: list[dict] | None = None,
) -> list[EligibilityRule]:
    """Extract eligibility rules.

    The MVP eval harness uses curated JSON fixtures, so this function accepts
    fixture rules directly. Later agent/tool implementations can replace this
    with model-assisted extraction while keeping the same output shape.
    """

    del page_text
    return [
        EligibilityRule.from_mapping(rule_data, source_url=source_url)
        for rule_data in fixture_rules or []
    ]


def match_profile(
    profile: StudentProfile,
    rules: list[EligibilityRule],
) -> tuple[list[EligibilityRule], list[EligibilityRule], list[EligibilityRule]]:
    """Partition extracted rules into matched, blocking, and unclear buckets."""

    matched: list[EligibilityRule] = []
    blocking: list[EligibilityRule] = []
    unclear: list[EligibilityRule] = []

    for rule in rules:
        rule = _apply_profile_guard(profile, rule)
        if rule.status == "blocking":
            blocking.append(rule)
        elif rule.status == "matched" and rule.has_evidence:
            matched.append(rule)
        else:
            unclear.append(rule)

    return matched, blocking, unclear

