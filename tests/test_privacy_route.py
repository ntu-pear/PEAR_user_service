import pytest
from unittest import mock
from datetime import datetime
from app.crud.privacy_level_setting_crud import get_privacy_level_setting_by_user, get_privacy_level_settings_by_user, get_privacy_level_setting_by_role, get_privacy_level_settings_by_role, create_privacy_level_setting, update_privacy_level_setting, delete_privacy_level_setting
from app.schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSetting, PrivacyLevelSettingUpdate
from app.schemas.role import RoleRead
from app.models.privacy_level_setting_model import PrivacyLevelSetting as PrivacyLevelSettingModel, PrivacyStatus
from app.models.role_model import Role as RoleModel

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

# Mocking the relevant models
@mock.patch("app.models.privacy_level_setting_model.PrivacyLevelSetting")
def test_get_privacy_level_setting_by_user(db_session_mock, Read_Privacy_Level):
    """Test case for retrieving privacy level setting by ID."""
    # Arrange
    db_session_mock.query.return_value.filter.return_value.first.return_value = Read_Privacy_Level

    # Act
    result = get_privacy_level_setting_by_user(db_session_mock, Read_Privacy_Level.id)

    # Assert
    db_session_mock.query.assert_called_once_with(PrivacyLevelSettingModel)
    db_session_mock.query.return_value.filter.assert_called_once()
    
    assert result.id == Read_Privacy_Level.id
    assert result.active == Read_Privacy_Level.active
    assert result.privacyLevelSensitive == Read_Privacy_Level.privacyLevelSensitive
    
def test_get_privacy_level_settings_by_user(db_session_mock, Read_Privacy_Levels):
    """Test case for retrieving all privacy level settings by User"""
    # Arrange
    db_session_mock.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = Read_Privacy_Levels

    # Act
    result = get_privacy_level_settings_by_user(db_session_mock)

    # Assert
    assert len(result) == len(Read_Privacy_Levels)
    assert result[0].id == Read_Privacy_Levels[0].id
    assert result[0].privacyLevelSensitive == Read_Privacy_Levels[0].privacyLevelSensitive
    assert result[1].id == Read_Privacy_Levels[1].id
    assert result[1].privacyLevelSensitive == Read_Privacy_Levels[1].privacyLevelSensitive

def test_get_privacy_level_setting_by_role(db_session_mock, Read_Role):
    """Test case for retrieving privacy level setting by Role."""
    # Arrange
    db_session_mock.query.return_value.filter.return_value.first.return_value = Read_Role

    # Act
    result = get_privacy_level_setting_by_role(db_session_mock, Read_Role.id)

    # Assert
    db_session_mock.query.assert_called_once_with(RoleModel)
    db_session_mock.query.return_value.filter.assert_called_once()
    
    assert result.id == Read_Role.id
    assert result.active == Read_Role.active
    assert result.privacyLevelSensitive == Read_Role.privacyLevelSensitive
    
def test_get_privacy_level_settings_by_role(db_session_mock, Read_Roles):
    """Test case for retrieving all privacy level settings by Role"""
    # Arrange
    db_session_mock.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = Read_Roles

    # Act
    result = get_privacy_level_settings_by_role(db_session_mock)

    # Assert
    assert len(result) == len(Read_Roles)
    assert result[0].id == Read_Roles[0].id
    assert result[0].privacyLevelSensitive == Read_Roles[0].privacyLevelSensitive
    assert result[1].id == Read_Roles[1].id
    assert result[1].privacyLevelSensitive == Read_Roles[1].privacyLevelSensitive
    

def test_create_privacy_level_setting(db_session_mock, Create_Privacy_Level):
    """Test Case for creating Privacy Level"""
    # Arrange
    patient_id = 'Pc8ec553e5f0'
    
    # Act
    result = create_privacy_level_setting(db_session_mock, patient_id, Create_Privacy_Level, 1)
    
    # Assert
    db_session_mock.add.assert_called_once_with(result)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.id == 'Pc8ec553e5f0'
    assert result.active == 1
    assert result.privacyLevelSensitive == PrivacyStatus.LOW
    
