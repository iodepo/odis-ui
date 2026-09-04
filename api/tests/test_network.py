from app.domain.network import classify_odiscat_hits, truncate_errors


def test_truncate_errors_under_limit() -> None:
    assert truncate_errors(["a", "b"]) == ["a", "b"]


def test_truncate_errors_over_limit() -> None:
    messages = [f"err-{i}" for i in range(7)]
    assert truncate_errors(messages) == [
        "err-0",
        "err-1",
        "err-2",
        "err-3",
        "err-4",
        "… and 2 more",
    ]


def test_classify_healthy_unresponsive_parsing_and_missing_source() -> None:
    hits = [
        {
            "_id": "healthy",
            "_source": {
                "name": "Healthy Node",
                "url": "https://healthy.example/sitemap.xml",
                "summoner_errors": 0,
                "summoner_pages_seen": 10,
                "summoner_messages": [],
            },
        },
        {
            "_id": "down",
            "_source": {
                "name": "Down Node",
                "url": "https://down.example/sitemap.xml",
                "summoner_errors": 2,
                "summoner_pages_seen": 0,
                "summoner_messages": ["timed out", "no page URLs from sitemap"],
            },
        },
        {
            "_id": "parse",
            "_source": {
                "name": "Parse Node",
                "url": "https://parse.example/sitemap.xml",
                "summoner_errors": 3,
                "summoner_pages_seen": 5,
                "summoner_messages": ["no application/ld+json script tags found"],
            },
        },
        {"_id": "broken"},
    ]

    status = classify_odiscat_hits(hits)

    assert status.total_nodes == 4
    assert status.unresponsive_count == 1
    assert status.parsing_error_count == 1
    assert status.summoner_error_count == 1
    assert status.total_error_nodes == 3
    assert status.unresponsive[0].name == "Down Node"
    assert status.unresponsive[0].errors == ["timed out", "no page URLs from sitemap"]
    assert status.parsing_errors[0].name == "Parse Node"
    assert status.updated_at


def test_classify_truncates_long_error_lists() -> None:
    hits = [
        {
            "_id": "many",
            "_source": {
                "name": "Many Errors",
                "url": "https://many.example/sitemap.xml",
                "summoner_errors": 8,
                "summoner_pages_seen": 0,
                "summoner_messages": [f"error {i}" for i in range(8)],
            },
        }
    ]
    status = classify_odiscat_hits(hits)
    assert status.unresponsive[0].errors[-1] == "… and 3 more"
    assert len(status.unresponsive[0].errors) == 6
