from app.search.elasticsearch.mappings import raw_types_for_filter
from app.search.elasticsearch.urls import elasticsearch_document_url


def test_elasticsearch_document_url() -> None:
    assert (
        elasticsearch_document_url("http://localhost:9200/", "odis_metadata", "abc123")
        == "http://localhost:9200/odis_metadata/_doc/abc123"
    )


def test_elasticsearch_document_url_encodes_special_ids() -> None:
    assert (
        elasticsearch_document_url(
            "http://odis.org:9400/",
            "gleaner-oe",
            "https://oceanexpert.org/institute/12721",
        )
        == "http://odis.org:9400/gleaner-oe/_doc/https%3A%2F%2Foceanexpert.org%2Finstitute%2F12721"
    )


def test_boattrip_type_filter_uses_pascal_case_keyword() -> None:
    assert raw_types_for_filter(["boattrip"]) == ["BoatTrip"]
