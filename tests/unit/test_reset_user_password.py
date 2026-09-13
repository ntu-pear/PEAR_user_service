import asyncio
from unittest import mock

import pytest
from fastapi import HTTPException

from app.routers import user_router
from app.models.user_model import User
from app.schemas import account as schemas_account

from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


@mock.patch("app.routers.user_router.log_crud_action")
@mock.patch("app.routers.user_router.EmailService.confirm_token")
def test_reset_user_password_logs_token_resolved_actor(mock_confirm_token, mock_log_crud, db_session_mock):
    mock_confirm_token.return_value = {"userId": "U12345", "email": "user@example.com"}

    mock_user = mock.MagicMock()
    mock_user.id = "U12345"
    mock_user.nric_FullName = "DANIEL ANG"
    mock_user.roleName = "DOCTOR"
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_user

    payload = schemas_account.UserResetPassword(
        newPassword="ILoVEFYP!123",
        confirmPassword="ILoVEFYP!123",
    )

    result = asyncio.run(
        user_router.reset_user_password(token="tok", userResetPassword=payload, db=db_session_mock)
    )

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
@mock.patch("app.routers.user_router.EmailService.confirm_token")
def test_reset_user_password_mismatched_passwords(mock_confirm_token, mock_log_crud, db_session_mock):
    mock_confirm_token.return_value = {"userId": "U12345", "email": "user@example.com"}

    payload = schemas_account.UserResetPassword(
        newPassword="ILoVEFYP!123",
        confirmPassword="Different!123",
    )

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            user_router.reset_user_password(token="tok", userResetPassword=payload, db=db_session_mock)
        )

    assert excinfo.value.status_code == 404
    mock_log_crud.assert_not_called()


@mock.patch("app.routers.user_router.log_crud_action")
@mock.patch("app.routers.user_router.EmailService.confirm_token")
def test_reset_user_password_user_not_found(mock_confirm_token, mock_log_crud, db_session_mock):
    mock_confirm_token.return_value = {"userId": "missing", "email": "missing@example.com"}
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    payload = schemas_account.UserResetPassword(
        newPassword="ILoVEFYP!123",
        confirmPassword="ILoVEFYP!123",
    )

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            user_router.reset_user_password(token="tok", userResetPassword=payload, db=db_session_mock)
        )

    assert excinfo.value.status_code == 404
    mock_log_crud.assert_not_called()
