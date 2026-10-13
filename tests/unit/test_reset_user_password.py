from datetime import date
from unittest import mock

import pytest
from fastapi import HTTPException

from app.routers import user_router
from app.schemas import account as schemas_account

from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


def make_payload(**overrides):
    fields = {
        "nric": "S1234567A",
        "nric_DateOfBirth": date(1990, 1, 1),
        "newPassword": "ILoVEFYP!123",
        "confirmPassword": "ILoVEFYP!123",
    }
    fields.update(overrides)
    return schemas_account.RequestResetPasswordBase(**fields)


def make_matching_user():
    mock_user = mock.MagicMock()
    mock_user.id = "U12345"
    mock_user.nric_FullName = "DANIEL ANG"
    mock_user.nric = "S1234567A"
    mock_user.nric_DateOfBirth = date(1990, 1, 1)
    mock_user.roleName = "DOCTOR"
    return mock_user


@mock.patch("app.routers.user_router.log_crud_action")
def test_request_reset_password_logs_nric_dob_resolved_actor(mock_log_crud, db_session_mock):
    mock_user = make_matching_user()
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_user

    payload = make_payload()

    result = user_router.request_reset_password(account=payload, db=db_session_mock)

    assert result == {"Password Updated"}
    db_session_mock.commit.assert_called_once()

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "U12345"
    assert kwargs["user_full_name"] == "DANIEL ANG"
    assert kwargs["role"] == "DOCTOR"
    assert kwargs["entity_id"] == "U12345"
    assert kwargs["log_type"] == "auth"


@mock.patch("app.routers.user_router.log_crud_action")
def test_request_reset_password_mismatched_passwords(mock_log_crud, db_session_mock):
    mock_user = make_matching_user()
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_user

    payload = make_payload(newPassword="ILoVEFYP!123", confirmPassword="Different!123")

    with pytest.raises(HTTPException) as excinfo:
        user_router.request_reset_password(account=payload, db=db_session_mock)

    assert excinfo.value.status_code == 404
    mock_log_crud.assert_not_called()


@mock.patch("app.routers.user_router.log_crud_action")
def test_request_reset_password_user_not_found(mock_log_crud, db_session_mock):
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    payload = make_payload()

    with pytest.raises(HTTPException) as excinfo:
        user_router.request_reset_password(account=payload, db=db_session_mock)

    assert excinfo.value.status_code == 404
    mock_log_crud.assert_not_called()


@mock.patch("app.routers.user_router.log_crud_action")
def test_request_reset_password_invalid_identity(mock_log_crud, db_session_mock):
    mock_user = make_matching_user()
    mock_user.nric_DateOfBirth = date(1985, 5, 5)  # does not match payload's DOB
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_user

    payload = make_payload()

    with pytest.raises(HTTPException) as excinfo:
        user_router.request_reset_password(account=payload, db=db_session_mock)

    assert excinfo.value.status_code == 404
    db_session_mock.commit.assert_not_called()
    mock_log_crud.assert_not_called()
