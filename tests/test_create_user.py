import pytest
from unittest import mock
from app.crud.user_crud import create_user, verify_user
from app.service import user_service
from app.schemas.user import TempUserCreate, UserCreate
from app.models.user_model import User

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock


# Mocking the relevant models
@mock.patch("app.models.user_model.User")

def test_create_user(db_session_mock, Temp_User_Create):
    """Test Case for creating a User acc"""

    # Arrange
    created_by = 1
    # Simulate no user exists with the given email
    db_session_mock.query(User).filter(User.email == Temp_User_Create.email).first.return_value = None
    # Simulate no user exists with the given nric
    db_session_mock.query(User).filter(User.nric == Temp_User_Create.nric).first.return_value = None
    #Act
    result = create_user(db_session_mock, Temp_User_Create, created_by)
    # Assert
    db_session_mock.add.assert_called_once_with(result)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.nric_FullName == "DANIEL ANG"
    assert result.createdById == created_by
    assert result.roleName == "DOCTOR"

def test_create_user_email_already_exists(db_session_mock, Temp_User_Create):
    """Test Case for existing user with the same email"""

    # Simulate an existing user with the same email
    db_session_mock.query(User).filter(User.email == Temp_User_Create.email).first.return_value = mock.MagicMock()

    # Assert that an HTTPException is raised
    with pytest.raises(HTTPException):
        create_user(db_session_mock, Temp_User_Create, created_by=1)

def test_create_user_nric_already_exists(db_session_mock, Temp_User_Create):
    """Test Case for existing user with the same email"""

    # Simulate an existing user with the same email
    db_session_mock.query(User).filter(User.nric == Temp_User_Create.nric).first.return_value = mock.MagicMock()

    # Assert that an HTTPException is raised
    with pytest.raises(HTTPException):
        create_user(db_session_mock, Temp_User_Create, created_by=1)


def test_create_user_invalid_nric(db_session_mock):
    """Test Case for invalid NRIC format"""
    invalid_user = TempUserCreate(
        nric_FullName="John Doe",
        nric_Address="123 Test St",
        nric_DateOfBirth="1990-01-01",
        nric_Gender="M",
        contactNo="91234567",
        email="john.doe@example.com",
        roleName="DOCTOR",
        nric="INVALhjh54IDNRIC"  # Invalid NRIC
    )
    with pytest.raises(HTTPException):
        create_user(db_session_mock, invalid_user, created_by=1)

@pytest.fixture
def db_session_mock():
    """Fixture to mock the database session."""
    return get_db_session_mock()

@pytest.fixture
def Temp_User_Create():
    """Fixture to provide a mock User object. W/O Password"""
    return TempUserCreate(
    nric_FullName="DANIEL ANG",
    nric_Address="112 Bedok #01-111",
    nric_DateOfBirth= "2000-01-01",
    nric_Gender="M",
    contactNo= "91234567",
    email= "daniel@gmail.com",
    roleName= "DOCTOR",
    nric= "S1234567D")

