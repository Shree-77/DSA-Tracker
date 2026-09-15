"""Authentication and per-user data isolation tests."""

from __future__ import annotations

from tests import fixtures

START = "2026-09-15"


def _import(client) -> int:
    content = fixtures.build_valid_workbook()
    resp = client.post(
        "/api/plans/import",
        data={"start_date": START},
        files={"file": ("plan.xlsx", content, "application/octet-stream")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["plan"]["id"]


def test_register_returns_token_and_user(unauth_client):
    resp = unauth_client.post(
        "/api/auth/register", json={"username": "alice", "password": "secret12"}
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "alice"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_duplicate_username_rejected(unauth_client):
    unauth_client.post(
        "/api/auth/register", json={"username": "bob", "password": "secret12"}
    )
    resp = unauth_client.post(
        "/api/auth/register", json={"username": "bob", "password": "another1"}
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "USERNAME_TAKEN"


def test_duplicate_username_case_insensitive(unauth_client):
    unauth_client.post(
        "/api/auth/register", json={"username": "Carol", "password": "secret12"}
    )
    resp = unauth_client.post(
        "/api/auth/register", json={"username": "carol", "password": "secret12"}
    )
    assert resp.status_code == 409


def test_login_success_and_failure(unauth_client):
    unauth_client.post(
        "/api/auth/register", json={"username": "dave", "password": "secret12"}
    )
    ok = unauth_client.post(
        "/api/auth/login", json={"username": "dave", "password": "secret12"}
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    bad = unauth_client.post(
        "/api/auth/login", json={"username": "dave", "password": "wrongpass"}
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "INVALID_CREDENTIALS"

    missing = unauth_client.post(
        "/api/auth/login", json={"username": "ghost", "password": "secret12"}
    )
    assert missing.status_code == 401


def test_protected_route_requires_token(unauth_client):
    resp = unauth_client.get("/api/plans")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_invalid_token_rejected(unauth_client):
    unauth_client.headers.update({"Authorization": "Bearer not.a.jwt"})
    resp = unauth_client.get("/api/plans")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


def test_me_returns_current_user(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_short_password_rejected(unauth_client):
    resp = unauth_client.post(
        "/api/auth/register", json={"username": "eve", "password": "123"}
    )
    assert resp.status_code == 422


def test_data_is_isolated_per_user(make_user):
    alice = make_user("alice")
    bob = make_user("bob")

    alice_plan = _import(alice)

    # Bob sees none of Alice's plans.
    assert bob.get("/api/plans").json() == []
    # Alice sees exactly her plan.
    assert [p["id"] for p in alice.get("/api/plans").json()] == [alice_plan]

    # Bob cannot read, mutate, or delete Alice's plan.
    assert bob.get(f"/api/plans/{alice_plan}").status_code == 404
    assert bob.get(f"/api/plans/{alice_plan}/days/1").status_code == 404
    assert bob.delete(f"/api/plans/{alice_plan}").status_code == 404
    assert (
        bob.patch(f"/api/plans/{alice_plan}/days/1", json={"status": "DONE"}).status_code
        == 404
    )


def test_import_only_replaces_own_plan(make_user):
    alice = make_user("alice")
    bob = make_user("bob")

    _import(alice)
    _import(bob)

    # Each user still has exactly one plan; Bob's import did not wipe Alice's.
    assert len(alice.get("/api/plans").json()) == 1
    assert len(bob.get("/api/plans").json()) == 1


def test_tracker_isolated_per_user(make_user):
    alice = make_user("alice")
    bob = make_user("bob")
    alice_plan = _import(alice)

    day = alice.get(f"/api/plans/{alice_plan}/days/1").json()
    study_day_id = day["id"]

    # Bob cannot touch Alice's study-day tracker.
    assert bob.get(f"/api/study-days/{study_day_id}/tracker").status_code == 404
    assert (
        bob.put(
            f"/api/study-days/{study_day_id}/tracker", json={"study_hours": 1.0}
        ).status_code
        == 404
    )
