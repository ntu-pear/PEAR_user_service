import pytest
from unittest import mock
from datetime import datetime
from app.crud.privacy_level_setting_crud import get_privacy_level_setting_by_user, get_privacy_level_settings_by_user, get_privacy_level_setting_by_role, get_privacy_level_settings_by_role, create_privacy_level_setting, update_privacy_level_setting, delete_privacy_level_setting
from app.schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSetting, PrivacyLevelSettingUpdate
from app.models.privacy_level_setting_model import PrivacyStatus

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

# Mocking the relevant models
#@mock.patch("app.models.privacy_level_setting_model.PrivacyLevelSetting")
# def test_get_privacy_level_setting_by_user(db_session_mock, Read_Privacy_Level):
#     """Test case for retrieving privacy level setting by ID."""
#     db_session_mock.query.return_value.filter.return_value.first.return_value = mock_results

#     # Act
#     result = get_privacy_level_setting_by_user(db_session_mock, 'Pc8ec553e5f0')

#     # Assert
#     db_session_mock.query.assert_called_once_with(result)
#     db_session_mock.query.return_value.filter.assert_called_once()
    
#     assert result.id == mock_results.id
#     assert result.active == mock_results.active
#     assert result.privacyLevelSensitive == mock_results.privacyLevelSensitive
    

def test_create_privacy_level_setting(db_session_mock, Create_Privacy_Level):
    """Test Case for creating Privacy Level"""
    # Act
    result = create_privacy_level_setting(db_session_mock, 'Pc8ec553e5f0', Create_Privacy_Level, 1)
    # Assert
    db_session_mock.add.assert_called_once_with(result)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.id == 'Pc8ec553e5f0'
    assert result.active == 1
    assert result.privacyLevelSensitive == PrivacyStatus.LOW
    
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
def Create_Privacy_Level():
    """Fixture to provide a mock PrivacyLevelSettingCreate Object."""
    return PrivacyLevelSettingCreate(
        active=1,
        privacyLevelSensitive=1
    )