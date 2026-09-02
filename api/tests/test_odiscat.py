import pytest

from app.search.gleaner.odiscat import OdiscatNames


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
async def test_odiscat_names_loads_name_field_only() -> None:
    client = FakeElasticsearch(
        {
            "hits": {
                "hits": [
                    {
                        "_id": "ocean-biodiversity-information-system",
                        "_source": {"name": "Ocean Biodiversity Information System"},
                    },
                    {"_id": "oceanexpert", "_source": {"name": "OceanExpert"}},
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
        "_source": ["name"],
    }
    assert names.get("ocean-biodiversity-information-system") == (
        "Ocean Biodiversity Information System"
    )
    assert names.get("oceanexpert") == "OceanExpert"
    assert names.get("geonova-geographic-catalog") is None
    assert names.as_dict() == {
        "ocean-biodiversity-information-system": "Ocean Biodiversity Information System",
        "oceanexpert": "OceanExpert",
    }

    # Second load is a no-op.
    await names.load(client, "odiscat")
    assert client.last_body == {
        "size": 200,
        "query": {"match_all": {}},
        "_source": ["name"],
    }
