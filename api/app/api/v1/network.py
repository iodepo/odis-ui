from fastapi import APIRouter

from app.dependencies import SearchBackendDep
from app.domain.network import NetworkStatusResponse

router = APIRouter(tags=["network"])


@router.get(
    "/network-status",
    response_model=NetworkStatusResponse,
    summary="ODIS network node status",
)
async def network_status(backend: SearchBackendDep) -> NetworkStatusResponse:
    """Classify ODISCat nodes by summoner health (unresponsive / parsing errors)."""
    return await backend.network_status()
