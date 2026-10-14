import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.routers import user_auth_router
from app.service import user_auth_service


@pytest.fixture
def events(monkeypatch):
    recorded = []

    def record(event, reason=None, user_id=None, **fields):
        recorded.append((event, reason, user_id))

    monkeypatch.setattr(user_auth_router, "auth_event", record)
    return recorded


def _db_returning(user):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db


def _login(db, password="pw"):
    form = SimpleNamespace(username="someone@example.com", password=password)
    return asyncio.run(user_auth_router.login_for_access_token(form_data=form, db=db))


def _refresh(body, db=None):
    request = SimpleNamespace(json=AsyncMock(return_value=body))
    return asyncio.run(user_auth_router.refresh_access_token(request=request, db=db or MagicMock()))


def test_unknown_user_is_logged_without_the_email(events):
    with pytest.raises(HTTPException) as exc:
        _login(_db_returning(None))
    assert exc.value is user_auth_service.user_credentials_exception
    assert events == [("login_failed", "unknown_user", None)]


def test_wrong_password(events, monkeypatch):
    monkeypatch.setattr(user_auth_service, "verify_password", lambda plain, hashed: False)
    user = SimpleNamespace(id="U5", password="hash", verified=True)
    with pytest.raises(HTTPException) as exc:
        _login(_db_returning(user))
    assert exc.value is user_auth_service.user_credentials_exception
    assert events == [("login_failed", "wrong_password", "U5")]


def test_unverified_account(events, monkeypatch):
    monkeypatch.setattr(user_auth_service, "verify_password", lambda plain, hashed: True)
    user = SimpleNamespace(id="U5", password="hash", verified=False)
    with pytest.raises(HTTPException) as exc:
        _login(_db_returning(user))
    assert exc.value is user_auth_service.user_verify_exception
    assert events == [("login_failed", "unverified_account", "U5")]


def test_missing_refresh_token(events):
    with pytest.raises(HTTPException) as exc:
        _refresh({})
    assert exc.value.status_code == 400
    assert events == [("refresh_failed", "missing_refresh_token", None)]


def test_undecodable_refresh_token(events, monkeypatch):
    def reject(token):
        raise user_auth_service.invalid_token_exception

    monkeypatch.setattr(user_auth_service, "decode_refresh_token", reject)
    with pytest.raises(HTTPException) as exc:
        _refresh({"refresh_token": "bogus"})
    assert exc.value is user_auth_service.invalid_token_exception
    assert events == [("refresh_failed", "Could not validate token", None)]


def test_refresh_token_not_matching_the_session(events, monkeypatch):
    payload = {"userId": "U5", "fullName": "A", "roleName": "CAREGIVER", "email": "a@b.c", "sessionId": "S1"}
    monkeypatch.setattr(user_auth_service, "decode_refresh_token", lambda token: payload)
    monkeypatch.setattr(user_auth_service, "create_access_token", lambda data: {"token": "t", "expires_at": None})

    def mismatch(session_id, token, db):
        raise HTTPException(status_code=404, detail="Invalid Token or Session")

    monkeypatch.setattr(user_auth_service, "check_refresh_token", mismatch)
    with pytest.raises(HTTPException) as exc:
        _refresh({"refresh_token": "r"})
    assert exc.value.status_code == 404
    assert events == [("refresh_failed", "Invalid Token or Session", "U5")]


def test_successful_refresh_logs_no_auth_event(events, monkeypatch):
    payload = {"userId": "U5", "fullName": "A", "roleName": "CAREGIVER", "email": "a@b.c", "sessionId": "S1"}
    monkeypatch.setattr(user_auth_service, "decode_refresh_token", lambda token: payload)
    monkeypatch.setattr(user_auth_service, "create_access_token", lambda data: {"token": "t", "expires_at": None})
    monkeypatch.setattr(user_auth_service, "check_refresh_token", lambda session_id, token, db: None)
    monkeypatch.setattr(user_auth_router.user_Session, "update_session", lambda **kwargs: None)
    assert _refresh({"refresh_token": "r"})["access_token"] == "t"
    assert events == []
