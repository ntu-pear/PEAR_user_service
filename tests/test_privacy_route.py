import pytest
from unittest import mock
from app.crud.privacy_level_setting_crud import create_privacy_level_setting, update_privacy_level_setting
from app.schemas.privacy_level_setting import PrivacyLevelSettingCreate, PrivacyLevelSettingUpdate

from fastapi import HTTPException, status

# Import your mock_db from tests/utils
from tests.utils.mock_db import get_db_session_mock

# Mocking the relevant models
#@mock.patch("app.models.privacy_level_setting_model.PrivacyLevelSetting")
def test_create_privacy_level_setting(db_session_mock, Create_Privacy_Level):
    """Test Case for creating Privacy Level"""
    #Act
    result = create_privacy_level_setting(db_session_mock, Create_Privacy_Level)
    # Assert
    db_session_mock.add.assert_called_once_with(result)
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once_with(result)

    assert result.privacyLevelSensitive == 1
    assert result.privacyLevelNonSensitive == 1
    
@pytest.fixture
def db_session_mock():
    """Fixture to mock the database session."""
    return get_db_session_mock()

@pytest.fixture
def Create_Privacy_Level():
    """Fixture to provide a mock Role Object."""
    from app.models.role_model import Role
    from app.models.user_model import User
    
    return PrivacyLevelSettingCreate(
        roleId="1",
        privacyLevelSensitive=1,
        privacyLevelNonSensitive=1,
        Role="ADMIN"
    )