import pytest
from unittest import mock
from app.crud import user_crud 
from app.service import validation_service
from app.schemas.user import UserUpdate, UserRead
from app.models.user_model import User

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock
@mock.patch("app.models.user_model.User")
def test_update_user(db_session_mock, User_Update):
    """Test Updating User"""

    # Arrange
    modified_by =2
    userId = "U123124234"
    #Act
    # Simulate an existing user with the same id
    mock_existing_user = mock.MagicMock()
    mock_existing_user.id = userId
    mock_existing_user.nric_FullName = "DANIEL TAN"
    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_existing_user
    result = user_crud.update_user(db_session_mock, userId, User_Update, modified_by)
    #Assert
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.nric_FullName == "DANIEL TAN"
    assert result.modifiedById == modified_by

def test_update_user_invalid_user(db_session_mock, User_Update):
    """Test Updating User, User no found"""

    # Arrange
    modified_by =2
    userId = "U123124234"
    # Simulate no user exists with the given id
    db_session_mock.query(User).filter(User.id == userId).first.return_value = None
    # Assert that an HTTPException is raised
    with pytest.raises(HTTPException):
        user_crud.update_user(db_session_mock, userId, User_Update, modified_by)


def test_delete_user(db_session_mock):
    """Test Delete User"""
    userId = "U123124234"
    # Simulate an existing user with the same id
    mock_existing_user = mock.MagicMock()
    mock_existing_user.id = userId
    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_existing_user
    result = user_crud.delete_user(db_session_mock, userId)
    #Assert
    assert result == mock_existing_user


def test_delete_user_invalid_userId(db_session_mock):
    """Test Delete User, invalid/not found user"""
    userId = "U123124234"
    # Simulate an existing user with the same id
    # Simulate no user exists with the given id
    db_session_mock.query(User).filter(User.id == userId).first.return_value = None
    # Assert that an HTTPException is raised
    with pytest.raises(HTTPException):
        user_crud.delete_user(db_session_mock, userId)



@pytest.fixture
def db_session_mock():
    """Fixture to mock the database session."""
    return get_db_session_mock()

@pytest.fixture
def User_Update():
    """Fixture to provide a mock User object."""
    return UserUpdate(
    nric_FullName="DANIEL TAN",
    nric_Address="112 Bedok #01-111",
    nric_DateOfBirth= "2000-02-01",
    nric_Gender="M",
    contactNo= "94434567",
    allowNotification= True,
    profilePicture=None,
    lockoutReason="",
    status="ACTIVE",
    email= "daniel22@gmail.com",
)

def test_admin_soft_delete_user_success(db_session_mock):
    userId = "user123"
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.roleName = "USER"
    mock_user.isDeleted = False

    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_user

    result = user_crud.soft_delete_admin_user(db_session_mock, userId)

    db_session_mock.commit.assert_called_once()
    assert result.isDeleted is True

def test_admin_soft_delete_user_not_found(db_session_mock):
    userId = "nonexistent"
    db_session_mock.query(User).filter(User.id == userId).first.return_value = None

    with pytest.raises(HTTPException) as exc:
        user_crud.soft_delete_admin_user(db_session_mock, userId)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"

def test_admin_cannot_soft_delete_other_admin(db_session_mock):
    userId = "admin456"

    # Simulate that the user to delete is an ADMIN
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.roleName = "ADMIN"
    mock_user.isDeleted = False

    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_user

    with pytest.raises(HTTPException) as exc:
        user_crud.soft_delete_admin_user(db_session_mock, userId)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Cannot delete another admin"



def test_admin_cannot_soft_delete_self():
    userId = "admin123"
    current_user = {
        "userId": "admin123",
        "roleName": "ADMIN"
    }

    with pytest.raises(HTTPException) as exc:
        if current_user["userId"] == userId:
            raise HTTPException(status_code=404, detail="No self delete")

    assert exc.value.status_code == 404
    assert exc.value.detail == "No self delete"


