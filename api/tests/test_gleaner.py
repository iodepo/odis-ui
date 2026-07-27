from app.domain.search import SearchQuery
from app.search.gleaner.ids import decode_record_id, encode_record_id
from app.search.gleaner.queries import build_search_body, map_document_to_item


def test_encode_decode_roundtrip() -> None:
    encoded = encode_record_id("obis", "https://obis.org/dataset/abc")
    assert encoded.startswith("gleaner:obis:")
    assert decode_record_id(encoded) == ("obis", "https://obis.org/dataset/abc")


def test_map_gleaner_dataset() -> None:
    item = map_document_to_item(
        "https://obis.org/dataset/abc",
        {
            "source": "ocean-biodiversity-information-system",
            "id": "https://obis.org/dataset/abc",
            "type": ["Dataset"],
            "name": "Turtle tracks",
            "description": "Telemetry summary",
            "url": "https://obis.org/dataset/abc",
            "keywords": ["Occurrence"],
        },
        index="odis",
    )
    assert item.id.startswith("gleaner:ocean-biodiversity-information-system:")
    assert item.type == "Dataset"
    assert item.title == "Turtle tracks"
    assert item.source is not None
    assert item.source.id == "ocean-biodiversity-information-system"
    assert item.source.name is None


def test_map_gleaner_person_with_geo() -> None:
    item = map_document_to_item(
        "https://oceanexpert.org/expert/1",
        {
            "source": "oceanexpert",
            "id": "https://oceanexpert.org/expert/1",
            "type": ["Person"],
            "name": "Ada Lovelace",
            "description": None,
            "url": None,
            "source_url": "https://oceanexpert.org/expert/1",
            "jsonld": {
                "workLocation": {
                    "geo": {"latitude": -14.2, "longitude": -51.9},
                }
            },
        },
        index="odis",
    )
    assert item.type == "Person"
    assert item.url == "https://oceanexpert.org/expert/1"
    assert item.spatial is not None
    assert item.spatial.points[0].lat == -14.2


def test_gleaner_search_body_filters_and_aggs() -> None:
    body = build_search_body(
        SearchQuery(q="coral", types=["dataset"], sources=["ocean-biodiversity-information-system"])
    )
    assert body["post_filter"]["bool"]["filter"]
    assert "types" in body["aggs"]
    assert "sources" in body["aggs"]
    assert body["query"]["bool"]["must"][0]["multi_match"]["query"] == "coral"
    assert body["track_total_hits"] is True


def test_gleaner_search_body_omits_primary_type_filter_when_graph_fragments_enabled() -> None:
    body = build_search_body(SearchQuery(include_graph_fragments=True))
    filters = body["query"]["bool"].get("filter", [])
    assert filters == []


def test_gleaner_search_body_primary_type_filter_by_default() -> None:
    body = build_search_body(SearchQuery())
    filters = body["query"]["bool"]["filter"]
    assert any("terms" in clause and "type" in clause["terms"] for clause in filters)


def test_gleaner_type_filter_preserves_pascal_case() -> None:
    body = build_search_body(SearchQuery(types=["HowToStep"], include_graph_fragments=True))
    assert body["post_filter"] == {"terms": {"type": ["HowToStep", "schema:HowToStep"]}}


def test_gleaner_type_filter_lowercase_dataset() -> None:
    body = build_search_body(SearchQuery(types=["dataset"], include_graph_fragments=True))
    type_terms = body["post_filter"]["terms"]["type"]
    assert "Dataset" in type_terms
