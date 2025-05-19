import pytest
from unittest import mock
from app.crud.role_crud import create_role, update_role, delete_role
from app.models.role_model import RolePrivacyStatus
from app.schemas.role import RoleBase, RoleUpdate
from app.models.role_model import Role

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

# Mocking the relevant models
@mock.patch("app.crud.role_crud.Role") 
def test_create_role(mock_role_class, db_session_mock, Create_Role):
    # Arrange
    db_session_mock.query.return_value.filter.return_value.first.return_value = None
    # Simulate the Role class instantiation
    mock_role = mock.Mock()
    mock_role_class.return_value = mock_role

    #Act
    result = create_role(db_session_mock, Create_Role, created_by="admin1")

    # Assert
    db_session_mock.add.assert_called_once_with(mock_role)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(mock_role)

    # And we return exactly that instance
    assert result is mock_role

    # Check Role(...) was called correctly
    mock_role_class.assert_called_once()
    _, kwargs = mock_role_class.call_args
    assert kwargs["roleName"] == "DOCTOR"
    assert kwargs["accessLevelSensitive"] == RolePrivacyStatus.LOW

@mock.patch("app.crud.role_crud.Role")
def test_create_role_roleName_exist(db_session_mock, Create_Role):
    # Arrange
    existing = mock.Mock()
    db_session_mock.query.return_value.filter.return_value.first.return_value = existing

    # Act & Assert: should raise a 400 HTTPException
    with pytest.raises(HTTPException) as excinfo:
        create_role(db_session_mock, Create_Role, created_by="admin1")

    assert excinfo.value.status_code == 400
    assert "already exists" in str(excinfo.value.detail).lower()

def test_update_role(db_session_mock, Update_Role):
    """Test Case for updating a Role"""
    # Arrange
    modified_by = 1
    roleID = 123
    # Simulate Role Found with the provided id/roleName
    mock_existing_role = mock.MagicMock()
    mock_existing_role.roleName = Update_Role.roleName
    mock_existing_role.active = False 
    db_session_mock.query(Role).filter(Role.roleName == Update_Role.roleName).first.return_value = mock_existing_role
    #Act
    result=update_role(db_session_mock, roleID ,Update_Role, modified_by)
    #Assertions
    assert result.active is False
    assert result.roleName == "CAREGIVER"
    #Commit updated Role
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

@pytest.fixture
def db_session_mock():
    """Fixture to mock the database session."""
    return get_db_session_mock()

@pytest.fixture
def Create_Role():
    """Fixture to provide a mock Role Object."""
    return RoleBase(
        roleName="DOCTOR",
        accessLevelSensitive=RolePrivacyStatus.LOW,
    )

@pytest.fixture
def Update_Role():
    """Fixture to provide a mock Role Object."""
    return RoleUpdate(
        roleName="CAREGIVER",
        active = False
    )