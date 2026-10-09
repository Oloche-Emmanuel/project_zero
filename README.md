# Rental Property Management API

A REST API for managing rental properties, units, tenants, leases, rent
payments, and maintenance requests — built with Python, FastAPI, and
SQLAlchemy.

## Key features

- **Properties & units** — record properties (address, type) and their
  individual rentable units (bedrooms, rent, vacancy status).
- **Tenants** — tenant profiles with contact and emergency-contact info,
  optionally linked to a login account.
- **Leases** — bind a tenant to a unit for a date range and rent amount;
  a unit can't have two active leases at once, and the unit's
  vacant/occupied status is kept in sync automatically.
- **Rent invoicing & payments** — generate rent invoices per lease, record
  (partial or full) payments against them, and flag invoices overdue.
- **Maintenance requests** — tenants/staff log issues per unit, tracked
  through open → in_progress → completed/cancelled.
- **Auth & role-based access control** — JWT-based login with three
  roles (`admin`, `landlord`, `tenant`); landlords only see their own
  properties, admins see everything.

## Architecture

This is a **modular monolith**: one deployable service, internally split
into self-contained feature modules so it can grow — or later be peeled
apart into services — without a rewrite.

```
src/rentalapp/
├── main.py              # FastAPI app factory; wires routers together
├── config.py             # Settings (env-driven, pydantic-settings)
├── database.py            # SQLAlchemy engine/session, declarative Base
├── core/                  # Cross-cutting code shared by every module
│   ├── security.py        # password hashing, JWT encode/decode
│   ├── deps.py             # get_current_user, require_roles(...)
│   ├── exceptions.py        # AppError hierarchy -> HTTP status mapping
│   └── repository.py         # generic CRUD base class
└── modules/
    ├── users/          ─┐
    ├── properties/       │  each module is a vertical slice:
    ├── tenants/           │    models.py     SQLAlchemy ORM models
    ├── leases/             │    schemas.py    Pydantic request/response
    ├── payments/            │    repository.py DB queries (extends BaseRepository)
    └── maintenance/       ─┘    service.py    business rules
                                  router.py     FastAPI endpoints
```

**Why this shape:**

- **Each module owns its slice end-to-end** (model → repo → service →
  router). Adding a feature — e.g. a `notifications` or `documents`
  module — means adding a new folder under `modules/` and one line in
  `main.py`'s `create_app()`. Nothing existing has to change.
- **Business rules live in `service.py`, not in routers.** Routers only
  do HTTP concerns (auth, status codes, request/response shapes). This
  keeps rules like "a unit can't have two active leases" testable and
  reusable if a second interface (CLI, background job, GraphQL) is added
  later.
- **Repositories isolate persistence.** `BaseRepository` gives every
  module basic CRUD for free; each module only writes the queries that
  are actually specific to it. Swapping SQLite for Postgres is a
  one-line `DATABASE_URL` change (see `.env.example`); swapping
  SQLAlchemy for something else would only touch `database.py` and the
  repositories, not services or routers.
- **`core/exceptions.py` decouples errors from HTTP.** Services raise
  `NotFoundError`, `ConflictError`, etc.; a single handler in `main.py`
  turns those into HTTP responses, so services stay framework-agnostic.
- **Alembic is wired up** (`alembic.ini`, `migrations/`) for schema
  migrations once the app moves past ad-hoc `create_all()` during local
  development.

### Natural extension points

- New domain module: notifications (email/SMS on invoice due, lease
  expiring), documents (lease PDFs, receipts — store metadata in a
  `documents` module, files in S3/local disk), reporting/analytics.
- Swap JWT bearer auth for OAuth2/SSO by changing only `core/security.py`
  and `core/deps.py`.
- Add a background scheduler (e.g. APScheduler or a cron-triggered
  endpoint) calling `InvoiceService.refresh_overdue_statuses()` and a new
  "generate next month's invoices" job.
- Add a `documents` module for lease/ID uploads without touching leases
  or tenants.
- Multi-tenancy (SaaS for many property-management companies): add an
  `organization_id` column + a scoping dependency in `core/deps.py`.

## Tech stack

| Concern          | Choice                                   |
|-------------------|-------------------------------------------|
| Language          | Python 3.11+                               |
| API framework     | FastAPI                                    |
| ORM               | SQLAlchemy 2.0 (typed declarative models)   |
| Validation        | Pydantic v2                                 |
| DB (dev)          | SQLite (file-based, zero setup)              |
| DB (prod-ready)   | PostgreSQL (`DATABASE_URL`, `pip install .[postgres]`) |
| Migrations        | Alembic                                       |
| Auth              | JWT (python-jose) + bcrypt (passlib)           |
| Tests             | pytest + FastAPI's TestClient                   |

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
```

Run the API (auto-creates SQLite tables on startup for local dev):

```bash
uvicorn rentalapp.main:app --reload --app-dir src
```

Open http://127.0.0.1:8000/docs for interactive Swagger UI.

Run tests:

```bash
pytest
```

For production schema changes, use Alembic instead of the dev
auto-create:

```bash
alembic revision --autogenerate -m "add invoices table"
alembic upgrade head
```

## Example flow

1. `POST /api/v1/auth/register` — create a `landlord` user.
2. `POST /api/v1/auth/login` — get a JWT (send as `Authorization: Bearer <token>`).
3. `POST /api/v1/properties` — create a property.
4. `POST /api/v1/properties/{id}/units` — add a unit.
5. `POST /api/v1/tenants` — create a tenant profile.
6. `POST /api/v1/leases` — lease the unit to the tenant (unit auto-flips to `occupied`).
7. `POST /api/v1/invoices` — create a rent invoice for the lease.
8. `POST /api/v1/invoices/{id}/payments` — record a payment against it.
9. `POST /api/v1/maintenance-requests` — log an issue on the unit.
