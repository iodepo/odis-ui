# ODIS UI

Faceted search UI for ODIS metadata records. Read-only FastAPI backend + Svelte frontend.

Search is backed by Elasticsearch. Two backends are supported (switchable in the UI):

| Backend id | Cluster | Corpus |
|------------|---------|--------|
| `elasticsearch` (default) | Gleaner ES (`GLEANER_ELASTICSEARCH_URL`) | Federated `odis` index only |
| `legacy` | ODIS metadata ES (`ELASTICSEARCH_URL`) | Single `odis_metadata` index |

The UI header switcher selects the active backend per browser (sent as `X-Search-Backend`). Server default remains `SEARCH_BACKEND` in `.env`.

See [`docs/faceted-search-plan.md`](docs/faceted-search-plan.md) and [`docs/data-sources-analysis.md`](docs/data-sources-analysis.md) for background.

## Prerequisites

- Docker
- Access to the Gleaner Elasticsearch cluster with the `odis` index (default)
- Optional: access to the legacy `odis_metadata` Elasticsearch for the Legacy backend

## Quick start (development)

```bash
git clone https://github.com/iobis/odis-ui.git
cd odis-ui
cp .env.example .env
docker compose up --build
```

Open http://localhost:8080

- Frontend: http://localhost:8080/
- API health: http://localhost:8080/api/v1/health
- API docs (Swagger): http://localhost:8080/api/docs
- API docs (ReDoc): http://localhost:8080/api/redoc

## Production

Production runs nginx (static UI + reverse proxy) and the API in Docker. TLS uses host-installed Certbot with certificates on the VPS filesystem, bind-mounted into the nginx container.

### Prerequisites

- A domain pointing at the VPS (DNS A/AAAA record)
- Ports 80 and 443 open in the firewall
- Docker on the VPS
- Certbot on the host:

```bash
sudo apt update && sudo apt install -y certbot
sudo mkdir -p /var/www/certbot
```

### First deploy with TLS

```bash
sudo ./scripts/init-letsencrypt.sh
```

### Updates (after TLS bootstrap)

```bash
./scripts/deploy-prod.sh --pull
```

## Running tests

```bash
cd api && pip install -e ".[dev]" && pytest
```

Or via Docker:

```bash
docker compose run --rm api pytest
```
