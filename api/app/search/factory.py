from app.config import Settings
from app.search.base import SearchBackend
from app.search.elasticsearch.backend import ElasticsearchBackend
from app.search.gleaner.backend import GleanerBackend

# Default first: federated `odis` index. Second: legacy odis_metadata on :9200.
KNOWN_BACKENDS: tuple[str, ...] = ("elasticsearch", "legacy")


def create_search_backend(settings: Settings, backend_name: str | None = None) -> SearchBackend:
    name = (backend_name or settings.search_backend).lower()
    if name == "elasticsearch":
        return GleanerBackend(settings)
    if name == "legacy":
        return ElasticsearchBackend(settings)
    raise ValueError(
        f"Unknown search backend: {name}. Use 'elasticsearch' (odis index) or 'legacy'."
    )


def create_all_backends(settings: Settings) -> dict[str, SearchBackend]:
    """Instantiate every known backend so the UI can switch without restarting."""
    return {name: create_search_backend(settings, name) for name in KNOWN_BACKENDS}
