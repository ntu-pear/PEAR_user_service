import asyncio
from io import BytesIO
from unittest import mock

import pytest
from PIL import Image

from app.routers import admin_router
from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


class FakeUploadFile:
    def __init__(self, content: bytes, filename: str = "avatar.png", content_type: str = "image/png"):
        self._content = content
        self.filename = filename
        self.content_type = content_type
        # validate_profile_picture_format() checks size via file.file
        # (mirrors the real UploadFile's underlying SpooledTemporaryFile),
        # padded here to clear the service's 5 KB minimum-size check.
        self.file = BytesIO(content.ljust(6144, b"\0"))

    async def read(self):
        return self._content


def _make_png_bytes() -> bytes:
    img = Image.new("RGB", (10, 10), color=(0, 255, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@mock.patch("app.routers.admin_router.log_crud_action")
@mock.patch("app.routers.admin_router.cloudinary.uploader.destroy")
@mock.patch("app.routers.admin_router.cloudinary.uploader.upload")
def test_admin_upload_profile_picture_logs_admin_actor(mock_upload, mock_destroy, mock_log_crud, db_session_mock):
    mock_upload.return_value = {"secure_url": "https://cdn.example.com/new.jpg"}

    mock_user = mock.MagicMock()
    mock_user.id = "U99999"
    mock_user.nric_FullName = "TARGET USER"
    mock_user.profilePicture = "https://cdn.example.com/old.jpg"

    with mock.patch.object(admin_router.crud_user, "get_user", return_value=mock_user):
        current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}
        fake_file = FakeUploadFile(_make_png_bytes())

        result = asyncio.run(
            admin_router.upload_profile_picture(
                userId="U99999", file=fake_file, current_user=current_user, db=db_session_mock
            )
        )

    assert result == {"message": "Profile picture uploaded successfully", "file_url": "https://cdn.example.com/new.jpg"}

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["user_full_name"] == "Admin User"
    assert kwargs["role"] == "ADMIN"
    assert kwargs["entity_id"] == "U99999"
    assert kwargs["original_data"] == {"profilePicture": "https://cdn.example.com/old.jpg"}
    assert kwargs["updated_data"] == {"profilePicture": "https://cdn.example.com/new.jpg"}


@mock.patch("app.routers.admin_router.log_crud_action")
@mock.patch("app.routers.admin_router.cloudinary.uploader.destroy")
def test_admin_delete_profile_picture_logs_admin_actor(mock_destroy, mock_log_crud, db_session_mock):
    mock_user = mock.MagicMock()
    mock_user.id = "U99999"
    mock_user.nric_FullName = "TARGET USER"
    mock_user.profilePicture = "https://cdn.example.com/old.jpg"

    with mock.patch.object(admin_router.crud_user, "get_user", return_value=mock_user):
        current_user = {"userId": "admin1", "fullName": "Admin User", "roleName": "ADMIN", "email": "admin@example.com"}

        result = admin_router.delete_profile_picture(userId="U99999", current_user=current_user, db=db_session_mock)

    assert result == {"message": "Profile picture deleted successfully"}
    assert mock_user.profilePicture is None

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "admin1"
    assert kwargs["entity_id"] == "U99999"
    assert kwargs["original_data"] == {"profilePicture": "https://cdn.example.com/old.jpg"}
