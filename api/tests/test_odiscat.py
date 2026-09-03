import pytest

from app.search.gleaner.odiscat import OdiscatEntry, OdiscatNames


class FakeSearchResponse:
    def __init__(self, body: dict) -> None:
        self.body = body


class FakeElasticsearch:
    def __init__(self, body: dict) -> None:
        self.body = body
        self.last_index: str | None = None
        self.last_body: dict | None = None

    async def search(self, *, index: str, body: dict) -> FakeSearchResponse:
        self.last_index = index
        self.last_body = body
        return FakeSearchResponse(self.body)


@pytest.mark.asyncio
async def test_odiscat_loads_metadata_fields() -> None:
    client = FakeElasticsearch(
        {
            "hits": {
                "hits": [
                    {
                        "_id": "ocean-biodiversity-information-system",
                        "_source": {
                            "name": "Ocean Biodiversity Information System",
                            "url": "https://obis.org",
                            "domain": "obis.org",
                            "dateModified": "2024-11-15T10:00:00Z",
                        },
                    },
                    {
                        "_id": "oceanexpert",
                        "_source": {"name": "OceanExpert"},
                    },
                    {"_id": "geonova-geographic-catalog", "_source": {}},
                ]
            }
        }
    )
    names = OdiscatNames()
    await names.load(client, "odiscat")

    assert client.last_index == "odiscat"
    assert client.last_body == {
        "size": 200,
        "query": {"match_all": {}},
        "_source": [
            "name",
            "url",
            "domain",
            "dateModified",
            "lastIndexed",
            "last_indexed",
            "indexedAt",
            "indexed_at",
        ],
    }

    entry = names.get("ocean-biodiversity-information-system")
    assert entry is not None
    assert entry == OdiscatEntry(
        name="Ocean Biodiversity Information System",
        url="https://obis.org",
        domain="obis.org",
        last_indexed="2024-11-15T10:00:00Z",
    )

    entry2 = names.get("oceanexpert")
    assert entry2 is not None
    assert entry2.name == "OceanExpert"
    assert entry2.url is None
    assert entry2.domain is None
    assert entry2.last_indexed is None

    assert names.get("geonova-geographic-catalog") is None
    assert names.get_name("ocean-biodiversity-information-system") == (
        "Ocean Biodiversity Information System"
    )
    assert names.as_dict() == {
        "ocean-biodiversity-information-system": "Ocean Biodiversity Information System",
        "oceanexpert": "OceanExpert",
    }

    # Second load is a no-op.
    await names.load(client, "odiscat")
    assert client.last_body == {
        "size": 200,
        "query": {"match_all": {}},
        "_source": [
            "name",
            "url",
            "domain",
            "dateModified",
            "lastIndexed",
            "last_indexed",
            "indexedAt",
            "indexed_at",
        ],
    }
