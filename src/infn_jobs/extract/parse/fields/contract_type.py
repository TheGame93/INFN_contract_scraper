"""Extract contract type and subtype fields from a PDF segment."""

from __future__ import annotations

import re

from infn_jobs.extract.parse.normalize.subtypes import normalize_subtype

# Ordered from most specific to least specific
_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"INCARICO\s+POST.?DOC", re.IGNORECASE), "Incarico Post-Doc"),
    (re.compile(r"CONTRATTO\s+DI\s+RICERCA", re.IGNORECASE), "Contratto di ricerca"),
    (re.compile(r"INCARICO\s+DI\s+RICERCA", re.IGNORECASE), "Incarico di ricerca"),
    (re.compile(r"ASSEGNO\s+DI\s+RICERCA", re.IGNORECASE), "Assegno di ricerca"),
    (re.compile(r"BORSA(?:\s+DI\s+STUDIO)?", re.IGNORECASE), "Borsa di studio"),
]

_SUBTYPE_RE = re.compile(r"(Tipo\s+[AB]|Fascia\s+II|Fascia\s+2)", re.IGNORECASE)


def extract_contract_type(segment: str, anno: int | None) -> dict:
    """Extract contract type, type_raw, and subtype fields from a segment.

    Returns dict with keys: contract_type, contract_type_raw, contract_type_evidence,
    contract_subtype, contract_subtype_raw, contract_subtype_evidence.
    All values are str | None.
    """
    result: dict = {
        "contract_type": None,
        "contract_type_raw": None,
        "contract_type_evidence": None,
        "contract_subtype": None,
        "contract_subtype_raw": None,
        "contract_subtype_evidence": None,
    }

    for line in segment.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Match contract type
        if result["contract_type"] is None:
            for pattern, canonical in _TYPE_PATTERNS:
                m = pattern.search(stripped)
                if m:
                    result["contract_type"] = canonical
                    result["contract_type_raw"] = m.group(0)
                    result["contract_type_evidence"] = stripped
                    break

        # Match subtype
        if result["contract_subtype_raw"] is None:
            m = _SUBTYPE_RE.search(stripped)
            if m:
                raw = m.group(1)
                result["contract_subtype_raw"] = raw
                result["contract_subtype"] = normalize_subtype(raw, anno)
                result["contract_subtype_evidence"] = stripped

        if result["contract_type"] is not None and result["contract_subtype_raw"] is not None:
            break

    return result