def test_update_privacy_level_setting(db_session_mock, Read_Privacy_Level, Update_Privacy_Level):
    """Test Case for updating Privacy Level"""

    # Arrange
    modified_by = 2
    mock_patient = Read_Privacy_Level
    mock_patient_id = Read_Privacy_Level.id
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_patient
    
    # Act
    result = update_privacy_level_setting(db_session_mock, mock_patient_id, Update_Privacy_Level, modified_by)
    
    #Assert
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.active == 0
    assert result.privacyLevelSensitive == PrivacyStatus.NONE
    
def test_delete_privacy_level_setting(db_session_mock, Read_Privacy_Level):
    """Test case for deleting Privacy Level."""
    # Arrange
    mock_patient_id = Read_Privacy_Level.id
    db_session_mock.query.return_value.filter.return_value.first.return_value = Read_Privacy_Level
    
    # Act
    result = delete_privacy_level_setting(db_session_mock, mock_patient_id)
    
    #Assert
    assert result.id == mock_patient_id
    
@pytest.fixture
def db_session_mock():
    """Fixture to mock the database session."""
    return get_db_session_mock()

@pytest.fixture
def Read_Privacy_Level():
    """Fixture to provide a mock PrivacyLevelSetting Object."""
    return PrivacyLevelSetting(
        id='Pc8ec553e5f0',
        active=1,
        privacyLevelSensitive=1,
        createdDate=datetime.now(),
        modifiedDate=datetime.now(),
        createdById="1",
        modifiedById="1"
    )

@pytest.fixture
def Read_Privacy_Levels():
    """Fixture to provide a list of mock PrivacyLevelSetting Objects."""
    return [
        PrivacyLevelSetting(
            id='Pc8ec553e5f0',
            active=1,
            privacyLevelSensitive=1,
            createdDate=datetime.now(),
            modifiedDate=datetime.now(),
            createdById="1",
            modifiedById="1"
        ),
        PrivacyLevelSetting(
            id='Pb895f80031b',
            active=1,
            privacyLevelSensitive=2,
            createdDate=datetime.now(),
            modifiedDate=datetime.now(),
            createdById="1",
            modifiedById="1"
        )
    ]
    
@pytest.fixture
def Read_Role():
    """Fixture to provide a mock Role Object."""
    return RoleRead(
        id='ADmin123',
        active=1,
        roleName='ADMIN',
        privacyLevelSensitive=3,
        createdDate=datetime.now(),
        modifiedDate=datetime.now(),
        createdById="1",
        modifiedById="1"
    )

@pytest.fixture
def Read_Roles():
    """Fixture to provide a list of mock Role Objects."""
    return [
        RoleRead(
            id='ADmin123',
            active=1,
            roleName='ADMIN',
            privacyLevelSensitive=3,
            createdDate=datetime.now(),
            modifiedDate=datetime.now(),
            createdById="1",
            modifiedById="1"
        ),
        RoleRead(
            id='Game1234',
            active=1,
            roleName='GAME THERAPIST',
            privacyLevelSensitive=1,
            createdDate=datetime.now(),
            modifiedDate=datetime.now(),
            createdById="1",
            modifiedById="1"
        )
    ]

@pytest.fixture
def Create_Privacy_Level():
    """Fixture to provide a mock PrivacyLevelSettingCreate Object."""
    return PrivacyLevelSettingCreate(
        active=1,
        privacyLevelSensitive=1
    )

@pytest.fixture
def Update_Privacy_Level():
    """Fixture to provide a mock PrivacyLevelSettingCreate Object."""
    return PrivacyLevelSettingCreate(
        active=0,
        privacyLevelSensitive=0
    )