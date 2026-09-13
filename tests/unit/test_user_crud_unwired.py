import pytest
from unittest import mock
from fastapi import HTTPException

from app.crud import user_crud
from app.models.user_model import User

from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


@mock.patch("app.crud.user_crud.log_crud_action")
def test_reset_password_logs_actor(mock_log_crud, db_session_mock):
    userId = "U123124234"
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.nric_FullName = "DANIEL ANG"
    mock_user.roleName = "DOCTOR"
    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_user

    result = user_crud.reset_password(db_session_mock, userId, "ILoVEFYP!123", modified_by="admin1")

    assert result is mock_user
    db_session_mock.commit.assert_called_once()

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["user_full_name"] == "DANIEL ANG"
    assert kwargs["role"] == "DOCTOR"
    assert kwargs["entity_id"] == userId
    assert kwargs["log_type"] == "auth"


@mock.patch("app.crud.user_crud.log_crud_action")
def test_reset_password_user_not_found(mock_log_crud, db_session_mock):
    db_session_mock.query(User).filter(User.id == "missing").first.return_value = None

    with pytest.raises(HTTPException):
        user_crud.reset_password(db_session_mock, "missing", "ILoVEFYP!123", modified_by="admin1")
    mock_log_crud.assert_not_called()


@mock.patch("app.crud.user_crud.log_crud_action")
def test_activate_user_logs_actor(mock_log_crud, db_session_mock):
    userId = "U123124234"
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.nric_FullName = "DANIEL ANG"
    mock_user.roleName = "DOCTOR"
    mock_user.isDeleted = True
    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_user

    result = user_crud.activate_user(db_session_mock, userId, modified_by="admin1")

    assert result is mock_user
    assert mock_user.isDeleted is False
    db_session_mock.commit.assert_called_once()

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["entity_id"] == userId
    assert kwargs["original_data"] == {"isDeleted": True, "status": "deleted"}
    assert kwargs["updated_data"] == {"isDeleted": False, "status": "active"}


@mock.patch("app.crud.user_crud.log_crud_action")
def test_deactivate_user_logs_actor(mock_log_crud, db_session_mock):
    userId = "U123124234"
    mock_user_before = mock.MagicMock()
    mock_user_before.id = userId
    mock_user_before.isDeleted = False
    mock_user_before.lockOutReason = None

    mock_user_after = mock.MagicMock()
    mock_user_after.id = userId
    mock_user_after.isDeleted = True
    mock_user_after.lockOutReason = "Repeated policy violations"
    mock_user_after.nric_FullName = "DANIEL ANG"
    mock_user_after.roleName = "DOCTOR"

    db_session_mock.query(User).filter(User.id == userId).first.side_effect = [
        mock_user_before,
        mock_user_after,
    ]

    result = user_crud.deactivate_user(db_session_mock, userId, "Repeated policy violations", modified_by="admin1")

    assert result is mock_user_after
    db_session_mock.commit.assert_called_once()

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["entity_id"] == userId
    assert kwargs["original_data"] == {"isDeleted": False, "lockOutReason": None, "status": "active"}
    assert kwargs["updated_data"] == {"isDeleted": True, "lockOutReason": "Repeated policy violations", "status": "deleted"}


@mock.patch("app.crud.user_crud.log_crud_action")
def test_deactivate_user_not_found(mock_log_crud, db_session_mock):
    db_session_mock.query(User).filter(User.id == "missing").first.return_value = None

    with pytest.raises(HTTPException):
        user_crud.deactivate_user(db_session_mock, "missing", "reason", modified_by="admin1")
    mock_log_crud.assert_not_called()


@mock.patch("app.crud.user_crud.log_crud_action")
def test_update_user_profile_picture_logs_actor(mock_log_crud, db_session_mock):
    userId = "U123124234"
    mock_user_before = mock.MagicMock()
    mock_user_before.id = userId
    mock_user_before.profilePicture = "https://cdn.example.com/old.jpg"

    mock_user_after = mock.MagicMock()
    mock_user_after.id = userId
    mock_user_after.profilePicture = "https://cdn.example.com/new.jpg"
    mock_user_after.nric_FullName = "DANIEL ANG"
    mock_user_after.roleName = "DOCTOR"

    db_session_mock.query(User).filter(User.id == userId).first.side_effect = [
        mock_user_before,
        mock_user_after,
    ]

    result = user_crud.update_user_profile_picture(
        db_session_mock, userId, "https://cdn.example.com/new.jpg", modified_by="admin1"
    )

    assert result is mock_user_after
    db_session_mock.commit.assert_called_once()

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["entity_id"] == userId
    assert kwargs["original_data"] == {"profilePicture": "https://cdn.example.com/old.jpg"}
    assert kwargs["updated_data"] == {"profilePicture": "https://cdn.example.com/new.jpg"}


@mock.patch("app.crud.user_crud.log_crud_action")
def test_update_user_profile_picture_user_not_found(mock_log_crud, db_session_mock):
    db_session_mock.query(User).filter(User.id == "missing").first.return_value = None

    result = user_crud.update_user_profile_picture(db_session_mock, "missing", "https://cdn.example.com/x.jpg", modified_by="admin1")

    assert result is None
    mock_log_crud.assert_not_called()
