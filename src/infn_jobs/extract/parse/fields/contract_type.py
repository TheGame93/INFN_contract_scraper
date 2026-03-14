"""Extract contract type and subtype fields from a PDF segment."""

from __future__ import annotations

from infn_jobs.extract.parse.rules.contract_identity import resolve_contract_identity


def extract_contract_type(segment: str, anno: int | None) -> dict:
    """Extract contract type, type_raw, and subtype fields from a segment.

    Returns dict with keys: contract_type, contract_type_raw, contract_type_evidence,
    contract_subtype, contract_subtype_raw, contract_subtype_evidence.
    All values are str | None.
    """
    resolved = resolve_contract_identity(segment_text=segment, anno=anno)
    return {
        "contract_type": resolved.contract_type,
        "contract_type_raw": resolved.contract_type_raw,
        "contract_type_evidence": resolved.contract_type_evidence,
        "contract_subtype": resolved.contract_subtype,
        "contract_subtype_raw": resolved.contract_subtype_raw,
        "contract_subtype_evidence": resolved.contract_subtype_evidence,
    }
