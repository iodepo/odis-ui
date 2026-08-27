import pytest
from httpx import AsyncClient

from tests.fakes import FakeSearchBackend


@pytest.mark.asyncio
async def test_list_backends(client: AsyncClient, fake_backend: FakeSearchBackend) -> None:
    response = await client.get("/api/v1/backends")
    assert response.status_code == 200
    payload = response.json()
    assert payload["default"] == "elasticsearch"
    assert len(payload["backends"]) == 1
    assert payload["backends"][0]["id"] == "elasticsearch"
    assert payload["backends"][0]["health"]["status"] == "ok"


@pytest.mark.asyncio
async def test_search_respects_backend_header(
    client: AsyncClient, fake_backend: FakeSearchBackend
) -> None:
    response = await client.get(
        "/api/v1/search",
        headers={"X-Search-Backend": "elasticsearch"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_unknown_backend_header_rejected(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/search",
        headers={"X-Search-Backend": "nope"},
    )
    assert response.status_code == 400
