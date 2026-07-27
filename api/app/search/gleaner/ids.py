"""ODIS summoned corpus on the Gleaner Elasticsearch cluster (single `odis` index)."""

from __future__ import annotations

from urllib.parse import quote, unquote

# Legacy short harvest codes (kept for callers that still check membership).
GLEANER_SOURCE_IDS: frozenset[str] = frozenset({"obps", "medin", "obis", "oe"})

# Default search surface: federated `odis` index only (ignore per-source gleaner-* indices).
DEFAULT_INDICES: tuple[str, ...] = ("odis",)

# Record ids keep the historical `gleaner:` namespace so deep links keep routing correctly.
RECORD_ID_PREFIX = "gleaner:"


def encode_record_id(source: str, doc_id: str) -> str:
    """Namespace summoned ids so composite routing can find them later."""
    return f"{RECORD_ID_PREFIX}{source}:{quote(doc_id, safe='')}"


def decode_record_id(record_id: str) -> tuple[str, str] | None:
    if not record_id.startswith(RECORD_ID_PREFIX):
        return None
    parts = record_id.split(":", 2)
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return parts[1], unquote(parts[2])


def is_gleaner_source(source_id: str) -> bool:
    return source_id in GLEANER_SOURCE_IDS
