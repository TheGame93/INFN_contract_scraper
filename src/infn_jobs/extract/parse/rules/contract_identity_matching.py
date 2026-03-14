"""Internal matching helpers for contract identity rule resolution."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.contracts.profile import ContractProfile
from infn_jobs.extract.parse.rules.text_windows import iter_adjacent_line_windows

_TYPE_PRECEDENCE: dict[str, int] = {
    "Incarico Post-Doc": 10,
    "Contratto di ricerca": 20,
    "Incarico di ricerca": 30,
    "Assegno di ricerca": 40,
    "Borsa di studio": 50,
}
_PRIMARY_TYPE_RULE_ID = "contract_identity.00.first_match.type"
_FALLBACK_TYPE_RULE_ID = "contract_identity.90.predicted_fallback.type"


def _slug(value: str) -> str:
    """Return a deterministic slug used in contract-identity rule ids."""
    return value.lower().replace(" ", "-").replace("/", "-").replace(".", "")


def _profile_precedence(profile: ContractProfile) -> int:
    """Return deterministic precedence for same-line contract matches."""
    return _TYPE_PRECEDENCE.get(profile.canonical_name, 80)


def _first_match(
    segment_text: str,
    pattern_texts: tuple[str, ...],
    *,
    max_window_lines: int = 1,
) -> tuple[str | None, str | None]:
    """Return first `(raw_match, evidence_line)` for patterns, else `(None, None)`."""
    patterns = tuple(re.compile(pattern, re.IGNORECASE) for pattern in pattern_texts)
    for window in iter_adjacent_line_windows(segment_text, max_lines=max_window_lines):
        for pattern in patterns:
            match = pattern.search(window.text)
            if match:
                return match.group(0).strip(), window.evidence
    return None, None


def _select_primary_contract_match(
    segment_text: str,
    profiles: tuple[ContractProfile, ...],
) -> tuple[str, str, str] | None:
    """Return first line contract match as `(canonical, raw, evidence)`."""
    for line in segment_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        line_candidates: list[tuple[int, str, str]] = []
        for profile in profiles:
            raw_match, _ = _first_match(stripped, profile.contract_type_patterns)
            if raw_match is None:
                continue
            line_candidates.append(
                (_profile_precedence(profile), profile.canonical_name, raw_match)
            )
        if line_candidates:
            _, canonical, raw = min(line_candidates, key=lambda item: (item[0], item[1]))
            return canonical, raw, stripped
    return None
