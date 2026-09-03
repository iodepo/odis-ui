from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from elasticsearch import AsyncElasticsearch


@dataclass(frozen=True, slots=True)
class OdiscatEntry:
    name: str
    url: str | None = None
    domain: str | None = None
    last_indexed: str | None = None


class OdiscatNames:
    """Lazy cache of datasource metadata from the odiscat index (keyed by slug/_id)."""

    # Field names in the ODISCat mapping have changed over time; fetch a small
    # set and take the first value we can interpret as a timestamp.
    _FIELDS = [
        "name",
        "url",
        "domain",
        # Common timestamps.
        "dateModified",
        "lastIndexed",
        "last_indexed",
        "indexedAt",
        "indexed_at",
    ]

    def __init__(self) -> None:
        self._entries: dict[str, OdiscatEntry] = {}
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    async def load(self, client: AsyncElasticsearch, index: str) -> None:
        if self._loaded:
            return

        response = await client.search(
            index=index,
            body={
                "size": 200,
                "query": {"match_all": {}},
                "_source": self._FIELDS,
            },
        )
        payload = response.body if hasattr(response, "body") else response
        for hit in payload.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            name = src.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            url = src.get("url") if isinstance(src.get("url"), str) else None
            domain_val = src.get("domain") if isinstance(src.get("domain"), str) else None
            # Prefer explicit "last indexed" fields, fall back to "dateModified".
            raw_last_indexed = (
                src.get("last_indexed")
                or src.get("lastIndexed")
                or src.get("indexed_at")
                or src.get("indexedAt")
                or src.get("dateModified")
            )

            last_indexed = self._coerce_last_indexed(raw_last_indexed)
            self._entries[hit["_id"]] = OdiscatEntry(
                name=name.strip(),
                url=url.strip() if url else None,
                domain=domain_val.strip() if domain_val else None,
                last_indexed=last_indexed,
            )

        self._loaded = True

    def get(self, source_id: str) -> OdiscatEntry | None:
        return self._entries.get(source_id)

    def get_name(self, source_id: str) -> str | None:
        entry = self._entries.get(source_id)
        return entry.name if entry else None

    def as_dict(self) -> dict[str, str]:
        return {k: v.name for k, v in self._entries.items()}

    @staticmethod
    def _coerce_last_indexed(value: object) -> str | None:
        """
        Best-effort conversion of an arbitrary timestamp representation to a string.

        - If we receive an epoch number (seconds or millis), convert to ISO-8601.
        - If we receive a string, keep it (trimmed). The frontend formats it and
          will fall back to displaying the raw string when parsing fails.
        """
        if value is None:
            return None

        if isinstance(value, (int, float)):
            num = int(value)
        elif isinstance(value, str):
            v = value.strip()
            if not v:
                return None
            # If it looks numeric, treat it as an epoch timestamp.
            if v.isdigit():
                num = int(v)
            else:
                return v
        else:
            return None

        # Heuristic: 13-digit-ish is milliseconds, otherwise seconds.
        ms = num if num > 1_000_000_000_000 else num * 1000
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
