# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI payment service that handles multi-gateway payment processing (Midtrans, Xendit), transaction management, voucher systems, and product catalogs. The system supports multi-database architecture (primary/replica/analytics) and webhook callbacks from payment gateways.

**Key domains:** products, transactions, vouchers, payment methods, gateways, webhooks, reports/analytics, admin configuration.

## Tech Stack

- **Framework:** FastAPI 0.118.0 with Uvicorn 0.37.0
- **Database:** SQLAlchemy 2.0.43 + SQLModel 0.0.25, Alembic 1.16.5 (migrations)
- **Config:** Pydantic 2.11.10, pydantic-settings 2.11.0
- **Database drivers:** psycopg2 for PostgreSQL
- **Python:** 3.11+

## Development Commands

### Database Setup & Migrations

```bash
# Apply pending migrations
alembic upgrade head

# Create a new migration (auto-detect changes from entities)
alembic revision --autogenerate -m "describe change"

# View migration history
alembic history

# Downgrade to previous version
alembic downgrade -1
```

### Run Development Server

```bash
# Default: port 9080, auto-reload on code changes
uvicorn app.main:app --reload --port=9080

# Without reload (cleaner logs)
uvicorn app.main:app --port=9080

# With different port
uvicorn app.main:app --reload --port=8000
```

### Environment Setup

- Copy `.env` to your local environment (see `app/config/database.py` for all `DB_*` prefixes)
- Default: PostgreSQL on localhost:5432, database `fastapi_payment`
- Optional replicas via `REPLICA_DB_*` env vars
- Optional analytics DB via `ANALYTICS_DB_*` env vars

## Code Architecture

### Layer Structure

```
app/
├── domain/           # Core business logic (entities, schemas, repositories)
│   ├── entity/       # SQLModel ORM models (Product, Transaction, PaymentMethod, etc)
│   ├── schema/       # Pydantic request/response schemas
│   └── repository/   # Query builders & interfaces (not concrete repos in this codebase)
├── interfaces/http/  # FastAPI route handlers
│   ├── routes/       # Endpoint groups by domain (products.py, transactions.py, etc)
│   └── middleware/   # HTTP middleware
├── infrastructure/   # External integrations & persistence
│   ├── database/     # Connection pool, database manager, migrations
│   └── storage/      # Abstract storage interface (unused; for future extensibility)
├── config/           # Settings: database, CORS, general app config
├── core/             # Shared utilities: logging, exceptions, enums
└── main.py           # FastAPI app factory, lifespan events
```

### Key Patterns

**Multi-Database Manager:**
- `app/infrastructure/database/manager.py` registers and manages connections (primary, replica, analytics)
- Initialized in `main.py` lifespan (startup/shutdown)
- Env vars control which DBs are enabled (only primary is required)

**Repository Query Builder:**
- `app/domain/repository/query_builder.py` provides chainable query syntax (select, filter, join, pagination)
- Used directly in routes to avoid repository boilerplate; not abstracted into service layer (keep it simple)

**Schema-Entity Separation:**
- Entities (`domain/entity/`) define database models (SQLModel)
- Schemas (`domain/schema/`) define request/response contracts (Pydantic)
- Conversions are inline in route handlers

**Webhook Handling:**
- Gateway callbacks validated by signature (SHA512 for Midtrans, token for Xendit)
- `POST /webhook/payment/{gateway_code}` receives and validates callbacks
- Signature validation prevents processing invalid requests
- Callbacks are logged and mapped to internal transaction status
- See `documentation.md` sections 5-7 for full webhook flow and gateway setup

### Common Operations in Routes

- Use `query_builder.py` for database queries: `Builder(model).select(...).filter(...).paginate(...)`
- Always validate webhook signatures before processing
- Convert Pydantic schemas to entities before saving
- Map gateway-specific status codes to internal enum values (see `domain/entity/enums.py`)

## Data Flow: Transaction Lifecycle

1. **Create** → `POST /api/transactions` (cart → transaction)
2. **Select Payment** → `POST /api/transactions/{id}/pay` (choose method & gateway)
3. **Process** → gateway processes (user pays via bank transfer, card, etc)
4. **Callback** → `POST /webhook/payment/{gateway_code}` (gateway notifies)
5. **Update Status** → transaction marked paid/pending/failed
6. **Verify** → `GET /api/transactions/{id}/status` or webhook retry logic

Vouchers are validated and applied at step 2 (before payment).

## Setup Data Order (Mandatory Before Live)

Follow this sequence to avoid runtime payment failures:

1. Create applications (`applications` table) with app_key, app_secret, callback_url
2. Seed payment gateways (`payment_gateways` table) — Midtrans, Xendit, etc
3. Add gateway credentials per app (`payment_gateway_credentials`)
4. Add payment methods (`payment_methods`) — virtual account, e-wallet, card, etc
5. Map methods to gateways (`payment_method_gateways`) — defines fallback chain
6. Seed products and vouchers

See `documentation.md` sections 3-7 for full setup checklist and endpoint maps.

## Important Notes

- **Never hard-delete data:** Use soft deletes (`is_active=false`); historical transactions must remain.
- **Webhook signature validation is critical:** All gateway callbacks must validate before updating transaction state.
- **Multi-gateway fallback:** Priority order in `payment_gateways` table determines fallback sequence.
- **Credentials per app:** Each application has separate credentials per gateway (no sharing).
- **Callback idempotency:** If same webhook fires twice, second should be a no-op (check before updating).

## Documentation References

- **Setup & Operations:** `documentation.md` (Indonesian) — full step-by-step setup, data seeding, gateway checklist
- **Database Schema:** `readme.md` — table descriptions and purposes

## Admin Operations

Endpoints in `/api/admin/` for:
- Application key management & rotation
- Gateway configuration (toggle active, manage credentials)
- Manual transaction status override (emergency only)
- Webhook log retrieval and retry
- Reconciliation reports

See `documentation.md` section 6.7 for full admin endpoint list.

## Rules

- **Commits are FORBIDDEN** — Claude must NOT run `git commit` under any circumstances
- **Git read-only** — Only these operations are allowed: `git log`, `git status`, `git diff`, `git show`
- **FORBIDDEN: `git commit`, `git push`, `git merge`, `git rebase`, `git reset`** — all git write operations are prohibited
