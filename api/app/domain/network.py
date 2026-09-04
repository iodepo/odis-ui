from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class NetworkNodeStatus(BaseModel):
    id: str = Field(description="ODISCat document id / slug")
    name: str = Field(description="Human-readable node name")
    url: str | None = Field(default=None, description="Node catalogue or sitemap URL")
    errors: list[str] = Field(
        default_factory=list,
        description="Truncated summoner error messages for display",
    )


class NetworkStatusResponse(BaseModel):
    updated_at: str = Field(description="ISO-8601 timestamp when this status was computed")
    total_nodes: int
    total_error_nodes: int
    unresponsive_count: int
    parsing_error_count: int
    summoner_error_count: int
    unresponsive: list[NetworkNodeStatus] = Field(default_factory=list)
    parsing_errors: list[NetworkNodeStatus] = Field(default_factory=list)


ERROR_PREVIEW_LIMIT = 5

NETWORK_STATUS_SOURCE_FIELDS = [
    "name",
    "url",
    "summoner_errors",
    "summoner_pages_seen",
    "summoner_messages",
]


def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return default


def _as_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _as_message_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        messages: list[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                messages.append(" ".join(item.strip().splitlines()))
            elif item is not None:
                text = str(item).strip()
                if text:
                    messages.append(" ".join(text.splitlines()))
        return messages
    text = str(value).strip()
    return [text] if text else []


def truncate_errors(messages: list[str], *, limit: int = ERROR_PREVIEW_LIMIT) -> list[str]:
    if len(messages) <= limit:
        return messages
    shown = messages[:limit]
    remaining = len(messages) - limit
    return [*shown, f"… and {remaining} more"]


def node_from_hit(hit: dict[str, Any]) -> NetworkNodeStatus | None:
    """Build a display node from an ES hit that has `_source` (or None if unusable)."""
    source = hit.get("_source")
    if not isinstance(source, dict):
        return None
    doc_id = str(hit.get("_id") or "")
    name = _as_str(source.get("name")) or doc_id or "unknown"
    url = _as_str(source.get("url"))
    errors = truncate_errors(_as_message_list(source.get("summoner_messages")))
    return NetworkNodeStatus(id=doc_id or name, name=name, url=url, errors=errors)


def classify_odiscat_hits(hits: list[dict[str, Any]]) -> NetworkStatusResponse:
    """Classify odiscat hits using the same rules as adamml/odis_dashboard."""
    unresponsive: list[NetworkNodeStatus] = []
    parsing_errors: list[NetworkNodeStatus] = []
    summoner_error_count = 0

    for hit in hits:
        if "_source" not in hit or not isinstance(hit.get("_source"), dict):
            summoner_error_count += 1
            continue

        source = hit["_source"]
        summoner_errors = _as_int(source.get("summoner_errors"))
        if summoner_errors <= 0:
            continue

        node = node_from_hit(hit)
        if node is None:
            summoner_error_count += 1
            continue

        pages_seen = _as_int(source.get("summoner_pages_seen"))
        if pages_seen == 0:
            unresponsive.append(node)
        else:
            parsing_errors.append(node)

    total_nodes = len(hits)
    unresponsive_count = len(unresponsive)
    parsing_error_count = len(parsing_errors)
    total_error_nodes = unresponsive_count + parsing_error_count + summoner_error_count

    return NetworkStatusResponse(
        updated_at=datetime.now(timezone.utc).isoformat(),
        total_nodes=total_nodes,
        total_error_nodes=total_error_nodes,
        unresponsive_count=unresponsive_count,
        parsing_error_count=parsing_error_count,
        summoner_error_count=summoner_error_count,
        unresponsive=unresponsive,
        parsing_errors=parsing_errors,
    )
