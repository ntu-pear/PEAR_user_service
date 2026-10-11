from types import SimpleNamespace
from unittest import mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.database import get_db
from app.routers import user_router
from app.service import user_auth_service as AuthService


def _user(uid, full, preferred=None):
    return SimpleNamespace(id=uid, nric_FullName=full, preferredName=preferred)


def _make_client(rows, authed=True):
    db = mock.MagicMock()
    db.query.return_value.filter.return_value.all.return_value = rows
    app = FastAPI()
    app.include_router(user_router.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    if authed:
        app.dependency_overrides[AuthService.get_current_user] = lambda: {"userId": "U1"}
    return TestClient(app), db


def test_returns_names_for_known_ids_and_omits_unknown():
    client, _ = _make_client([_user("U1", "Alice Tan"), _user("U2", "Bob Lim")])
    r = client.post("/api/v1/user/names", json={"ids": ["U1", "U2", "NOPE"]})
    assert r.status_code == 200
    assert r.json() == {"names": {"U1": "Alice Tan", "U2": "Bob Lim"}}


def test_falls_back_to_preferred_name_when_full_name_empty():
    client, _ = _make_client([_user("U1", "", "Ali"), _user("U2", None, "Bo"), _user("U3", "", None)])
    r = client.post("/api/v1/user/names", json={"ids": ["U1", "U2", "U3"]})
    assert r.status_code == 200
    assert r.json() == {"names": {"U1": "Ali", "U2": "Bo"}}


def test_dedupes_ids_and_uses_single_query():
    client, db = _make_client([_user("U1", "Alice Tan")])
    r = client.post("/api/v1/user/names", json={"ids": ["U1", "U1", "U1"]})
    assert r.status_code == 200
    assert db.query.call_count == 1


@pytest.mark.parametrize("ids", [[], ["U%d" % i for i in range(101)]])
def test_rejects_zero_or_too_many_ids(ids):
    client, _ = _make_client([])
    assert client.post("/api/v1/user/names", json={"ids": ids}).status_code == 422


def test_accepts_exactly_100_ids():
    client, _ = _make_client([])
    ids = ["U%d" % i for i in range(100)]
    r = client.post("/api/v1/user/names", json={"ids": ids})
    assert r.status_code == 200
    assert r.json() == {"names": {}}


def test_requires_token():
    client, _ = _make_client([], authed=False)
    assert client.post("/api/v1/user/names", json={"ids": ["U1"]}).status_code == 401
