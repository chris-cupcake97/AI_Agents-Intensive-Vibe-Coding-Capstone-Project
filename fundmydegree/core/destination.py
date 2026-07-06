"""Destination matching helpers for fixture-mode scholarship fit checks."""

from __future__ import annotations


GLOBAL_DESTINATIONS = {
    "global",
    "worldwide",
    "international",
    "multiple countries",
    "any country",
    "all countries",
}

UNKNOWN_DESTINATIONS = {"", "unknown", "not specified", "tbc", "n/a", "na"}

REGION_COUNTRIES: dict[str, set[str]] = {
    "europe": {
        "finland",
        "germany",
        "sweden",
        "united kingdom",
        "uk",
    }
}


def normalize_destination(value: str) -> str:
    return " ".join(value.strip().lower().replace("-", " ").split())


def destination_is_missing(country: str) -> bool:
    return normalize_destination(country) in UNKNOWN_DESTINATIONS


def target_regions_summary(target_regions: list[str]) -> str:
    return ", ".join(region for region in target_regions if region.strip()) or "not set"


def destination_supported(country: str, target_regions: list[str]) -> bool:
    """Return whether a candidate country fits the student's selected destinations."""

    country_norm = normalize_destination(country)
    if not target_regions:
        return True
    if destination_is_missing(country):
        return False
    if country_norm in GLOBAL_DESTINATIONS:
        return True

    for region in target_regions:
        region_norm = normalize_destination(region)
        if not region_norm:
            continue
        if region_norm == country_norm:
            return True
        if country_norm in REGION_COUNTRIES.get(region_norm, set()):
            return True

    return False
