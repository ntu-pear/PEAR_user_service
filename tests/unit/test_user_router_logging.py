import asyncio
from io import BytesIO
from unittest import mock

import pytest
from PIL import Image

from app.routers import user_router

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
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@mock.patch("app.routers.user_router.log_crud_action")
@mock.patch("app.routers.user_router.cloudinary.uploader.destroy")
@mock.patch("app.routers.user_router.cloudinary.uploader.upload")
def test_upload_profile_picture_self_service_logs_actor(mock_upload, mock_destroy, mock_log_crud, db_session_mock):
    mock_upload.return_value = {"secure_url": "https://cdn.example.com/new.jpg"}

    mock_user = mock.MagicMock()
    mock_user.id = "U12345"
    mock_user.nric_FullName = "DANIEL ANG"
    mock_user.profilePicture = "https://cdn.example.com/old.jpg"
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_user

    current_user = {"userId": "U12345", "fullName": "DANIEL ANG", "roleName": "DOCTOR", "email": "d@x.com"}
    fake_file = FakeUploadFile(_make_png_bytes())

    result = asyncio.run(
        user_router.upload_profile_picture(file=fake_file, current_user=current_user, db=db_session_mock)
    )

    assert result == {"message": "Profile picture uploaded successfully", "file_url": "https://cdn.example.com/new.jpg"}

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "U12345"
    assert kwargs["user_full_name"] == "DANIEL ANG"
    assert kwargs["role"] == "DOCTOR"
    assert kwargs["entity_id"] == "U12345"
    assert kwargs["original_data"] == {"profilePicture": "https://cdn.example.com/old.jpg"}
    assert kwargs["updated_data"] == {"profilePicture": "https://cdn.example.com/new.jpg"}


@mock.patch("app.routers.user_router.log_crud_action")
@mock.patch("app.routers.user_router.cloudinary.uploader.destroy")
def test_delete_profile_picture_self_service_logs_actor(mock_destroy, mock_log_crud, db_session_mock):
    mock_user = mock.MagicMock()
    mock_user.id = "U12345"
    mock_user.nric_FullName = "DANIEL ANG"
    mock_user.profilePicture = "https://cdn.example.com/old.jpg"
    db_session_mock.query.return_value.filter.return_value.first.return_value = mock_user

    current_user = {"userId": "U12345", "fullName": "DANIEL ANG", "roleName": "DOCTOR", "email": "d@x.com"}

    result = asyncio.run(
        user_router.delete_profile_picture(current_user=current_user, db=db_session_mock)
    )

    assert result == {"message": "Profile picture deleted successfully"}
    assert mock_user.profilePicture is None

    mock_log_crud.assert_called_once()
    kwargs = mock_log_crud.call_args[1]
    assert kwargs["user"] == "U12345"
    assert kwargs["entity_id"] == "U12345"
    assert kwargs["original_data"] == {"profilePicture": "https://cdn.example.com/old.jpg"}
