import pytest
from unittest import mock
from app.crud.role_crud import create_role, update_role, delete_role
from app.schemas.role import RoleCreate, RoleUpdate
from app.models.role_model import Role

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

# Mocking the relevant models
@mock.patch("app.models.role_model.Role")
def test_create_role(db_session_mock, Create_Role):
    """Test Case for creating a Role"""
    # Arrange
    created_by = 1
    # Simulate no Role exists with the given Name
    db_session_mock.query(Role).filter(Role.roleName == Create_Role.roleName).first.return_value = None
    #Act
    result = create_role(db_session_mock, Create_Role, created_by)
    # Assert
    db_session_mock.add.assert_called_once_with(result)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.roleName == "DOCTOR"

def test_create_role_roleName_exist(db_session_mock, Create_Role):
    """Test Case for creating a Role with existing Name"""  
    # Arrange
    created_by = 1
    # Simulate Role exists with the given Name
    mock_existing_role = mock.MagicMock()
    mock_existing_role.roleName = Create_Role.roleName
    db_session_mock.query(Role).filter(Role.roleName == Create_Role.roleName).first.return_value = mock_existing_role
    # Assert that an HTTPException is raised
    with pytest.raises(HTTPException):
        create_role(db_session_mock, Create_Role, created_by)

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
    return RoleCreate(
        roleName="DOCTOR",
        createdDate="2002-01-01",
        modifiedDate ="2002-01-01",
    )
@pytest.fixture
def Update_Role():
    """Fixture to provide a mock Role Object."""
    return RoleUpdate(
        roleName="CAREGIVER",
        active = False
    )