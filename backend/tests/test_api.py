"""End-to-end API tests via TestClient."""

from __future__ import annotations

from datetime import date

import pytest

from tests import fixtures

START = "2026-09-15"


def _import(client) -> int:
    content = fixtures.build_valid_workbook()
    resp = client.post(
        "/api/plans/import",
        data={"start_date": START},
        files={
            "file": (
                "plan.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["plan"]["id"]


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_import_and_list_plans(client):
    plan_id = _import(client)
    resp = client.get("/api/plans")
    assert resp.status_code == 200
    plans = resp.json()
    assert len(plans) == 1
    assert plans[0]["id"] == plan_id
    assert plans[0]["total_days"] == 56


def test_import_preview_endpoint(client):
    content = fixtures.build_valid_workbook()
    resp = client.post(
        "/api/plans/import/preview",
        data={"start_date": START},
        files={"file": ("plan.xlsx", content, "application/octet-stream")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["total_days"] == 56
    assert body["total_weeks"] == 8


def test_invalid_file_type_rejected(client):
    resp = client.post(
        "/api/plans/import",
        data={"start_date": START},
        files={"file": ("plan.csv", b"a,b,c", "text/csv")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_FILE_TYPE"


def test_get_day_and_patch(client):
    plan_id = _import(client)

    resp = client.get(f"/api/plans/{plan_id}/days/8")
    assert resp.status_code == 200
    body = resp.json()
    assert body["day_number"] == 8
    assert body["phase"] == "Recursive Sorting"
    assert body["status"] == "NOT_STARTED"

    patch = client.patch(
        f"/api/plans/{plan_id}/days/8", json={"status": "DONE"}
    )
    assert patch.status_code == 200
    assert patch.json()["status"] == "DONE"
    assert patch.json()["completed_at"] is not None


def test_today_endpoint_active(client):
    plan_id = _import(client)
    # Day 8 is scheduled on 2026-09-22.
    resp = client.get(f"/api/plans/{plan_id}/today", params={"today": "2026-09-22"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "active"
    assert body["day"]["day_number"] == 8
    assert len(body["upcoming"]) == 3


def test_today_before_start(client):
    plan_id = _import(client)
    resp = client.get(f"/api/plans/{plan_id}/today", params={"today": "2026-09-12"})
    body = resp.json()
    assert body["state"] == "before"
    assert body["days_until_start"] == 3


def test_today_after_end(client):
    plan_id = _import(client)
    resp = client.get(f"/api/plans/{plan_id}/today", params={"today": "2026-12-01"})
    assert resp.json()["state"] == "completed"


def test_progress_endpoint(client):
    plan_id = _import(client)
    client.patch(f"/api/plans/{plan_id}/days/1", json={"status": "DONE"})
    resp = client.get(f"/api/plans/{plan_id}/progress", params={"today": START})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_days"] == 56
    assert body["completed_days"] == 1
    assert body["current_streak"] == 1


def test_tracker_put_and_get(client):
    plan_id = _import(client)
    day = client.get(f"/api/plans/{plan_id}/days/8").json()
    study_day_id = day["id"]

    put = client.put(
        f"/api/study-days/{study_day_id}/tracker",
        json={
            "study_hours": 2.0,
            "problems_attempted": 3,
            "solved_alone": 2,
            "needed_hint": 1,
            "confidence": 4,
            "reflection": "Nice",
        },
    )
    assert put.status_code == 200
    assert put.json()["study_hours"] == 2.0

    get = client.get(f"/api/study-days/{study_day_id}/tracker")
    assert get.status_code == 200
    assert get.json()["confidence"] == 4


def test_invalid_confidence_rejected(client):
    plan_id = _import(client)
    day = client.get(f"/api/plans/{plan_id}/days/8").json()
    resp = client.put(
        f"/api/study-days/{day['id']}/tracker",
        json={"confidence": 9},
    )
    assert resp.status_code == 422


def test_missing_plan_returns_404(client):
    resp = client.get("/api/plans/9999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PLAN_NOT_FOUND"


def test_delete_plan(client):
    plan_id = _import(client)
    resp = client.delete(f"/api/plans/{plan_id}")
    assert resp.status_code == 204
    assert client.get(f"/api/plans/{plan_id}").status_code == 404
