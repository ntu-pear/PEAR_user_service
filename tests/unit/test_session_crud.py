from unittest import mock

import pytest

from app.crud import session_crud
from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


@mock.patch("app.crud.session_crud.log_crud_action")
def test_delete_sessions_logs_system_actor_for_expired_sessions_only(mock_log_crud, db_session_mock):
    expired_session = mock.MagicMock()
    expired_session.id = "SESS0001"
    expired_session.user_id = "U12345"

    active_session = mock.MagicMock()
    active_session.id = "SESS0002"
    active_session.user_id = "U99999"

    db_session_mock.query.return_value.all.return_value = [expired_session, active_session]

    with mock.patch(
        "app.crud.session_crud.check_session_expiry", side_effect=[True, False]
    ) as mock_check_expiry:
        session_crud.delete_sessions(db_session_mock)

    assert mock_check_expiry.call_count == 2
    mock_check_expiry.assert_any_call(session_id="SESS0001", db=db_session_mock)
    mock_check_expiry.assert_any_call(session_id="SESS0002", db=db_session_mock)

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "SYSTEM"
    assert kwargs["role"] == "SYSTEM"
    assert kwargs["entity_id"] == "SESS0001"
    assert kwargs["original_data"] == {"id": "SESS0001", "user_id": "U12345"}
    assert kwargs["table"] == "session"


@mock.patch("app.crud.session_crud.log_crud_action")
def test_delete_sessions_no_log_when_nothing_expired(mock_log_crud, db_session_mock):
    active_session = mock.MagicMock()
    active_session.id = "SESS0002"
    active_session.user_id = "U99999"

    db_session_mock.query.return_value.all.return_value = [active_session]

    with mock.patch("app.crud.session_crud.check_session_expiry", return_value=False):
        session_crud.delete_sessions(db_session_mock)

    mock_log_crud.assert_not_called()
