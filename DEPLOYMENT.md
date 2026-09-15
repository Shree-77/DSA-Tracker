# Deployment Guide

The backend is provider-agnostic. You only need:

1. A **PostgreSQL** database (managed is easiest).
2. **Backend hosting** that can run the provided Docker image.

The Flutter app is then built pointing at your deployed API URL.

---

## Recommended path (Render + managed Postgres)

### 1. Create a PostgreSQL database

Use any managed Postgres (Render, Railway, Neon, Supabase, RDS, DigitalOcean).
Copy the connection string and convert it to the SQLAlchemy form:

```
postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME
```

### 2. Deploy the backend (Docker)

The `backend/Dockerfile` builds a production image that:

- installs dependencies,
- runs as a non-root user,
- exposes a `/health` endpoint,
- runs `alembic upgrade head` then starts Uvicorn on port 8000.

On Render (Web Service → "Deploy from a Dockerfile", root `backend/`), set
environment variables:

| Variable       | Value                                                          |
| -------------- | ------------------------------------------------------------- |
| `DATABASE_URL` | your `postgresql+psycopg2://...` string                       |
| `CORS_ORIGINS` | your web app origin(s), e.g. `https://app.example.com`        |
| `APP_ENV`      | `production`                                                  |
| `LOG_LEVEL`    | `INFO`                                                        |

The same variables work on Railway, Fly.io, DigitalOcean App Platform, and AWS
(ECS/App Runner). No provider-specific code is required.

### 3. Verify

```bash
curl https://your-backend.example.com/health
# {"status":"ok"}
```

Open `https://your-backend.example.com/docs` for the OpenAPI UI.

### 4. Build the Flutter app against the deployed API

```bash
cd frontend
flutter build web    --release --dart-define=API_BASE_URL=https://your-backend.example.com
flutter build apk    --release --dart-define=API_BASE_URL=https://your-backend.example.com
# iOS (on macOS):
flutter build ios    --release --dart-define=API_BASE_URL=https://your-backend.example.com
```

Users can also change the API URL at runtime in **Settings → API Server**.

---

## Manual (non-Docker) deployment

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME"
export CORS_ORIGINS="https://app.example.com"
export APP_ENV=production
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Put it behind a reverse proxy (nginx/Caddy) terminating TLS.

---

## Production checklist

- [x] CORS configured via `CORS_ORIGINS`
- [x] DB credentials via `DATABASE_URL` (no secrets in source)
- [x] Production `Dockerfile` (non-root, healthcheck)
- [x] `GET /health` returns `{"status":"ok"}`
- [x] Alembic migrations (`alembic upgrade head`) — no auto-create at startup
- [x] Centralized error handling; raw DB errors never exposed
- [x] Structured logging (`LOG_LEVEL`)
- [x] OpenAPI docs at `/docs`
- [x] `APP_ENV=production` (no debug/reload)
