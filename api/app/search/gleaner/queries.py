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
from app.search.display import display_for
from app.search.gleaner.odiscat import OdiscatNames
from app.search.elasticsearch.mappings import pascal_type, raw_types_for_filter
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
                "description": {"number_of_fragments": 0},
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


def _strip_type_prefix(value: str) -> str:
    return value.removeprefix("schema:").removeprefix("sc:")


def _normalize_type(raw: Any) -> str | None:
    values = _as_str_list(raw) if not isinstance(raw, str) else [_as_str(raw) or ""]
    candidates = [_strip_type_prefix(v).lower() for v in values if v]
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
    if normalized:
        return pascal_type(normalized)
    values = _as_str_list(raw)
    return _strip_type_prefix(values[0]) if values else "Record"


def _merge_type_facets(buckets: list[dict[str, Any]]) -> list[FacetBucket]:
    """Collapse schema.org prefix variants (Dataset vs schema:Dataset) into one facet."""
    counts: dict[str, int] = {}
    for bucket in buckets:
        key = bucket.get("key")
        if not key:
            continue
        canonical = _strip_type_prefix(str(key)).lower()
        if not canonical:
            continue
        counts[canonical] = counts.get(canonical, 0) + int(bucket["doc_count"])
    return [
        FacetBucket(value=pascal_type(canonical), count=count)
        for canonical, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _highlight_field_key(field: str) -> str:
    if field == "name":
        return "title"
    if field == "description":
        return "summary"
    return field


def _map_highlight(highlight: dict[str, list[str]] | None) -> dict[str, str] | None:
    if not highlight:
        return None
    mapped: dict[str, str] = {}
    for field, fragments in highlight.items():
        if not fragments:
            continue
        mapped[_highlight_field_key(field)] = html.unescape(fragments[0])
    return mapped or None


def map_document_to_item(
    es_id: str,
    source: dict[str, Any],
    *,
    index: str | None = None,
    highlight: dict[str, list[str]] | None = None,
    elasticsearch_document_url: str | None = None,
    score: float | None = None,
    source_names: OdiscatNames | dict[str, str] | None = None,
) -> SearchItem:
    source_code = _as_str(source.get("source")) or "unknown"
    doc_id = _as_str(source.get("id")) or es_id
    record_id = encode_record_id(source_code, doc_id)
    normalized = _normalize_type(source.get("type"))
    display = display_for(source, normalized)
    summary = _as_str(source.get("description"))
    url = _as_str(source.get("url")) or _as_str(source.get("source_url"))

    if isinstance(source_names, OdiscatNames):
        entry = source_names.get(source_code)
        source_ref = SourceRef(
            id=source_code,
            name=entry.name if entry else None,
            url=entry.url if entry else None,
            domain=entry.domain if entry else None,
            last_indexed=entry.last_indexed if entry else None,
        )
    else:
        source_ref = SourceRef(
            id=source_code,
            name=(source_names or {}).get(source_code),
        )

    item = SearchItem(
        id=record_id,
        title=display.title,
        summary=summary,
        type=_display_type(normalized, source.get("type")),
        url=url,
        facts=list(display.facts),
        source=source_ref,
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
    source_names: OdiscatNames | dict[str, str] | None = None,
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
                source_names=source_names,
            )
        )

    aggs = raw.get("aggregations", {})
    type_facets = _merge_type_facets(
        aggs.get("types", {}).get("buckets", {}).get("buckets", [])
    )
    name_dict: dict[str, str] = (
        source_names.as_dict() if isinstance(source_names, OdiscatNames) else (source_names or {})
    )
    source_facets = [
        SourceFacetBucket(
            id=str(bucket["key"]),
            name=name_dict.get(str(bucket["key"])),
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
