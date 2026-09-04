import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_network_status_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/network-status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] == 3
    assert data["total_error_nodes"] == 2
    assert data["unresponsive_count"] == 1
    assert data["parsing_error_count"] == 1
    assert data["unresponsive"][0]["name"] == "Unresponsive Node"
    assert data["parsing_errors"][0]["name"] == "Parsing Node"
