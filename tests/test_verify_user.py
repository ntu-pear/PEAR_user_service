import pytest
from unittest import mock
from app.crud.user_crud import create_user, verify_user
from app.service import user_service
from app.schemas.user import TempUserCreate, UserCreate
from app.models.user_model import User

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

def test_verify_user_user_found_not_verified(db_session_mock, User_Create):
    """Test Case for user found but not verified"""
    # Simulate a user in the DB with 'verified' status as "F"
    mock_user = mock.MagicMock()
    mock_user.email = User_Create.email
    mock_user.verified = False  # Account is not verified
  
    # Simulate that the user exists in the DB with the email provided
    db_session_mock.query(User).filter(User.email == User_Create.email).first.return_value = mock_user

    # Simulate verify_userDetails returning True (i.e., details match)
    with mock.patch("app.service.user_service.verify_userDetails", return_value=True):
           # Call the function to verify the user
        result = verify_user(db_session_mock, User_Create)
    
    # Assertions
    # Ensure that the account's 'verified' status is updated to True
    assert result.verified == True
    
    #Commit User with password
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

def test_verify_user_user_already_verified(db_session_mock, User_Create):
    """Test Case for user already verified"""

    # Simulate a user in the DB with 'verified' status as "Y"
    mock_user = mock.MagicMock()
    mock_user.email = User_Create.email
    mock_user.verified = True  # Account is already verified

    # Simulate that the user exists in the DB with the email provided
    db_session_mock.query(User).filter(User.email == User_Create.email).first.return_value = mock_user

    # Call the function to verify the user and assert that the account is already verified
    with pytest.raises(HTTPException) as exc_info:
        verify_user(db_session_mock, User_Create)

    # Assert that the correct HTTPException is raised
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Account has already been verified"


def test_verify_user_details_do_not_match(db_session_mock, User_Create):
    """Test Case for user found, but details do not match"""

    # Simulate a user in the DB with 'verified' status as False (Not Verified)
    mock_user = mock.MagicMock()
    mock_user.email = User_Create.email
    mock_user.verified = False  # User is not verified yet
    mock_user.nric_FullName = "John Doe"  # Different name for the mismatch
    mock_user.nric_Address = "123 Test St"  # Different address for the mismatch
    
    # Simulate that the user exists in the DB with the email provided
    db_session_mock.query(User).filter(User.email == User_Create.email).first.return_value = mock_user

    # Call the function to verify the user and assert that the details do not match
    with pytest.raises(HTTPException) as exc_info:
        verify_user(db_session_mock, User_Create)

    # Assert that the correct HTTPException is raised
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == "Details do not match with pre-registered details"

@pytest.fixture
def db_session_mock():
    """Fixture to mock the database session."""
    return get_db_session_mock()

@pytest.fixture
def User_Create():
    """Fixture to provide a mock User object. With Password"""
    from app.models.role_model import Role
    from app.models.privacy_level_setting_model import PrivacyLevelSetting
    
    return UserCreate(
    nric_FullName="DANIEL ANG",
    nric_Address="112 Bedok #01-111",
    nric_DateOfBirth= "2000-01-01",
    nric_Gender="M",
    contactNo= "91234567",
    email= "daniel@gmail.com",
    roleName= "DOCTOR",
    nric= "S1234567D",
    password = "ILoVEFYP!123")

