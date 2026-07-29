# Yara Backend

Django + DRF modular monolith for the Yara Care Platform.

## Prerequisites

- Python 3.12+
- PostgreSQL 15+

## Quick Start

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your local PostgreSQL credentials

# Create the database (PostgreSQL shell or createdb)
createdb yara
createdb yara_test

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

Health check: `GET http://127.0.0.1:8000/api/v1/health/`

## Settings

| Environment | Module |
|-------------|--------|
| Development | `config.settings.development` (default) |
| Production | `config.settings.production` |
| Tests | `config.settings.test` |

Set `DJANGO_SETTINGS_MODULE` to override the default.

## Testing

```bash
pytest
python manage.py check
lint-imports
python manage.py seed_identity_access
```

Domain tests require PostgreSQL. Configure `TEST_DATABASE_URL` in `.env` before running `pytest tests/identity_access/`.

## Identity & Access API (B1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register/` | Create user account |
| POST | `/api/v1/auth/token/` | Obtain JWT (phone + password) |
| POST | `/api/v1/auth/token/refresh/` | Refresh JWT |
| GET/PATCH | `/api/v1/users/me/` | Current user profile |
| GET/POST | `/api/v1/elders/` | List/create elders |
| GET/PATCH | `/api/v1/elders/{id}/` | Elder detail/update |
| GET | `/api/v1/elders/{id}/members/` | List memberships |
| POST | `/api/v1/invitations/accept/` | Accept invitation |
| GET/PUT | `/api/v1/elders/{id}/emergency-recipients/` | Emergency recipients |
| POST | `/api/v1/elders/{id}/permissions/check/` | Permission check (`Can`) |

After migrations, seed roles and permissions:

```bash
python manage.py seed_identity_access
```

## Project Layout

```text
backend/
  config/          # Django project (settings, URLs, WSGI)
  common/          # Shared infrastructure (health, etc.)
  domains/         # Domain Django apps (B1+)
  architecture/    # Architecture check helpers
  tests/           # Test suite
```

Domain apps are added under `domains/` as Frozen Domain Contracts are implemented.

## Architecture Guardrails

- **import-linter** — `.importlinter` enforces import boundaries (expanded in B1).
- **model_relations** — helper for cross-domain FK checks in pytest.
- **contracts.py** — allowlist for permitted cross-domain FKs per Frozen Contracts.
