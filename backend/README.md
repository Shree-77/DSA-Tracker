# Study Plan Tracker — Backend (FastAPI)

A clean, layered FastAPI backend for importing study plans (any subject) from
Excel and tracking daily progress, streaks, and statistics.

## Tech stack

- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy 2.x (typed ORM)
- PostgreSQL
- Alembic (migrations)
- Pydantic v2 (schemas / validation)
- pandas + openpyxl (Excel import)
- pytest (tests, runnable against SQLite)

## Architecture

```
Route (app/api/routes)      # thin HTTP layer, no DB logic
  -> Service (app/services) # business logic, transactions
  -> Repository (app/repositories)  # all DB access lives here
  -> Database (SQLAlchemy models)
```

Centralized exception handling (`app/exceptions`) guarantees every error is
returned as:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} } }
```

Raw database exceptions are never surfaced to clients.

## Project layout

```
backend/
├── app/
│   ├── main.py            # FastAPI app factory, /health
│   ├── config.py          # env-driven settings
│   ├── database.py        # engine, session, Base
│   ├── models/            # Plan, StudyDay, DailyTracker, enums
│   ├── schemas/           # Pydantic request/response models
│   ├── repositories/      # DB access
│   ├── services/          # business logic (import, plan, study_day, progress)
│   ├── api/routes/        # plans, study_days, progress
│   ├── utils/             # excel_parser
│   └── exceptions/        # error types + handlers
├── alembic/               # migrations
├── tests/                 # pytest suite
├── scripts/               # sample plan generator
├── requirements.txt
├── Dockerfile
├── Makefile
└── .env.example
```

## Environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable       | Description                                   | Example                                                        |
| -------------- | --------------------------------------------- | -------------------------------------------------------------- |
| `DATABASE_URL` | SQLAlchemy Postgres URL                       | `postgresql+psycopg2://dsa:dsa@localhost:5432/dsa_tracker`     |
| `CORS_ORIGINS` | Comma-separated allowed origins               | `http://localhost:3000,http://localhost:8080`                  |
| `APP_ENV`      | `development` or `production`                 | `development`                                                  |
| `LOG_LEVEL`    | Logging level                                 | `INFO`                                                         |

No secrets are hard-coded; all sensitive values come from the environment.

## Local setup (without Docker)

1. **Create a PostgreSQL database:**

   ```bash
   sudo -u postgres psql -c "CREATE USER dsa WITH PASSWORD 'dsa';"
   sudo -u postgres psql -c "CREATE DATABASE dsa_tracker OWNER dsa;"
   ```

2. **Install dependencies:**

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   # or: make install
   ```

3. **Run migrations:**

   ```bash
   alembic upgrade head
   # or: make migrate
   ```

4. **Run the server:**

   ```bash
   uvicorn app.main:app --reload
   # or: make dev
   ```

   API docs: <http://localhost:8000/docs>

## Docker (recommended)

From the repository root:

```bash
docker compose up --build
```

This starts PostgreSQL and the API. The API container runs
`alembic upgrade head` automatically before serving on port 8000.

## Generating the sample Excel plan

```bash
make sample
# writes sample_data/DSA_Recursion_to_Trees_8_Week_Plan.xlsx (56 days)
```

## API endpoints

| Method   | Path                                          | Description                    |
| -------- | --------------------------------------------- | ------------------------------ |
| `GET`    | `/health`                                     | Health check `{"status":"ok"}` |
| `POST`   | `/api/plans/import`                           | Import an .xlsx plan           |
| `POST`   | `/api/plans/import/preview`                   | Validate + preview (no commit) |
| `GET`    | `/api/plans`                                  | List plans                     |
| `GET`    | `/api/plans/{plan_id}`                        | Get a plan                     |
| `DELETE` | `/api/plans/{plan_id}`                        | Delete a plan (cascade)        |
| `GET`    | `/api/plans/{plan_id}/days`                   | List study days                |
| `GET`    | `/api/plans/{plan_id}/days/{day_number}`      | Get one day                    |
| `PATCH`  | `/api/plans/{plan_id}/days/{day_number}`      | Update status / notes          |
| `GET`    | `/api/plans/{plan_id}/today`                  | Today's task + upcoming        |
| `GET`    | `/api/plans/{plan_id}/progress`               | Progress + streaks + stats     |
| `GET`    | `/api/study-days/{id}/tracker`                | Get tracker (204 if none)      |
| `PUT`    | `/api/study-days/{id}/tracker`                | Upsert tracker                 |

### Import request

`multipart/form-data`:

- `file`: the `.xlsx` file
- `start_date`: date mapped to Day 1 (e.g. `2026-09-15`)
- `plan_name` (optional): overrides the plan name

Day *n* is scheduled on `start_date + (n - 1)` days. The same plan can be
re-imported with a different start date.

## Running tests

```bash
pytest
# or: make test
```

Tests run against an in-memory SQLite database (no Postgres required) and cover
Excel import (valid, missing columns, invalid rows, duplicate days, rollback),
study-day updates, tracker upserts, progress, streak logic, and the full API.

## Migrations (Alembic)

```bash
alembic upgrade head          # apply latest
alembic downgrade -1          # roll back one
alembic revision --autogenerate -m "add column"   # new migration
```

Do **not** rely on auto-creating tables at startup in production — always run
`alembic upgrade head`.

## Deployment

The backend is provider-agnostic. Recommended path:

- **Database:** a managed PostgreSQL instance (Render / Railway / Neon / RDS).
- **API:** build the `Dockerfile` and deploy to Render, Railway, Fly.io, etc.

Set `DATABASE_URL`, `CORS_ORIGINS`, and `APP_ENV=production` as environment
variables in your host. The container runs migrations on boot.
