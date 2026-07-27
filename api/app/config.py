from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Default: federated `odis` index on the Gleaner ES cluster (:9400).
    search_backend: str = "elasticsearch"

    # Legacy backend (SEARCH_BACKEND=legacy / X-Search-Backend: legacy) — odis_metadata on :9200.
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_user: str = ""
    elasticsearch_password: str = ""
    es_index: str = "odis_metadata"
    es_catalogue_index: str = "catalogue"

    # Default elasticsearch backend — Gleaner cluster hosting the `odis` index.
    gleaner_elasticsearch_url: str = "http://odis.org:9400"
    gleaner_elasticsearch_user: str = ""
    gleaner_elasticsearch_password: str = ""
    # Comma-separated; empty = `odis` only (per-source gleaner-* indices are ignored).
    gleaner_indices: str = "odis"


settings = Settings()
