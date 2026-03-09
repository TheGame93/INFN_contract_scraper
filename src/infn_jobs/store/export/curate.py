"""Rebuild calls_curated from the employment-like filter on calls_raw."""

import sqlite3

# In v1, the scraper only fetches these 5 employment-like source tipos, so
# calls_curated will be identical to calls_raw in practice. The curated layer
# is infrastructure for v2, which may add new source types (e.g., prizes,
# awards) that this filter would then exclude.
_EMPLOYMENT_TIPOS = (
    "Borsa",
    "Incarico di ricerca",
    "Incarico Post-Doc",
    "Contratto di ricerca",
    "Assegno di ricerca",
)


def rebuild_curated(conn: sqlite3.Connection) -> None:
    """Rebuild calls_curated from the employment-like filter.

    position_rows_curated is a VIEW and updates automatically.
    """
    placeholders = ",".join("?" * len(_EMPLOYMENT_TIPOS))
    conn.execute("DELETE FROM calls_curated")
    conn.execute(
        f"INSERT INTO calls_curated SELECT * FROM calls_raw WHERE source_tipo IN ({placeholders})",
        _EMPLOYMENT_TIPOS,
    )
    conn.commit()
