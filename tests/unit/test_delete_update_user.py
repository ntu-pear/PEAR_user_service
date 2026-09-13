import pytest
from unittest import mock
from app.crud import user_crud 
from app.service import validation_service
from app.schemas.user import UserUpdate, UserRead
from app.models.user_model import User

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

@mock.patch("app.crud.user_crud.log_crud_action")
def test_update_user(mock_log_crud, db_session_mock, User_Update):
    """Test Updating User"""

    # Arrange
    modified_by =2
    userId = "U123124234"
    #Act
    # Simulate an existing user with the same id
    mock_existing_user = mock.MagicMock()
    mock_existing_user.id = userId
    mock_existing_user.nric_FullName = "DANIEL TAN"
    mock_existing_user.email = "daniel22@gmail.com"
    mock_existing_user.contactNo = "94434567"
    mock_existing_user.roleName = "DOCTOR"
    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_existing_user
    result = user_crud.update_user(db_session_mock, userId, User_Update, modified_by)
    #Assert
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.nric_FullName == "DANIEL TAN"
    assert result.modifiedById == modified_by

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == str(modified_by)
    assert kwargs["entity_id"] == userId
    assert kwargs["table"] == "user"

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


@mock.patch("app.crud.user_crud.log_crud_action")
def test_delete_user(mock_log_crud, db_session_mock):
    """Test Delete User"""
    userId = "U123124234"
    # Simulate an existing user with the same id
    mock_existing_user = mock.MagicMock()
    mock_existing_user.id = userId
    mock_existing_user.nric_FullName = "DANIEL ANG"
    mock_existing_user.email = "daniel@example.com"
    mock_existing_user.roleName = "DOCTOR"
    mock_existing_user.profilePicture = None
    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_existing_user

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

    result = user_crud.delete_user(db_session_mock, userId, current_user)
    #Assert
    assert result == mock_existing_user

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["user_full_name"] == "Admin User"
    assert kwargs["role"] == "ADMIN"
    assert kwargs["entity_id"] == userId
    assert kwargs["table"] == "user"
    assert kwargs["original_data"]["nric_FullName"] == "DANIEL ANG"


@mock.patch("app.crud.user_crud.log_crud_action")
def test_delete_user_invalid_userId(mock_log_crud, db_session_mock):
    """Test Delete User, invalid/not found user"""
    userId = "U123124234"
    # Simulate no user exists with the given id
    db_session_mock.query(User).filter(User.id == userId).first.return_value = None

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

    # Assert that an HTTPException is raised
    with pytest.raises(HTTPException):
        user_crud.delete_user(db_session_mock, userId, current_user)
    mock_log_crud.assert_not_called()



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

@mock.patch("app.crud.user_crud.log_crud_action")
def test_admin_soft_delete_user_success(mock_log_crud, db_session_mock):
    userId = "user123"
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.roleName = "USER"
    mock_user.isDeleted = False
    mock_user.nric_FullName = "SAMPLE USER"

    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_user

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

    result = user_crud.soft_delete_admin_user(db_session_mock, userId, current_user)

    db_session_mock.commit.assert_called_once()
    assert result.isDeleted is True

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["user_full_name"] == "Admin User"
    assert kwargs["role"] == "ADMIN"
    assert kwargs["entity_id"] == userId
    assert kwargs["original_data"] == {"isDeleted": False, "status": "active"}
    assert kwargs["updated_data"] == {"isDeleted": True, "status": "deleted"}


@mock.patch("app.crud.user_crud.log_crud_action")
def test_admin_soft_delete_user_not_found(mock_log_crud, db_session_mock):
    userId = "nonexistent"
    db_session_mock.query(User).filter(User.id == userId).first.return_value = None

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

    with pytest.raises(HTTPException) as exc:
        user_crud.soft_delete_admin_user(db_session_mock, userId, current_user)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"
    mock_log_crud.assert_not_called()


@mock.patch("app.crud.user_crud.log_crud_action")
def test_admin_cannot_soft_delete_other_admin(mock_log_crud, db_session_mock):
    userId = "admin456"

    # Simulate that the user to delete is an ADMIN
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.roleName = "ADMIN"
    mock_user.isDeleted = False

    db_session_mock.query(User).filter(User.id == userId).first.return_value = mock_user

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

    with pytest.raises(HTTPException) as exc:
        user_crud.soft_delete_admin_user(db_session_mock, userId, current_user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Cannot delete another admin"
    mock_log_crud.assert_not_called()



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


@mock.patch("app.crud.user_crud.log_crud_action")
def test_update_user_Admin_logs_actor(mock_log_crud, db_session_mock):
    from app.schemas.user import UserUpdate_Admin

    userId = "U123124234"
    mock_user = mock.MagicMock()
    mock_user.id = userId
    mock_user.preferredName = "Old Name"
    mock_user.nric_FullName = "DANIEL TAN"
    db_session_mock.query(User).filter(User.id == userId).first.side_effect = [mock_user, mock_user]

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}
    payload = UserUpdate_Admin(preferredName="New Name")

    result = user_crud.update_user_Admin(db=db_session_mock, userId=userId, user=payload, current_user=current_user)

    db_session_mock.execute.assert_called_once()
    db_session_mock.commit.assert_called_once()
    assert result is mock_user

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["user_full_name"] == "Admin User"
    assert kwargs["role"] == "ADMIN"
    assert kwargs["entity_id"] == userId
    assert kwargs["table"] == "user"


@mock.patch("app.crud.user_crud.log_crud_action")
def test_update_users_role_admin_logs_actor(mock_log_crud, db_session_mock):
    userId = "U123124234"

    mock_user_before = mock.MagicMock()
    mock_user_before.id = userId
    mock_user_before.roleName = "DOCTOR"

    mock_user_after = mock.MagicMock()
    mock_user_after.id = userId
    mock_user_after.roleName = "NURSE"
    mock_user_after.nric_FullName = "DANIEL TAN"

    db_session_mock.query(User).filter(User.id == userId).first.side_effect = [
        mock_user_before,
        mock_user_after,
    ]

    current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

    result = user_crud.update_users_role_admin(db=db_session_mock, userId=userId, roleName="NURSE", current_user=current_user)

    assert result is mock_user_after
    db_session_mock.commit.assert_called_once()

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["original_data"] == {"roleName": "DOCTOR"}
    assert kwargs["updated_data"] == {"roleName": "NURSE"}
