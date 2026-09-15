# Developer convenience commands for the backend.
# Usage: make <target>

PYTHON ?= python3
UVICORN_HOST ?= 0.0.0.0
UVICORN_PORT ?= 8000

.PHONY: help install dev migrate makemigration downgrade test lint sample docker-up docker-down

help:
	@echo "Targets:"
	@echo "  install        Install Python dependencies"
	@echo "  dev            Run the API with auto-reload"
	@echo "  migrate        Apply all Alembic migrations (alembic upgrade head)"
	@echo "  makemigration  Autogenerate a new migration (m=\"message\")"
	@echo "  downgrade      Roll back one migration"
	@echo "  test           Run the test suite"
	@echo "  sample         Generate the sample Excel plan"
	@echo "  docker-up      Start Postgres + API via docker compose (from repo root)"

install:
	$(PYTHON) -m pip install -r requirements.txt

dev:
	$(PYTHON) -m uvicorn app.main:app --reload --host $(UVICORN_HOST) --port $(UVICORN_PORT)

migrate:
	alembic upgrade head

makemigration:
	alembic revision --autogenerate -m "$(m)"

downgrade:
	alembic downgrade -1

test:
	$(PYTHON) -m pytest

sample:
	$(PYTHON) scripts/generate_sample_plan.py sample_data/DSA_Recursion_to_Trees_8_Week_Plan.xlsx

docker-up:
	cd .. && docker compose up --build

docker-down:
	cd .. && docker compose down
