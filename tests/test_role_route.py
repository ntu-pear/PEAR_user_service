import pytest
from unittest import mock
from fastapi import HTTPException

from app.crud.role_crud import create_role, update_role, delete_role
from app.schemas.role import RoleCreate, RoleUpdate

from tests.utils.mock_db import get_db_session_mock


@mock.patch("app.crud.role_crud.sqlalchemy_to_dict")
@mock.patch("app.crud.role_crud.log_crud_action")
@mock.patch("app.crud.role_crud.Role")
def test_create_role(
    mock_role_class,
    mock_log_crud,
    mock_sqlalchemy_to_dict,
    db_session_mock,
    create_role_payload,
):
    # Query sequence inside create_role:
    # 1) existing role by roleName -> None
    # 2) access level by accessLevelId -> exists
    # 3) existing role by generated roleId -> None
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        None,
        mock.Mock(id="ACL00002"),
        None,
    ]

    mock_role = mock.Mock()
    mock_role_class.return_value = mock_role

    mock_sqlalchemy_to_dict.return_value = {
        "id": "D1234567",
        "roleName": "DOCTOR",
        "description": "Doctor role",
        "accessLevelId": "ACL00002",
        "createdById": "admin1",
        "modifiedById": "admin1",
    }

    current_user = {
        "userId": "admin1",
        "fullName": "Admin User",
        "roleName": "ADMIN",
        "email": "admin@example.com",
    }

    result = create_role(db_session_mock, create_role_payload, current_user=current_user)

    db_session_mock.add.assert_called_once_with(mock_role)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(mock_role)

    mock_sqlalchemy_to_dict.assert_called_once_with(mock_role)

    mock_log_crud.assert_called_once()
    log_call_kwargs = mock_log_crud.call_args[1]
    assert log_call_kwargs["user"] == "admin1"
    assert log_call_kwargs["user_full_name"] == "Admin User"
    assert log_call_kwargs["role"] == "ADMIN"

    assert result is mock_role

    mock_role_class.assert_called_once()
    _, kwargs = mock_role_class.call_args
    assert kwargs["roleName"] == "DOCTOR"
    assert kwargs["description"] == "Doctor role"
    assert kwargs["accessLevelId"] == "ACL00002"
    assert kwargs["createdById"] == "admin1"
    assert kwargs["modifiedById"] == "admin1"


def test_create_role_role_name_exists(db_session_mock, create_role_payload):
    # existing role by roleName -> found
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock.Mock()

    current_user = {
        "userId": "admin1",
        "fullName": "Admin User",
        "roleName": "ADMIN",
        "email": "admin@example.com",
    }

    with pytest.raises(HTTPException) as excinfo:
        create_role(db_session_mock, create_role_payload, current_user=current_user)

    assert excinfo.value.status_code == 400
    assert "already exists" in str(excinfo.value.detail).lower()


def test_create_role_access_level_not_found(db_session_mock, create_role_payload):
    # 1) existing role by roleName -> None
    # 2) access level by accessLevelId -> None
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
    ]

    current_user = {
        "userId": "admin1",
        "fullName": "Admin User",
        "roleName": "ADMIN",
        "email": "admin@example.com",
    }

    with pytest.raises(HTTPException) as excinfo:
        create_role(db_session_mock, create_role_payload, current_user=current_user)

    assert excinfo.value.status_code == 400
    assert "access level" in str(excinfo.value.detail).lower()


def test_update_role(db_session_mock, update_role_payload):
    # Query sequence inside update_role:
    # 1) db_role by roleId -> found
    # 2) duplicate roleName check -> None
    # 3) access level by accessLevelId -> found
    mock_existing_role = mock.MagicMock()
    mock_existing_role.id = "RO123456"
    mock_existing_role.roleName = "OLD_ROLE"
    mock_existing_role.description = "Old description"
    mock_existing_role.accessLevelId = "ACL00001"
    mock_existing_role.isDeleted = False

    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        mock_existing_role,
        None,
        mock.Mock(id="ACL00003"),
    ]

    result = update_role(
        db_session_mock,
        "RO123456",
        update_role_payload,
        modified_by="admin1",
    )

    assert result.roleName == "CAREGIVER"
    assert result.description == "Updated caregiver role"
    assert result.accessLevelId == "ACL00003"
    assert result.modifiedById == "admin1"

    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)


def test_update_role_duplicate_name(db_session_mock):
    mock_existing_role = mock.MagicMock()
    mock_existing_role.id = "RO123456"
    mock_existing_role.roleName = "OLD_ROLE"

    # 1) db_role by roleId -> found
    # 2) duplicate roleName check -> found
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        mock_existing_role,
        mock.Mock(),
    ]

    payload = RoleUpdate(roleName="ADMIN")

    with pytest.raises(HTTPException) as excinfo:
        update_role(db_session_mock, "RO123456", payload, modified_by="admin1")

    assert excinfo.value.status_code == 400
    assert "already exists" in str(excinfo.value.detail).lower()


def test_delete_role_success(db_session_mock):
    mock_role = mock.MagicMock()
    mock_role.id = "RO123456"
    mock_role.roleName = "CAREGIVER"

    # 1) role lookup -> found
    # 2) user lookup by roleName -> none
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        mock_role,
        None,
    ]

    result = delete_role(db_session_mock, "RO123456")

    assert mock_role.isDeleted is True
    db_session_mock.commit.assert_called_once()



def test_delete_role_users_exist(db_session_mock):
    mock_role = mock.MagicMock()
    mock_role.id = "RO123456"
    mock_role.roleName = "CAREGIVER"

    # 1) role lookup -> found
    # 2) user lookup by roleName -> found
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        mock_role,
        mock.Mock(),
    ]

    with pytest.raises(HTTPException) as excinfo:
        delete_role(db_session_mock, "RO123456")

    assert excinfo.value.status_code == 400
    assert "users with the role" in str(excinfo.value.detail).lower()


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


@pytest.fixture
def create_role_payload():
    return RoleCreate(
        roleName="DOCTOR",
        description="Doctor role",
        accessLevelId="ACL00002",
    )


@pytest.fixture
def update_role_payload():
    return RoleUpdate(
        roleName="CAREGIVER",
        description="Updated caregiver role",
        accessLevelId="ACL00003",
    )