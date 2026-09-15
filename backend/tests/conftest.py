"""Pytest fixtures: isolated in-memory SQLite DB + FastAPI test client.

Tests run against SQLite so they need no external Postgres server, while the
production app uses Postgres. The ORM models are dialect-agnostic.

Every endpoint (except health/root/auth) now requires a bearer token. The
default ``client`` fixture registers a user and auto-attaches its token so the
existing test-suite keeps exercising the business logic. Tests that need to
verify auth behaviour (e.g. cross-user isolation) can use ``unauth_client`` and
``make_user``.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        Base.metadata.drop_all(bind=eng)
        eng.dispose()


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def unauth_client(engine) -> Generator[TestClient, None, None]:
    """A test client with NO auth header attached."""
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register(client: TestClient, username: str, password: str = "password123") -> str:
    """Register a user and return their access token."""
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def make_user(unauth_client):
    """Factory: register a user, return a TestClient pre-authenticated as them.

    Because all fixtures share the same in-memory engine, multiple clients built
    from this factory talk to the same database but as different users — ideal
    for testing per-user data isolation.
    """
    created: list[TestClient] = []

    def _factory(username: str, password: str = "password123") -> TestClient:
        token = _register(unauth_client, username, password)
        client = TestClient(app)
        client.headers.update({"Authorization": f"Bearer {token}"})
        created.append(client)
        return client

    yield _factory


@pytest.fixture()
def client(unauth_client) -> TestClient:
    """Default client, pre-authenticated as a standard test user."""
    token = _register(unauth_client, "testuser")
    unauth_client.headers.update({"Authorization": f"Bearer {token}"})
    return unauth_client


@pytest.fixture()
def test_user_id(db_session) -> int:
    """Create a user directly in the DB and return its id.

    Used by service-layer tests that construct services with an explicit
    ``user_id`` rather than going through the HTTP auth flow.
    """
    from app.models import User
    from app.security import hash_password

    user = User(username="svc_tester", password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user.id
