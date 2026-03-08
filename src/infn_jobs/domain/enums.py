"""Enums for the INFN jobs domain layer."""

from __future__ import annotations

from enum import StrEnum


class ListingStatus(StrEnum):
    """Whether a job listing is currently active or has expired."""

    ACTIVE = "active"
    EXPIRED = "expired"


class ContractType(StrEnum):
    """The five INFN job source tipos, stored verbatim as they appear on the site."""

    BORSA = "Borsa"
    INCARICO_RICERCA = "Incarico di ricerca"
    INCARICO_POSTDOC = "Incarico Post-Doc"
    CONTRATTO_RICERCA = "Contratto di ricerca"
    ASSEGNO_RICERCA = "Assegno di ricerca"


class ParseConfidence(StrEnum):
    """Parser confidence in the extracted field values for a position row."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TextQuality(StrEnum):
    """Classification of the PDF text source quality."""

    DIGITAL = "digital"
    OCR_CLEAN = "ocr_clean"
    OCR_DEGRADED = "ocr_degraded"
    NO_TEXT = "no_text"
