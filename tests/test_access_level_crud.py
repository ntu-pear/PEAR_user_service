import pytest
from unittest import mock
from fastapi import HTTPException

from app.crud.access_level_crud import (
    get_all_access_levels,
    get_access_level_by_id,
    create_access_level,
    update_access_level,
    delete_access_level,
)
from app.schemas.access_level import AccessLevelCreate, AccessLevelUpdate

from tests.utils.mock_db import get_db_session_mock

from datetime import datetime


def test_get_all_access_levels(db_session_mock):
    mock_level_1 = mock.MagicMock()
    mock_level_1.id = "ACL00001"
    mock_level_1.code = "NONE"
    mock_level_1.levelRank = 0
    mock_level_1.levelName = "None"
    mock_level_1.description = "No access to sensitive data"
    mock_level_1.isSystem = True

    mock_level_2 = mock.MagicMock()
    mock_level_2.id = "ACL00002"
    mock_level_2.code = "LOW"
    mock_level_2.levelRank = 1
    mock_level_2.levelName = "Low"
    mock_level_2.description = "Limited access to low-sensitivity data"
    mock_level_2.isSystem = True

    db_session_mock.query.return_value.order_by.return_value.all.return_value = [
        mock_level_1,
        mock_level_2,
    ]

    result = get_all_access_levels(db_session_mock)

    assert len(result) == 2
    assert result[0].code == "NONE"
    assert result[1].code == "LOW"


def test_get_access_level_by_id(db_session_mock):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL00003"
    mock_level.code = "MEDIUM"

    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_level

    result = get_access_level_by_id(db_session_mock, "ACL00003")

    assert result is mock_level
    assert result.code == "MEDIUM"


def test_create_access_level_success(db_session_mock, create_access_level_payload):
    # create_access_level query sequence:
    # 1) code lookup -> None (no duplicate)
    # 2) rank lookup -> None (no duplicate)
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
    ]

    # Simulate db.refresh() populating server-set timestamp fields on the object
    def mock_refresh(obj):
        obj.createdDate = datetime.now()
        obj.modifiedDate = datetime.now()

    db_session_mock.refresh.side_effect = mock_refresh

    result = create_access_level(
        db=db_session_mock,
        data=create_access_level_payload,
        new_id="ACL99999",
        created_by="admin1",
    )

    # Verify the object passed to db.add() has the correct field values
    added_obj = db_session_mock.add.call_args[0][0]
    assert added_obj.code == "RESTRICTED"
    assert added_obj.levelRank == 4

    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once()


def test_create_access_level_duplicate_code(db_session_mock, create_access_level_payload):
    # existing code lookup -> found
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock.Mock()

    with pytest.raises(HTTPException) as excinfo:
        create_access_level(
            db=db_session_mock,
            data=create_access_level_payload,
            new_id="ACL99999",
            created_by="admin1",
        )

    assert excinfo.value.status_code == 400
    assert "already exists" in str(excinfo.value.detail).lower()


def test_create_access_level_reserved_code(db_session_mock):
    payload = AccessLevelCreate(
        code="HIGH",
        levelRank=4,
        levelName="Restricted",
        description="Should fail",
    )

    with pytest.raises(HTTPException) as excinfo:
        create_access_level(
            db=db_session_mock,
            data=payload,
            new_id="ACL99999",
            created_by="admin1",
        )

    assert excinfo.value.status_code == 400
    assert "reserved" in str(excinfo.value.detail).lower()


def test_create_access_level_duplicate_rank(db_session_mock, create_access_level_payload):
    # 1) existing code lookup -> None
    # 2) existing rank lookup -> found
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        None,
        mock.Mock(),
    ]

    with pytest.raises(HTTPException) as excinfo:
        create_access_level(
            db=db_session_mock,
            data=create_access_level_payload,
            new_id="ACL99999",
            created_by="admin1",
        )

    assert excinfo.value.status_code == 400
    assert "rank already exists" in str(excinfo.value.detail).lower()


def test_update_custom_access_level_success(db_session_mock, update_access_level_payload):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL99999"
    mock_level.code = "RESTRICTED"
    mock_level.levelRank = 4
    mock_level.levelName = "Restricted"
    mock_level.description = "Old description"
    mock_level.isSystem = False
    mock_level.modifiedById = "old_admin"

    # Query sequence inside update_access_level:
    # 1) duplicate code lookup -> None
    # 2) duplicate rank lookup -> None
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
    ]

    result = update_access_level(
        db=db_session_mock,
        db_obj=mock_level,
        data=update_access_level_payload,
        modified_by="admin2",
    )

    assert result.code == "SPECIAL"
    assert result.levelRank == 5
    assert result.levelName == "Special"
    assert result.description == "Updated custom level"
    assert result.modifiedById == "admin2"

    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(mock_level)


def test_update_system_access_level_description_only(db_session_mock):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL00004"
    mock_level.code = "HIGH"
    mock_level.levelRank = 3
    mock_level.levelName = "High"
    mock_level.description = "Old description"
    mock_level.isSystem = True

    payload = AccessLevelUpdate(description="Updated system description")

    result = update_access_level(
        db=db_session_mock,
        db_obj=mock_level,
        data=payload,
        modified_by="admin1",
    )

    assert result.description == "Updated system description"
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(mock_level)


def test_update_system_access_level_forbidden_fields(db_session_mock):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL00004"
    mock_level.code = "HIGH"
    mock_level.levelRank = 3
    mock_level.levelName = "High"
    mock_level.description = "Old description"
    mock_level.isSystem = True

    payload = AccessLevelUpdate(levelName="Super High")

    with pytest.raises(HTTPException) as excinfo:
        update_access_level(
            db=db_session_mock,
            db_obj=mock_level,
            data=payload,
            modified_by="admin1",
        )

    assert excinfo.value.status_code == 403
    assert "only allow description updates" in str(excinfo.value.detail).lower()


def test_delete_access_level_success(db_session_mock):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL99999"
    mock_level.code = "SPECIAL"
    mock_level.isSystem = False
    mock_level.roles = []

    delete_access_level(db_session_mock, mock_level)

    db_session_mock.delete.assert_called_once_with(mock_level)
    db_session_mock.commit.assert_called_once()


def test_delete_access_level_system_forbidden(db_session_mock):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL00001"
    mock_level.code = "NONE"
    mock_level.isSystem = True
    mock_level.roles = []

    with pytest.raises(HTTPException) as excinfo:
        delete_access_level(db_session_mock, mock_level)

    assert excinfo.value.status_code == 403
    assert "cannot be deleted" in str(excinfo.value.detail).lower()


def test_delete_access_level_in_use(db_session_mock):
    mock_level = mock.MagicMock()
    mock_level.id = "ACL99999"
    mock_level.code = "SPECIAL"
    mock_level.isSystem = False
    mock_level.roles = [mock.Mock()]

    with pytest.raises(HTTPException) as excinfo:
        delete_access_level(db_session_mock, mock_level)

    assert excinfo.value.status_code == 400
    assert "assigned to roles" in str(excinfo.value.detail).lower()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


@pytest.fixture
def create_access_level_payload():
    return AccessLevelCreate(
        code="RESTRICTED",
        levelRank=4,
        levelName="Restricted",
        description="Restricted internal access",
    )


@pytest.fixture
def update_access_level_payload():
    return AccessLevelUpdate(
        code="SPECIAL",
        levelRank=5,
        levelName="Special",
        description="Updated custom level",
    )