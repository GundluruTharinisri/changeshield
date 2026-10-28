# ChangeShield

ChangeShield is a FastAPI-based API compatibility platform. It compares two OpenAPI 3 JSON specifications, detects breaking changes, calculates an explainable risk score, and stores structured findings for review.

## Why this project exists

API consumers can break when a provider removes fields, changes types, removes endpoints, or adds required request fields. ChangeShield turns those changes into a repeatable compatibility report before deployment.

## Features

- OpenAPI 3 JSON upload and validation
- Breaking and non-breaking change detection
- Explainable risk scoring from 0 to 100
- Structured findings with recommendations
- JSONL traffic replay against a candidate API with latency and status reporting
- PostgreSQL-ready persistence via SQLAlchemy
- FastAPI Swagger documentation
- Unit and API tests
- Docker and GitHub Actions setup

## Architecture

```text
Client -> FastAPI -> Specification Store (SQLAlchemy) -> PostgreSQL/SQLite
                         |
                         +-> Comparison Engine -> Findings + Risk Score
```

## Quick start

### Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Open Swagger at http://localhost:8000/docs.

### Docker

```bash
docker compose up --build
```

The default local development database is SQLite. Docker uses PostgreSQL through `DATABASE_URL`.

## Demo

Upload the example specifications:

```bash
OLD=$(curl -s -X POST 'http://localhost:8000/api/v1/specs?name=orders-v1' \
  -F 'file=@examples/orders-v1.json' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')

NEW=$(curl -s -X POST 'http://localhost:8000/api/v1/specs?name=orders-v2' \
  -F 'file=@examples/orders-v2.json' | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')

curl -X POST http://localhost:8000/api/v1/comparisons \
  -H 'Content-Type: application/json' \
  -d "{\"old_spec_id\":\"$OLD\",\"new_spec_id\":\"$NEW\"}"
```

The example intentionally demonstrates a removed response field, a response type change, a newly required request field, and an added endpoint.

## Traffic replay demo

Start the included candidate API in a second terminal:

```bash
uvicorn examples.candidate_api:app --port 9000
```

Then use Swagger's `POST /api/v1/replays` endpoint with:

```text
candidate_url: http://127.0.0.1:9000
file: examples/sample-traffic.jsonl
```

The replay report records the expected status, actual status, response time and pass/fail result for every request. The sample intentionally expects a `404` for `/orders/404`, while the candidate API returns `200`, so the report contains one failure.

## Risk scoring

- Critical: 25 points
- Major: 15 points
- Minor: 5 points
- Warning: 2 points
- Informational: 0 points

The total is capped at 100. This is an explainable project-specific heuristic, not a universal industry standard.

## Tests and lint

```bash
pytest -q
ruff check .
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/specs?name=...` | Upload an OpenAPI JSON file |
| GET | `/api/v1/specs` | List uploaded specifications |
| POST | `/api/v1/comparisons` | Compare two specification IDs |
| GET | `/api/v1/comparisons/{id}` | Retrieve a saved report |
| POST | `/api/v1/replays` | Replay JSONL traffic against a candidate API |
| GET | `/api/v1/replays` | List saved replay reports |
| GET | `/api/v1/replays/{id}` | Retrieve a replay report |

## Engineering trade-offs

The first version uses a modular monolith and synchronous comparison/replay work because the demo workloads are small and deterministic. For large specifications or production traffic, replay and comparison work should move to a background queue and expose a polling status endpoint. Schema `$ref` resolution, authentication and a web dashboard remain future iterations.

## Future improvements

- `$ref` resolution and richer parameter comparison
- Async job queue for large comparisons
- Traffic replay against a candidate base URL
- Authentication and team workspaces
- Prometheus metrics
- Web UI for report exploration
