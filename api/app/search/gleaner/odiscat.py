from elasticsearch import AsyncElasticsearch


class OdiscatNames:
    """Lazy cache of datasource display names from the odiscat index (keyed by slug/_id)."""

    def __init__(self) -> None:
        self._names: dict[str, str] = {}
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
                "_source": ["name"],
            },
        )
        payload = response.body if hasattr(response, "body") else response
        for hit in payload.get("hits", {}).get("hits", []):
            name = hit.get("_source", {}).get("name")
            if isinstance(name, str) and name.strip():
                self._names[hit["_id"]] = name.strip()

        self._loaded = True

    def get(self, source_id: str) -> str | None:
        return self._names.get(source_id)

    def as_dict(self) -> dict[str, str]:
        return dict(self._names)
