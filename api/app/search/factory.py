from app.config import Settings
from app.search.base import SearchBackend
from app.search.gleaner.backend import GleanerBackend

KNOWN_BACKENDS: tuple[str, ...] = ("elasticsearch",)


def create_search_backend(settings: Settings, backend_name: str | None = None) -> SearchBackend:
    name = (backend_name or settings.search_backend).lower()
    if name == "elasticsearch":
        return GleanerBackend(settings)
    raise ValueError(f"Unknown search backend: {name}. Use 'elasticsearch'.")


def create_all_backends(settings: Settings) -> dict[str, SearchBackend]:
    """Instantiate every known backend (currently the federated ODIS index only)."""
    return {name: create_search_backend(settings, name) for name in KNOWN_BACKENDS}
