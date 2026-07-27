"""Map Gleaner summoned documents to domain SearchItem models."""

from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any

from app.domain.enums import PRIMARY_RECORD_TYPES, SortOrder
from app.domain.search import (
    FacetBucket,
    SearchFacets,
    SearchItem,
    SearchQuery,
    SearchResponse,
    SourceFacetBucket,
    SourceRef,
)
from app.search.elasticsearch.mappings import raw_types_for_filter
from app.search.elasticsearch.spatial import extract_spatial_extent
from app.search.gleaner.ids import encode_record_id

# Gleaner also indexes Course; keep ODIS PRIMARY_RECORD_TYPES unchanged.
GLEANER_PRIMARY_TYPES: tuple[str, ...] = (*PRIMARY_RECORD_TYPES, "course")

SEARCH_SOURCE_FIELDS = [
    "id",
    "name",
    "description",
    "keywords",
    "type",
    "url",
    "source",
    "source_url",
    "jsonld",
]


def _gleaner_type_match_values(item: str) -> list[str]:
    """Map UI / facet type ids to values stored on the Gleaner `type` keyword field."""
    if item != item.lower() or item.startswith("schema:") or item.startswith("sc:"):
        bare = item.removeprefix("schema:").removeprefix("sc:")
        candidates = [item, bare, f"schema:{bare}"]
        return list(dict.fromkeys(candidates))

    values: list[str] = []
    for raw in raw_types_for_filter([item.lower()]):
        bare = raw.removeprefix("schema:")
        values.append(bare)
        if raw.startswith("schema:"):
            values.append(raw)
        elif bare != raw:
            values.append(f"schema:{bare}")
    return list(dict.fromkeys(values))


def _type_values_for_filter(types: list[str]) -> list[str]:
    """Gleaner stores PascalCase schema.org types on keyword field `type`."""
    values: list[str] = []
    seen: set[str] = set()
    for item in types:
        for candidate in _gleaner_type_match_values(item):
            if candidate not in seen:
                seen.add(candidate)
                values.append(candidate)
    return values


def _base_filters(query: SearchQuery) -> list[dict[str, Any]]:
    if query.include_graph_fragments:
        return []
    return [
        {"terms": {"type": _type_values_for_filter(list(GLEANER_PRIMARY_TYPES))}},
    ]


def _type_facet_filters(query: SearchQuery) -> list[dict[str, Any]]:
    filters = _base_filters(query)
    if query.sources:
        filters.append({"terms": {"source": query.sources}})
    return filters


def _source_facet_filters(query: SearchQuery) -> list[dict[str, Any]]:
    filters = _base_filters(query)
    if query.types:
        filters.append({"terms": {"type": _type_values_for_filter(query.types)}})
    return filters


def _user_post_filter(query: SearchQuery) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if query.types:
        clauses.append({"terms": {"type": _type_values_for_filter(query.types)}})
    if query.sources:
        clauses.append({"terms": {"source": query.sources}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"bool": {"filter": clauses}}


def _filter_agg(filters: list[dict[str, Any]], field: str, size: int) -> dict[str, Any]:
    return {
        "filter": {"bool": {"filter": filters}},
        "aggs": {"buckets": {"terms": {"field": field, "size": size}}},
    }


def build_search_body(query: SearchQuery) -> dict[str, Any]:
    filters = _base_filters(query)
    must: list[dict[str, Any]] = []
    if query.q:
        must.append(
            {
                "multi_match": {
                    "query": query.q,
                    "fields": ["name^3", "description", "keywords^2"],
                    "type": "best_fields",
                }
            }
        )

    body: dict[str, Any] = {
        "query": {
            "bool": {
                "filter": filters,
                **({"must": must} if must else {}),
            }
        },
        "from": (query.page - 1) * query.size,
        "size": query.size,
        "_source": SEARCH_SOURCE_FIELDS,
        "aggs": {
            "types": _filter_agg(_type_facet_filters(query), "type", 100),
            "sources": _filter_agg(_source_facet_filters(query), "source", 50),
        },
        "track_scores": True,
        # Exact total (default ES cap is 10_000 with relation=gte). Cheap on the `odis` corpus.
        "track_total_hits": True,
    }

    post_filter = _user_post_filter(query)
    if post_filter is not None:
        body["post_filter"] = post_filter

    if query.q:
        body["highlight"] = {
            "fields": {
                "name": {},
                "description": {},
                "keywords": {},
            }
        }

    if query.sort == SortOrder.TITLE.value:
        body["sort"] = [{"name.raw": {"order": "asc", "missing": "_last"}}]

    return body


def _as_str(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return html.unescape(value.strip())
    return None


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_as_str(v) for v in value) if item]
    single = _as_str(value)
    return [single] if single else []


