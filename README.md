# DSA Daily Tracker

A full-stack application for tracking daily Data Structures & Algorithms (DSA)
preparation. Import a study plan from an Excel workbook, see what to study today,
mark days complete, record study time / problems / confidence, and track your
progress and streaks.

The plan is **not** hard-coded — any `.xlsx` plan (any number of days, weeks, and
phases) can be imported, and the same plan can be re-imported with a different
start date.

> **This repository was previously a Python-games learning repo. It has been
> replaced with the DSA Daily Tracker full-stack application.**

---

## Project structure

```
.
├── backend/                 # FastAPI + SQLAlchemy + PostgreSQL + Alembic
│   ├── app/
│   │   ├── main.py          # app factory, /health
│   │   ├── config.py        # env-driven settings
│   │   ├── database.py
│   │   ├── models/          # Plan, StudyDay, DailyTracker, enums
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── repositories/    # DB access
│   │   ├── services/        # business logic (import, plan, day, progress)
│   │   ├── api/routes/      # plans, study_days, progress
│   │   ├── utils/           # excel_parser
│   │   └── exceptions/      # error types + centralized handlers
│   ├── alembic/             # migrations (0001_initial)
│   ├── tests/               # pytest suite (32 tests)
│   ├── scripts/             # sample plan generator
│   ├── sample_data/         # DSA_Recursion_to_Trees_8_Week_Plan.xlsx
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── Makefile
│   └── .env.example
│
├── frontend/                # Flutter (Material 3, Provider)
│   ├── lib/
│   │   ├── core/ models/ services/ repositories/ providers/
│   │   ├── screens/         # dashboard, plan, day_detail, progress,
│   │   │                    #   import_plan, settings
│   │   └── widgets/
│   ├── test/
│   └── pubspec.yaml
│
├── docker-compose.yml       # Postgres + API for local dev
└── README.md                # (this file)
```

## Technology stack

| Layer     | Technology                                                    |
| --------- | ------------------------------------------------------------- |
| Backend   | Python 3.12+, FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic   |
| Database  | PostgreSQL                                                     |
| Import    | pandas + openpyxl                                              |
| Tests     | pytest (backend, SQLite), flutter_test (frontend)             |
| Frontend  | Flutter, Dart, Material 3, Provider, http                     |

---

## Quick start (Docker — one command)

```bash
docker compose up --build
```

This starts PostgreSQL and the API. The API container runs `alembic upgrade head`
automatically. The API is then at:

- Swagger docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

Then run the Flutter app (see below) pointing at `http://localhost:8000`.

---

## Local setup (without Docker)

### 1. Database setup (PostgreSQL)

```bash
sudo -u postgres psql -c "CREATE USER dsa WITH PASSWORD 'dsa';"
sudo -u postgres psql -c "CREATE DATABASE dsa_tracker OWNER dsa;"
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # edit DATABASE_URL if needed
alembic upgrade head         # create tables
uvicorn app.main:app --reload
```

Generate the sample Excel plan (optional):

```bash
make sample   # -> backend/sample_data/DSA_Recursion_to_Trees_8_Week_Plan.xlsx
```

### 3. Frontend setup

```bash
cd frontend
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

> If the Android project folders are not yet generated, run `flutter create .`
> inside `frontend/` first, then wire up `network_security_config.xml`
> (see `frontend/android/app/src/main/README_ANDROID.md`).

---

## Excel import

Expected columns in the **DSA Plan** sheet (minor formatting differences are
tolerated — e.g. "Problems / Task" maps to the internal `task` field):

```
Day | Week | Phase | Focus | Problems / Task | Difficulty | Status | Completed Date | Notes
```

An optional **Daily Tracker** sheet is imported into `DailyTracker` records when
present. An **Overview** sheet may supply the plan name/description.

Import flow (in the app):

1. **Import Plan** → pick `.xlsx` → choose a **start date** (mapped to Day 1).
2. Review the preview (days / weeks / phases / date range + validation errors).
3. **Import Plan**. Imports run in a single transaction — invalid data is fully
   rolled back (never partially imported).

Day *n* is scheduled on `start_date + (n − 1)` days. Re-importing with a
different start date produces a new plan with new dates.

---

## Backend API

| Method   | Path                                       | Description               |
| -------- | ------------------------------------------ | ------------------------- |
| `GET`    | `/health`                                  | `{"status":"ok"}`         |
| `POST`   | `/api/plans/import`                        | Import a plan             |
| `POST`   | `/api/plans/import/preview`                | Validate + preview        |
| `GET`    | `/api/plans`                               | List plans                |
| `GET`    | `/api/plans/{plan_id}`                     | Get a plan                |
| `DELETE` | `/api/plans/{plan_id}`                     | Delete a plan             |
| `GET`    | `/api/plans/{plan_id}/days`                | List days                 |
| `GET`    | `/api/plans/{plan_id}/days/{day_number}`   | Get a day                 |
| `PATCH`  | `/api/plans/{plan_id}/days/{day_number}`   | Update status/notes       |
| `GET`    | `/api/plans/{plan_id}/today`               | Today's task + upcoming   |
| `GET`    | `/api/plans/{plan_id}/progress`            | Progress + streaks + stats|
| `GET`    | `/api/study-days/{id}/tracker`             | Get tracker (204 if none) |
| `PUT`    | `/api/study-days/{id}/tracker`             | Upsert tracker            |

All errors use a consistent envelope:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": {} } }
```

---

## Running tests

Backend:

```bash
cd backend
pytest          # runs against in-memory SQLite; no Postgres required
```

Frontend:

```bash
cd frontend
flutter test
```

---

## Building the Flutter app

```bash
cd frontend
# Android APK
flutter build apk --release --dart-define=API_BASE_URL=https://your-backend.example.com
# Android App Bundle
flutter build appbundle --release --dart-define=API_BASE_URL=https://your-backend.example.com
# iOS (on macOS)
flutter build ios --release --dart-define=API_BASE_URL=https://your-backend.example.com
# Web
flutter build web --release --dart-define=API_BASE_URL=https://your-backend.example.com
```

---

## Environment variables (backend)

| Variable       | Description                     | Example                                                     |
| -------------- | ------------------------------- | ----------------------------------------------------------- |
| `DATABASE_URL` | SQLAlchemy Postgres URL         | `postgresql+psycopg2://dsa:dsa@localhost:5432/dsa_tracker`  |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://localhost:8080`               |
| `APP_ENV`      | `development` / `production`    | `production`                                                |
| `LOG_LEVEL`    | Logging level                   | `INFO`                                                      |

No secrets are committed. All sensitive values come from the environment.

---

## Production deployment

See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for a step-by-step guide. Summary:

```
PostgreSQL → managed database (Render / Railway / Neon / RDS)
FastAPI    → Docker image on Render / Railway / Fly.io / DigitalOcean / AWS
Flutter    → Android / iOS / Web build pointed at the deployed API
```

You only need to provide a PostgreSQL database and backend hosting; the
container runs migrations on boot.

---

## Known limitations

- **Single-user (no auth).** By design (personal app). The layered backend is
  structured so authentication can be added later without a rewrite.
- **Offline is read-only cache**, not full sync. The current plan, today's data,
  and the day list are cached; mutations require connectivity.
- **Notifications** are best-effort local reminders (no server push); they are
  no-ops on web and require OS permission on Android 13+.
- **iOS builds** require macOS + Xcode.
