# Yara Backend

Django + DRF modular monolith for the Yara Care Platform.

## Prerequisites

- Python 3.12+
- PostgreSQL 15+

## Quick Start

```bash
cd backend

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"

cp env.example .env
# Set DATABASE_URL / TEST_DATABASE_URL to your real Postgres user and password.
# Django reads that password from .env; it does not use the createdb prompt.

# Skip these if the databases already exist.
createdb -U postgres -h localhost yara
createdb -U postgres -h localhost yara_test

python manage.py migrate
python manage.py seed_identity_access
python manage.py seed_licensing
python manage.py seed_hub_provision
python manage.py seed_family_lab
python manage.py seed_hub_dev_sync --device-id=<hub-device-uuid>
python manage.py runserver
```

### Hub tablet on local Wi-Fi

Bind to all interfaces so the tablet can reach your machine:

```bash
python manage.py runserver 0.0.0.0:8000
```

Development settings allow LAN hosts by default (`DEV_ALLOW_LAN_HOSTS=true`).
Use your machine's LAN IP in the Hub (e.g. `http://192.168.1.100:8000`).
To restrict hosts, set `DEV_ALLOW_LAN_HOSTS=false` and list IPs in `ALLOWED_HOSTS`.

Hub registers the tablet, then shows a caregiver login. Use the same phone and
password as the Family app (`seed_family_lab`). That authenticate call assigns
the Hub to that caregiver's elder so prescriptions and contacts can download.

Video calls need `SKYROOM_API_KEY` in `backend/.env`. An empty key returns HTTP 502
`Communication provider is not configured.` The key stays on the Backend only.

## Health & Readiness

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/v1/health/` | None | Database, event outbox, integration dispatcher, synchronization session checks |
| `GET /api/v1/hub/runtime/health/` | JWT | Hub runtime metrics + shared readiness checks |

Top-level `status`: `ok`, `degraded`, or `error` (database failure returns HTTP 503).

## Operational Commands

| Command | Purpose |
|---------|---------|
| `run_integration_cycle` | **Primary production cycle** — due occurrences, workflow timeouts, event dispatch |
| `process_due_occurrences` | Scheduling-only due scan |
| `process_workflow_timeouts` | Workflow-only timeout scan |
| `process_occurrence_due_events` | **Deprecated** — use `run_integration_cycle` |
| `seed_identity_access` | Seed roles and permissions |
| `seed_licensing` | Seed plans and entitlements |

Recommended cron (example):

```bash
python manage.py run_integration_cycle --event-limit=200
```

Options:

- `--event-limit` — cap events processed per dispatch batch (default 100)
- `--dry-run` — print planned cycle without side effects

## Settings

| Environment | Module |
|-------------|--------|
| Development | `config.settings.development` (default) |
| Production | `config.settings.production` |
| Tests | `config.settings.test` |

Set `DJANGO_SETTINGS_MODULE` to override the default.

Production requires `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS`.

## Verification

```bash
python manage.py makemigrations --check
python manage.py migrate
python manage.py check
python -m pytest
python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"
```

## Testing

Domain tests require PostgreSQL. Configure `TEST_DATABASE_URL` in `.env` before running `pytest`.

## Project Layout

```text
backend/
  config/          # Django project (settings, URLs, WSGI)
  common/          # Shared infrastructure (health, API errors, observability)
  domains/         # Domain Django apps (B1–B9)
  infrastructure/  # Provider adapters (Skyroom, etc.) — not a domain
  integration/     # Integration runtime + Hub APIs (B10)
  architecture/    # Architecture check helpers
  tests/           # Test suite
```

## Architecture Guardrails

- **import-linter** — `.importlinter` enforces import boundaries (12 contracts).
- **Frozen Domain Contracts** — business rules are not changed in hardening stages.
- **Integration isolation** — `integration/` imports only `domains.<x>.services` and Event query APIs.

## Observability Hooks (B11)

In-process metrics (no external platform integration):

- `workflow.started`, `workflow.confirmed`, `workflow.missed`
- `sync.started`, `sync.completed`
- `device.command.completed`
- `communication.session.started`
- `integration.event.*`, `integration.action.*`

Structured logging loggers: `yara.workflow`, `yara.device`, `yara.communication`, `yara.synchronization`, `yara.integration`.

Pass `X-Correlation-ID`, `X-Replica-ID`, and `X-Device-ID` on Hub requests for trace propagation.