def _normalize_type(raw: Any) -> str | None:
    values = _as_str_list(raw) if not isinstance(raw, str) else [_as_str(raw) or ""]
    candidates = [v.lower() for v in values if v]
    if not candidates:
        return None
    priority = (
        "dataset",
        "person",
        "organization",
        "creativework",
        "researchproject",
        "event",
        "course",
        "service",
    )
    for preferred in priority:
        if preferred in candidates:
            return preferred
    return candidates[0]


def _display_type(normalized: str | None, raw: Any) -> str:
    if normalized == "creativework":
        return "CreativeWork"
    if normalized == "researchproject":
        return "ResearchProject"
    if normalized:
        return normalized.title()
    values = _as_str_list(raw)
    return values[0] if values else "Record"


def _map_highlight(highlight: dict[str, list[str]] | None) -> dict[str, str] | None:
    if not highlight:
        return None
    mapped: dict[str, str] = {}
    for field, fragments in highlight.items():
        if not fragments:
            continue
        key = "title" if field == "name" else field
        mapped[key] = html.unescape(fragments[0])
    return mapped or None


def map_document_to_item(
    es_id: str,
    source: dict[str, Any],
    *,
    index: str | None = None,
    highlight: dict[str, list[str]] | None = None,
    elasticsearch_document_url: str | None = None,
    score: float | None = None,
) -> SearchItem:
    source_code = _as_str(source.get("source")) or "unknown"
    doc_id = _as_str(source.get("id")) or es_id
    record_id = encode_record_id(source_code, doc_id)
    normalized = _normalize_type(source.get("type"))
    summary = _as_str(source.get("description"))
    url = _as_str(source.get("url")) or _as_str(source.get("source_url"))
    item = SearchItem(
        id=record_id,
        title=_as_str(source.get("name")) or "(untitled)",
        summary=summary,
        type=_display_type(normalized, source.get("type")),
        url=url,
        source=SourceRef(
            id=source_code,
            name=None,
        ),
        highlight=_map_highlight(highlight),
        spatial=extract_spatial_extent(source),
        elasticsearch_document_url=elasticsearch_document_url,
    )
    # Attach score for composite ranking without changing the public schema.
    object.__setattr__(item, "_score", score if score is not None else 0.0)
    return item


def map_search_response(
    query: SearchQuery,
    raw: dict[str, Any],
    *,
    document_url_for: Callable[[str, str], str] | None = None,
) -> SearchResponse:
    hits = raw.get("hits", {})
    total_value = hits.get("total", {})
    total = total_value.get("value", 0) if isinstance(total_value, dict) else int(total_value or 0)

    items: list[SearchItem] = []
    for hit in hits.get("hits", []):
        source = hit.get("_source", {})
        es_id = hit.get("_id", "")
        index = hit.get("_index", "")
        doc_url = None
        if document_url_for and index:
            doc_url = document_url_for(index, es_id)
        items.append(
            map_document_to_item(
                es_id,
                source,
                index=index,
                highlight=hit.get("highlight"),
                elasticsearch_document_url=doc_url,
                score=hit.get("_score") or 0.0,
            )
        )

    aggs = raw.get("aggregations", {})
    type_facets = [
        FacetBucket(value=str(bucket["key"]), count=bucket["doc_count"])
        for bucket in aggs.get("types", {}).get("buckets", {}).get("buckets", [])
        if bucket.get("key")
    ]
    source_facets = [
        SourceFacetBucket(
            id=str(bucket["key"]),
            name=None,
            count=bucket["doc_count"],
        )
        for bucket in aggs.get("sources", {}).get("buckets", {}).get("buckets", [])
        if bucket.get("key")
    ]

    return SearchResponse(
        total=total,
        facets=SearchFacets(types=type_facets, sources=source_facets),
        items=items,
        page=query.page,
        size=query.size,
    )
