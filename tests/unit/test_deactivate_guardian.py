from unittest import mock

import pytest
from fastapi import HTTPException

from app.crud import user_crud
from app.models.user_model import User
from app.service import user_auth_service
from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


def _user(role="GUARDIAN", is_deleted=False):
    user = mock.MagicMock()
    user.id = "U123"
    user.nric_FullName = "TAN AH KOW"
    user.roleName = role
    user.isDeleted = is_deleted
    return user


@mock.patch("app.crud.user_crud.log_crud_action")
def test_deactivate_guardian_sets_is_deleted(mock_log, db_session_mock):
    user = _user()
    db_session_mock.query(User).filter().first.return_value = user

    result = user_crud.deactivate_guardian_user(db_session_mock, "U123")

    assert result.isDeleted is True
    db_session_mock.commit.assert_called_once()
    mock_log.assert_called_once()


@mock.patch("app.crud.user_crud.log_crud_action")
def test_deactivate_guardian_is_idempotent(mock_log, db_session_mock):
    user = _user(is_deleted=True)
    db_session_mock.query(User).filter().first.return_value = user

    result = user_crud.deactivate_guardian_user(db_session_mock, "U123")

    assert result is user
    db_session_mock.commit.assert_not_called()
    mock_log.assert_not_called()


def test_deactivate_guardian_rejects_non_guardian(db_session_mock):
    db_session_mock.query(User).filter().first.return_value = _user(role="DOCTOR")

    with pytest.raises(HTTPException) as exc_info:
        user_crud.deactivate_guardian_user(db_session_mock, "U123")

    assert exc_info.value.status_code == 400
    db_session_mock.commit.assert_not_called()


def test_deactivate_guardian_user_not_found(db_session_mock):
    db_session_mock.query(User).filter().first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        user_crud.deactivate_guardian_user(db_session_mock, "U404")

    assert exc_info.value.status_code == 404


def test_get_current_user_rejects_deactivated_account(db_session_mock):
    user = _user(is_deleted=True)
    db_session_mock.query(User).filter().first.return_value = user
    details = {"userId": "U123", "sessionId": "S1", "roleName": "GUARDIAN",
               "fullName": "TAN AH KOW", "email": "a@b.com"}

    with mock.patch.object(user_auth_service, "decode_access_token", return_value=details), \
         mock.patch.object(user_auth_service, "check_access_token"):
        with pytest.raises(HTTPException) as exc_info:
            user_auth_service.get_current_user(token="t", db=db_session_mock)

    assert exc_info.value.status_code == 403
