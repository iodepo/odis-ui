"""Type-specific display profiles for search result cards.

Each presenter turns a summoned document (root fields + `jsonld`) into a title
and optional facts. Register a new presenter when a record type needs a
different title strategy or extra fields on the card.
"""

from __future__ import annotations

import html
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from app.domain.search import DisplayFact

UNTITLED = "(untitled)"
_SCHEMA_PREFIXES = ("", "schema:")
_JSONLD_KEYS = ("jsonld", "data")


@dataclass(frozen=True)
class RecordDisplay:
    title: str
    facts: tuple[DisplayFact, ...] = field(default_factory=tuple)


Presenter = Callable[[dict[str, Any]], RecordDisplay]


def _blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = html.unescape(value.strip())
        return text or None
    if isinstance(value, dict):
        for key in ("@value", "value"):
            if key in value:
                return _text(value[key])
        return None
    if isinstance(value, list):
        parts = [part for item in value if (part := _text(item))]
        return " ".join(parts) if parts else None
    return None


def _lookup(obj: dict[str, Any], name: str) -> Any:
    for prefix in _SCHEMA_PREFIXES:
        key = f"{prefix}{name}"
        if key in obj and not _blank(obj[key]):
            return obj[key]
    return None


def _layers(source: dict[str, Any]) -> list[dict[str, Any]]:
    layers = [source]
    for key in _JSONLD_KEYS:
        blob = source.get(key)
        if isinstance(blob, dict):
            layers.append(blob)
    return layers


def get_property(source: dict[str, Any], *names: str) -> Any:
    """Return the first non-empty property from root fields or JSON-LD."""
    for layer in _layers(source):
        for name in names:
            value = _lookup(layer, name)
            if value is not None:
                return value
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _entity_label(value: Any) -> str | None:
    if isinstance(value, dict):
        return (
            _text(_lookup(value, "legalName"))
            or _text(_lookup(value, "name"))
            or _text(_lookup(value, "alternateName"))
        )
    return _text(value)


def _identifier_fact(raw: Any) -> DisplayFact | None:
    text = _text(raw)
    if not text:
        return None
    lowered = text.lower()
    href = text if "://" in text else None
    path = urlparse(text).path.rstrip("/").split("/")[-1] if href else text

    if "orcid.org" in lowered or (not href and path.count("-") == 3):
        orcid = path if path.count("-") == 3 else text
        return DisplayFact(
            label="ORCID",
            value=orcid,
            href=href or f"https://orcid.org/{orcid}",
        )
    if "oceanexpert.org" in lowered:
        return DisplayFact(label="OceanExpert", value=path or text, href=href or text)
    if "ror.org" in lowered:
        return DisplayFact(label="ROR", value=path or text, href=href or text)
    return None


def default_presenter(source: dict[str, Any]) -> RecordDisplay:
    title = _text(get_property(source, "name")) or UNTITLED
    return RecordDisplay(title=title)


def person_presenter(source: dict[str, Any]) -> RecordDisplay:
    title = _text(get_property(source, "name"))
    if not title:
        given = _text(get_property(source, "givenName"))
        family = _text(get_property(source, "familyName"))
        title = " ".join(part for part in (given, family) if part) or UNTITLED

    facts: list[DisplayFact] = []
    works_for = _entity_label(get_property(source, "worksFor"))
    if works_for:
        facts.append(DisplayFact(label="Organization", value=works_for))
    affiliation = _entity_label(get_property(source, "affiliation"))
    if affiliation and affiliation != works_for:
        facts.append(DisplayFact(label="Affiliation", value=affiliation))
    for identifier in _as_list(get_property(source, "identifier")):
        fact = _identifier_fact(identifier)
        if fact and all(existing.href != fact.href for existing in facts):
            facts.append(fact)

    return RecordDisplay(title=title, facts=tuple(facts))


def organization_presenter(source: dict[str, Any]) -> RecordDisplay:
    title = (
        _text(get_property(source, "name"))
        or _text(get_property(source, "legalName"))
        or _text(get_property(source, "alternateName"))
        or UNTITLED
    )
    return RecordDisplay(title=title)


PRESENTERS: dict[str, Presenter] = {
    "person": person_presenter,
    "organization": organization_presenter,
}


def display_for(source: dict[str, Any], normalized_type: str | None) -> RecordDisplay:
    presenter = PRESENTERS.get(normalized_type or "", default_presenter)
    return presenter(source)
