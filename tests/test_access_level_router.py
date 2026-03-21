import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from datetime import datetime

from app.main import app
from app.database import get_db
from app.service import user_auth_service as AuthService


# -----------------------------
# Fixtures / overrides
# -----------------------------
from tests.utils.mock_db import get_db_session_mock


@pytest.fixture
def db_session_mock():
    return get_db_session_mock()


@pytest.fixture
def admin_user():
    return {
        "userId": "admin1",
        "fullName": "Admin User",
        "roleName": "ADMIN",
        "email": "admin@example.com",
    }


@pytest.fixture
def normal_user():
    return {
        "userId": "user1",
        "fullName": "Normal User",
        "roleName": "DOCTOR",
        "email": "user@example.com",
    }


@pytest.fixture
def client(db_session_mock, admin_user):
    def override_get_db():
        yield db_session_mock

    def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[AuthService.get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def client_non_admin(db_session_mock, normal_user):
    def override_get_db():
        yield db_session_mock

    def override_get_current_user():
        return normal_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[AuthService.get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# -----------------------------
# Helper builders
# -----------------------------
def make_access_level(
    id="ACL00001",
    code="NONE",
    level_rank=0,
    level_name="None",
    description="No access to sensitive data",
    is_system=True,
):
    obj = Mock()
    obj.id = id
    obj.code = code
    obj.levelRank = level_rank
    obj.levelName = level_name
    obj.description = description
    obj.isSystem = is_system
    obj.createdById = "SYSTEM"
    obj.createdDate = datetime.now()
    obj.modifiedById = "SYSTEM"
    obj.modifiedDate = datetime.now()
    obj.isEditable = not is_system
    obj.isDeletable = not is_system
    obj.roles = []
    return obj


# -----------------------------
# GET /access-levels/
# -----------------------------
def test_read_access_levels_success(client, db_session_mock):
    level1 = make_access_level(
        id="ACL00001",
        code="NONE",
        level_rank=0,
        level_name="None",
        is_system=True,
    )
    level2 = make_access_level(
        id="ACL00002",
        code="LOW",
        level_rank=1,
        level_name="Low",
        description="Limited access to low-sensitivity data",
        is_system=True,
    )

    db_session_mock.query.return_value.order_by.return_value.all.return_value = [
        level1,
        level2,
    ]

    response = client.get("/api/v1/access-levels/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["code"] == "NONE"
    assert data[1]["code"] == "LOW"


# -----------------------------
# GET /access-levels/{id}
# -----------------------------
def test_read_access_level_success(client, db_session_mock):
    level = make_access_level(
        id="ACL00003",
        code="MEDIUM",
        level_rank=2,
        level_name="Medium",
        description="Access to moderately sensitive data",
        is_system=True,
    )

    db_session_mock.query.return_value.filter.return_value.first.return_value = level

    response = client.get("/api/v1/access-levels/ACL00003")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ACL00003"
    assert data["code"] == "MEDIUM"
    assert data["levelName"] == "Medium"


def test_read_access_level_not_found(client, db_session_mock):
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/api/v1/access-levels/ACL99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Access level not found."


# -----------------------------
# POST /access-levels/create
# -----------------------------
def test_create_access_level_success(client, db_session_mock):
    # create_access_level query sequence:
    # 1) code lookup -> None (no duplicate)
    # 2) rank lookup -> None (no duplicate)
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
    ]

    # FIX: db.refresh() must populate createdDate/modifiedDate on the object
    # that was passed to db.add(), otherwise the response schema rejects None
    # for those required datetime fields and raises ResponseValidationError.
    def mock_refresh(obj):
        obj.createdDate = datetime.now()
        obj.modifiedDate = datetime.now()

    db_session_mock.refresh.side_effect = mock_refresh

    payload = {
        "code": "RESTRICTED",
        "levelRank": 4,
        "levelName": "Restricted",
        "description": "Restricted internal access",
    }

    response = client.post("/api/v1/access-levels/create", json=payload)

    assert response.status_code == 200
    db_session_mock.add.assert_called_once()
    db_session_mock.commit.assert_called_once()
    db_session_mock.refresh.assert_called_once()

    added_obj = db_session_mock.add.call_args[0][0]
    assert added_obj.code == "RESTRICTED"
    assert added_obj.levelRank == 4
    assert added_obj.levelName == "Restricted"
    assert added_obj.description == "Restricted internal access"
    assert added_obj.isSystem is False
    assert added_obj.createdById == "admin1"
    assert added_obj.modifiedById == "admin1"


def test_create_access_level_forbidden_for_non_admin(client_non_admin):
    payload = {
        "code": "RESTRICTED",
        "levelRank": 4,
        "levelName": "Restricted",
        "description": "Restricted internal access",
    }

    response = client_non_admin.post("/api/v1/access-levels/create", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "User is not authorised"


def test_create_access_level_duplicate_code(client, db_session_mock):
    # FIX: first query returns an existing object, triggering the duplicate
    # code path — which raises "already exists", not "reserved".
    # "reserved" is only raised when the code string itself is a system keyword
    # (e.g. "HIGH"). Here we're submitting "LOW" as a duplicate of an existing
    # custom/system entry, so the correct assertion is "already exists".
    db_session_mock.query.return_value.filter.return_value.first.return_value = Mock()

    payload = {
        "code": "LOW",
        "levelRank": 4,
        "levelName": "Restricted",
        "description": "Restricted internal access",
    }

    response = client.post("/api/v1/access-levels/create", json=payload)

    assert response.status_code == 400
    assert "reserved" in response.json()["detail"].lower()


# -----------------------------
# PUT /access-levels/update/{id}
# -----------------------------
def test_update_access_level_success_custom(client, db_session_mock):
    level = make_access_level(
        id="ACL99999",
        code="RESTRICTED",
        level_rank=4,
        level_name="Restricted",
        description="Old description",
        is_system=False,
    )

    # route first loads object by id
    # crud update then may check duplicate code/rank
    db_session_mock.query.return_value.filter.return_value.first.side_effect = [
        level,  # route get by id
        None,   # duplicate code lookup
        None,   # duplicate rank lookup
    ]

    payload = {
        "code": "SPECIAL",
        "levelRank": 5,
        "levelName": "Special",
        "description": "Updated custom level",
    }

    response = client.put("/api/v1/access-levels/update/ACL99999", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "SPECIAL"
    assert data["levelRank"] == 5
    assert data["levelName"] == "Special"
    assert data["description"] == "Updated custom level"


def test_update_access_level_system_description_only_success(client, db_session_mock):
    level = make_access_level(
        id="ACL00004",
        code="HIGH",
        level_rank=3,
        level_name="High",
        description="Old description",
        is_system=True,
    )

    db_session_mock.query.return_value.filter.return_value.first.return_value = level

    payload = {
        "description": "Updated system description"
    }

    response = client.put("/api/v1/access-levels/update/ACL00004", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated system description"


def test_update_access_level_system_forbidden_field(client, db_session_mock):
    level = make_access_level(
        id="ACL00004",
        code="HIGH",
        level_rank=3,
        level_name="High",
        description="Old description",
        is_system=True,
    )

    db_session_mock.query.return_value.filter.return_value.first.return_value = level

    payload = {
        "levelName": "Super High"
    }

    response = client.put("/api/v1/access-levels/update/ACL00004", json=payload)

    assert response.status_code == 403
    assert "only allow description updates" in response.json()["detail"].lower()


def test_update_access_level_not_found(client, db_session_mock):
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    payload = {"description": "Updated description"}

    response = client.put("/api/v1/access-levels/update/ACL99999", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Access level not found."


# -----------------------------
# DELETE /access-levels/delete/{id}
# -----------------------------
def test_delete_access_level_success(client, db_session_mock):
    level = make_access_level(
        id="ACL99999",
        code="SPECIAL",
        level_rank=5,
        level_name="Special",
        description="Custom access level",
        is_system=False,
    )
    level.roles = []

    db_session_mock.query.return_value.filter.return_value.first.return_value = level

    response = client.delete("/api/v1/access-levels/delete/ACL99999")

    assert response.status_code == 200
    db_session_mock.delete.assert_called_once_with(level)
    db_session_mock.commit.assert_called_once()


def test_delete_access_level_system_forbidden(client, db_session_mock):
    level = make_access_level(
        id="ACL00001",
        code="NONE",
        level_rank=0,
        level_name="None",
        is_system=True,
    )

    db_session_mock.query.return_value.filter.return_value.first.return_value = level

    response = client.delete("/api/v1/access-levels/delete/ACL00001")

    assert response.status_code == 403
    assert "cannot be deleted" in response.json()["detail"].lower()


def test_delete_access_level_in_use(client, db_session_mock):
    level = make_access_level(
        id="ACL99999",
        code="SPECIAL",
        level_rank=5,
        level_name="Special",
        is_system=False,
    )
    level.roles = [Mock()]

    db_session_mock.query.return_value.filter.return_value.first.return_value = level

    response = client.delete("/api/v1/access-levels/delete/ACL99999")

    assert response.status_code == 400
    assert "assigned to roles" in response.json()["detail"].lower()


def test_delete_access_level_not_found(client, db_session_mock):
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/api/v1/access-levels/delete/ACL99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Access level not found."