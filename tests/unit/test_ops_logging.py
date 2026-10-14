"""Tests for the shared ops-logging module (app/ops_logging.py)."""
import asyncio
import base64
import json
import logging
import re
from logging.handlers import RotatingFileHandler

import pytest
from fastapi import FastAPI

from app import ops_logging

SERVICE = "patient"
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


class FakeApp:
    def __init__(self):
        self.middleware = []
        self.routes = []

    def add_middleware(self, cls, **kwargs):
        self.middleware.append(cls)

    def add_api_route(self, path, endpoint, **kwargs):
        self.routes.append(path)


def _token(user_id):
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")
    return f"{part({'alg': 'HS256'})}.{part({'sub': json.dumps({'userId': user_id}), 'exp': 9999999999})}.sig"


def _endpoint(status=200, body=b'{"ok": true}', before=None):
    async def app(scope, receive, send):
        if before:
            before()
        await send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": body})
    return app


def _call(app, path="/api/v1/patients/1", method="GET", query=b"", headers=None):
    scope = {"type": "http", "method": method, "path": path, "query_string": query, "headers": headers or []}
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(ops_logging.OpsRequestMiddleware(app)(scope, receive, send))
    return sent


def _lines(log_dir):
    files = list(log_dir.glob("ops_*.log"))
    if not files:
        return []
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


@pytest.fixture
def ops(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_LOGGING", "true")
    monkeypatch.setenv("OPS_ENVIRONMENT", "test")
    monkeypatch.delenv("OPS_DEBUG_ROUTES", raising=False)
    assert ops_logging.setup_ops_logging(FakeApp(), service=SERVICE, log_dir=str(tmp_path)) is True
    yield tmp_path
    ops_logging.shutdown_ops_logging()


@pytest.mark.parametrize("value,expected", [
    ("true", True), ("1", True), ("YES", True), (" On ", True),
    ("", False), ("false", False), ("0", False), ("off", False), ("enabled", False),
])
def test_flag_parsing(monkeypatch, value, expected):
    monkeypatch.setenv("OPS_LOGGING", value)
    assert ops_logging.is_enabled() is expected


def test_setup_does_nothing_when_flag_off(tmp_path, monkeypatch):
    monkeypatch.delenv("OPS_LOGGING", raising=False)
    root_handlers = list(logging.getLogger().handlers)
    fake = FakeApp()
    assert ops_logging.setup_ops_logging(fake, service=SERVICE, log_dir=str(tmp_path / "logs")) is False
    assert fake.middleware == [] and fake.routes == []
    assert logging.getLogger().handlers == root_handlers
    assert not (tmp_path / "logs").exists()
    assert ops_logging.outbound_headers() == {}
    ops_logging.auth_event("login_failed", reason="unknown_user")  # no-op, must not raise


def test_handler_is_size_capped_and_named_per_process(ops):
    handler = ops_logging._state["handler"]
    assert isinstance(handler, RotatingFileHandler)
    assert handler.maxBytes == 50 * 1024 * 1024 and handler.backupCount == 5
    name = handler.baseFilename.replace("\\", "/").split("/")[-1]
    assert re.fullmatch(rf"ops_{SERVICE}_[A-Za-z0-9.-]+-\d+\.log", name)


def test_setup_twice_adds_no_second_handler(ops):
    ops_logger = logging.getLogger(ops_logging.OPS_LOGGER_NAME)
    before = (len(ops_logger.handlers), len(logging.getLogger().handlers))
    assert ops_logging.setup_ops_logging(FakeApp(), service=SERVICE, log_dir=str(ops)) is True
    assert (len(ops_logger.handlers), len(logging.getLogger().handlers)) == before


def test_request_line_shape_and_query_masking(ops):
    _call(
        _endpoint(),
        query=b"name=John+Tan&mask=false&NRIC=S1234567A&pageSize=5&userEmail=",
        headers=[(b"authorization", f"Bearer {_token('U7')}".encode())],
    )
    (line,) = _lines(ops)
    assert line["schema"] == "pear-app-v1"
    assert line["ops_type"] == "request"
    assert line["service"] == SERVICE and line["environment"] == "test"
    assert line["method"] == "GET" and line["path"] == "/api/v1/patients/1" and line["status"] == 200
    assert line["query"] == "name=***&mask=false&NRIC=***&pageSize=5&userEmail=***"
    assert "John" not in json.dumps(line) and "S1234567A" not in json.dumps(line)
    assert line["user_id"] == "U7"
    assert line["level"] == "INFO"
    assert isinstance(line["duration_ms"], float)
    assert re.fullmatch(UUID, line["request_id"])
    assert line["timestamp"].endswith("Z")
    assert not {"user", "table", "action", "log_text", "log_type"} & set(line)


def test_incoming_request_id_is_reused_and_echoed(ops):
    sent = _call(_endpoint(), headers=[(b"x-request-id", b"trace-abc.123")])
    assert _lines(ops)[0]["request_id"] == "trace-abc.123"
    assert (b"x-request-id", b"trace-abc.123") in sent[0]["headers"]


@pytest.mark.parametrize("bad", [b"has space", b"x" * 65, b"a\nb", b'{"json":1}', b""])
def test_unsafe_request_id_is_replaced(ops, bad):
    sent = _call(_endpoint(), headers=[(b"x-request-id", bad)])
    request_id = _lines(ops)[0]["request_id"]
    assert re.fullmatch(UUID, request_id)
    assert (b"x-request-id", request_id.encode()) in sent[0]["headers"]


@pytest.mark.parametrize("method,path", [
    ("GET", "/health"), ("GET", "/health/"), ("GET", "/docs"), ("GET", "/openapi.json"),
    ("GET", "/redoc"), ("GET", "/"), ("OPTIONS", "/api/v1/patients/1"),
])
def test_machine_traffic_is_not_logged(ops, method, path):
    _call(_endpoint(), path=path, method=method)
    assert _lines(ops) == []


def test_token_verifier_calls_are_skipped_but_browser_calls_are_logged(ops):
    _call(_endpoint(), path="/api/v1/current_user/", headers=[(b"user-agent", b"python-httpx/0.28.1")])
    _call(_endpoint(), path="/api/v1/current_user/", headers=[(b"user-agent", b"python-requests/2.32.4")])
    assert _lines(ops) == []
    _call(_endpoint(), path="/api/v1/current_user/", headers=[(b"user-agent", b"Mozilla/5.0")])
    assert len(_lines(ops)) == 1


def test_sensitive_path_values_are_masked(ops):
    _call(_endpoint(), path="/api/v1/internal/user/check-nric/S1234567A")
    _call(_endpoint(), path="/api/v1/admin/get_email/someone@example.com")
    _call(_endpoint(), path="/api/v1/admin/get_nric/U12")
    paths = [line["path"] for line in _lines(ops)]
    assert paths == [
        "/api/v1/internal/user/check-nric/***",
        "/api/v1/admin/get_email/***",
        "/api/v1/admin/get_nric/U12",
    ]


@pytest.mark.parametrize("status", [401, 403])
def test_401_and_403_write_an_auth_event(ops, status):
    _call(
        _endpoint(status=status, body=b'{"detail": "Invalid or expired session", "code": "X"}'),
        headers=[(b"authorization", f"Bearer {_token('U9')}".encode())],
    )
    request_line, auth_line = _lines(ops)
    assert request_line["ops_type"] == "request" and request_line["status"] == status
    assert request_line["level"] == "WARNING"
    assert auth_line["ops_type"] == "auth"
    assert auth_line["auth_event"] == f"http_{status}"
    assert auth_line["reason"] == "Invalid or expired session"
    assert auth_line["user_id"] == "U9" and auth_line["status"] == status
    assert auth_line["request_id"] == request_line["request_id"]


def test_401_with_a_non_json_body_still_logs_without_reason(ops):
    _call(_endpoint(status=401, body=b"Unauthorized"))
    auth_line = _lines(ops)[1]
    assert auth_line["auth_event"] == "http_401" and "reason" not in auth_line


def test_unhandled_exception_is_logged_and_re_raised(ops):
    async def broken(scope, receive, send):
        raise RuntimeError("boom 42")

    with pytest.raises(RuntimeError, match="boom 42"):
        _call(broken)
    error_line, request_line = _lines(ops)
    assert error_line["ops_type"] == "error" and error_line["level"] == "ERROR"
    assert error_line["exception_type"] == "RuntimeError"
    assert "boom 42" in error_line["stack_trace"]
    assert request_line["status"] == 500
    assert error_line["request_id"] == request_line["request_id"]


def test_existing_warning_and_error_calls_are_captured_with_request_id(ops):
    app_logger = logging.getLogger("tests.ops.some_module")

    def emit():
        app_logger.info("routine detail")  # below WARNING: never an ops line
        app_logger.error("database write failed")

    _call(_endpoint(before=emit))
    lines = _lines(ops)
    errors = [line for line in lines if line["ops_type"] == "error"]
    request = next(line for line in lines if line["ops_type"] == "request")
    assert [line["message"] for line in errors] == ["database write failed"]
    assert errors[0]["logger"] == "tests.ops.some_module"
    assert errors[0]["request_id"] == request["request_id"]


def test_audit_shaped_records_are_never_written(ops):
    logging.getLogger("tests.ops.audit_shaped").warning(
        {"entity_id": 1},
        extra={"user": "1", "user_full_name": "A", "table": "T", "action": "create", "log_text": "m"},
    )
    assert _lines(ops) == []


def test_extra_audit_fields_never_leak_into_an_ops_line(ops):
    logging.getLogger("tests.ops.partial").error("Invalid token format", extra={"table": "auth", "action": "decode"})
    (line,) = _lines(ops)
    assert line["message"] == "Invalid token format"
    assert not {"user", "table", "action", "log_text"} & set(line)


def test_token_verifier_events_become_auth_lines(ops):
    logging.getLogger("pear.auth").warning(
        "Auth would_reject: token_rejected on /api/v1/patients/1 (claimed user U1, role DOCTOR)",
        extra={
            "auth_event": "would_reject",
            "auth_reason": "token_rejected",
            "auth_endpoint": "/api/v1/patients/1",
            "auth_claimed_user_id": "U1",
            "auth_claimed_role": "DOCTOR",
        },
    )
    (line,) = _lines(ops)
    assert line["ops_type"] == "auth" and line["auth_event"] == "would_reject"
    assert line["reason"] == "token_rejected"
    assert line["path"] == "/api/v1/patients/1" and line["user_id"] == "U1"


def test_auth_event_helper(ops):
    ops_logging.auth_event("login_failed", reason="wrong_password", user_id="U3")
    (line,) = _lines(ops)
    assert line["ops_type"] == "auth" and line["auth_event"] == "login_failed"
    assert line["reason"] == "wrong_password" and line["user_id"] == "U3"
    assert line["level"] == "WARNING" and line["message"] == "Auth login_failed: wrong_password"
    assert not {"user", "table", "action", "log_text"} & set(line)


ECS_OBJECT_FIELDS = {"event", "log", "host", "agent", "ecs", "input", "fields", "error", "file", "process"}


def test_lines_never_use_a_top_level_key_that_is_an_ecs_object(ops):
    ops_logging.auth_event("login_failed", reason="wrong_password", user_id="U3")
    logging.getLogger("pear.auth").warning(
        "Auth would_reject", extra={"auth_event": "would_reject", "auth_reason": "r"}
    )
    for line in _lines(ops):
        assert line["ops_type"] == "auth" and "auth_event" in line
        assert not ECS_OBJECT_FIELDS & set(line)


def test_auth_event_reason_is_truncated(ops):
    ops_logging.auth_event("refresh_failed", reason="x" * 5000)
    assert len(_lines(ops)[0]["reason"]) == 200


def test_outbound_headers_carry_the_current_request_id(ops):
    seen = {}
    _call(_endpoint(before=lambda: seen.update(ops_logging.outbound_headers())), headers=[(b"x-request-id", b"rid-1")])
    assert seen == {"X-Request-ID": "rid-1"}
    assert ops_logging.outbound_headers() == {}  # outside a request


def test_a_failing_hook_never_breaks_the_request(ops, monkeypatch):
    def explode(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(ops_logging, "_log_request", explode)
    sent = _call(_endpoint())
    assert sent[0]["status"] == 200 and sent[1]["body"] == b'{"ok": true}'


def test_a_failing_formatter_never_raises_into_the_caller(ops, monkeypatch):
    def explode(self, record):
        raise ValueError("bad record")

    monkeypatch.setattr(ops_logging.OpsJsonFormatter, "format", explode)
    monkeypatch.setattr(logging, "raiseExceptions", False)
    logging.getLogger("tests.ops.anything").error("still fine")  # must not raise
    ops_logging.auth_event("login_failed", reason="unknown_user")  # must not raise
    sent = _call(_endpoint())
    assert sent[0]["status"] == 200


def test_malformed_authorization_header_is_ignored(ops):
    _call(_endpoint(), headers=[(b"authorization", b"Bearer not.a-jwt")])
    assert _lines(ops)[0]["user_id"] is None


def test_debug_routes_need_their_own_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_LOGGING", "true")
    monkeypatch.delenv("OPS_DEBUG_ROUTES", raising=False)
    plain = FakeApp()
    debug = FakeApp()
    try:
        ops_logging.setup_ops_logging(plain, service=SERVICE, log_dir=str(tmp_path))
        monkeypatch.setenv("OPS_DEBUG_ROUTES", "true")
        ops_logging.setup_ops_logging(debug, service=SERVICE, log_dir=str(tmp_path))
    finally:
        ops_logging.shutdown_ops_logging()
    assert plain.routes == []
    assert debug.routes == ["/ops-debug/error", "/ops-debug/forbidden"]


def test_real_fastapi_app_sync_endpoint_sees_the_request_id(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_LOGGING", "true")
    api = FastAPI()

    @api.get("/echo")
    def echo():
        return ops_logging.outbound_headers()

    assert ops_logging.setup_ops_logging(api, service=SERVICE, log_dir=str(tmp_path)) is True
    scope = {
        "type": "http", "method": "GET", "path": "/echo", "raw_path": b"/echo", "query_string": b"",
        "headers": [(b"x-request-id", b"rid-sync"), (b"host", b"test")], "scheme": "http",
        "server": ("test", 80), "client": ("127.0.0.1", 1234), "root_path": "", "http_version": "1.1",
    }
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    try:
        asyncio.run(api(scope, receive, send))
    finally:
        ops_logging.shutdown_ops_logging()
    assert sent[0]["status"] == 200
    assert json.loads(sent[1]["body"]) == {"X-Request-ID": "rid-sync"}
    assert _lines(tmp_path)[0]["path"] == "/echo"


# ------------------------------------------------------------ fix round --

def test_scrub_replaces_nric_email_and_sql_tails():
    scrub = ops_logging._scrub
    assert scrub("bad s1234567a and T7654321Z here") == "bad *** and *** here"
    assert scrub("mail someone@example.com now") == "mail *** now"
    assert scrub("fine S12345678A") == "fine S12345678A"
    out = scrub("boom [SQL: SELECT * FROM T WHERE nric=?]\n[parameters: ('S1234567A',)]\n(Background)")
    assert out == "boom" and "SELECT" not in out and "S1234567A" not in out


def test_exception_text_is_scrubbed_in_message_and_stack(ops):
    async def broken(scope, receive, send):
        raise RuntimeError("no patient S1234567A for jane@example.com [parameters: ('S1234567A',)]")

    with pytest.raises(RuntimeError):
        _call(broken)
    error_line = _lines(ops)[0]
    dumped = json.dumps(error_line)
    assert "S1234567A" not in dumped and "jane@example.com" not in dumped and "parameters" not in dumped
    assert "***" in error_line["stack_trace"]


def test_logged_error_message_is_scrubbed(ops):
    logging.getLogger("tests.ops.pii").error("lookup failed for %s", "S1234567A")
    assert _lines(ops)[0]["message"] == "lookup failed for ***"


def test_401_detail_is_scrubbed(ops):
    _call(_endpoint(status=401, body=b'{"detail": "No account for jane@example.com"}'))
    auth_line = _lines(ops)[1]
    assert auth_line["reason"] == "No account for ***"
    assert "jane@example.com" not in json.dumps(_lines(ops))


def test_auth_event_reason_is_scrubbed_and_path_masked(ops):
    ops_logging.auth_event(
        "login_failed", reason="unknown S1234567A", method="GET", path="/api/v1/admin/get_email/a@b.com", status=401
    )
    (line,) = _lines(ops)
    assert line["reason"] == "unknown ***"
    assert line["path"] == "/api/v1/admin/get_email/***"


@pytest.mark.parametrize("query,expected", [
    ("S1234567A", "***"),
    ("page=1&S1234567A&size=5", "page=1&***&size=5"),
    ("a=1;nric=S1234567A", "***"),
    ("page=1;x=2&size=5", "***&size=5"),
    ("tag=a&tag=b&name=x&name=y", "tag=a&tag=b&name=***&name=***"),
    ("%4Eame=Jo%20Tan&n%61me=Al", "Name=***&name=***"),
    ("NaMe=x&eMAIL=y&PhOnE=z&TOKEN=t&PassWord=p", "NaMe=***&eMAIL=***&PhOnE=***&TOKEN=***&PassWord=***"),
    ("q=S1234567A&r=jane%40example.com", "q=***&r=***"),
])
def test_mask_query_edge_cases(query, expected):
    assert ops_logging.mask_query(query) == expected


def test_setup_failure_part_way_leaves_nothing_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_LOGGING", "true")
    root_handlers = list(logging.getLogger().handlers)

    class Exploding(FakeApp):
        def add_middleware(self, cls, **kwargs):
            raise RuntimeError("cannot add middleware")

    try:
        assert ops_logging.setup_ops_logging(Exploding(), service=SERVICE, log_dir=str(tmp_path)) is False
        assert ops_logging._state["installed"] is False and ops_logging._state["handler"] is None
        assert logging.getLogger().handlers == root_handlers
        assert logging.getLogger(ops_logging.OPS_LOGGER_NAME).handlers == []
        assert ops_logging.outbound_headers() == {}
    finally:
        ops_logging.shutdown_ops_logging()


def test_setup_is_idempotent_per_app(tmp_path, monkeypatch):
    monkeypatch.setenv("OPS_LOGGING", "true")
    monkeypatch.setenv("OPS_DEBUG_ROUTES", "true")
    app = FakeApp()
    other = FakeApp()
    try:
        assert ops_logging.setup_ops_logging(app, service=SERVICE, log_dir=str(tmp_path)) is True
        assert ops_logging.setup_ops_logging(app, service=SERVICE, log_dir=str(tmp_path)) is True
        assert ops_logging.setup_ops_logging(other, service=SERVICE, log_dir=str(tmp_path)) is True
    finally:
        ops_logging.shutdown_ops_logging()
    assert app.middleware == [ops_logging.OpsRequestMiddleware]
    assert app.routes == ["/ops-debug/error", "/ops-debug/forbidden"]
    assert other.middleware == [ops_logging.OpsRequestMiddleware]


def test_no_response_started_logs_null_status(ops):
    async def silent(scope, receive, send):
        return

    _call(silent)
    (line,) = _lines(ops)
    assert line["ops_type"] == "request" and "status" in line and line["status"] is None
    assert line["level"] == "INFO"


def test_client_disconnect_is_not_an_unhandled_error(ops):
    from starlette.requests import ClientDisconnect

    async def gone(scope, receive, send):
        raise ClientDisconnect()

    with pytest.raises(ClientDisconnect):
        _call(gone)
    (line,) = _lines(ops)
    assert line["ops_type"] == "request" and line["status"] is None


def test_a_file_handler_that_cannot_write_never_breaks_the_request(ops, monkeypatch):
    def disk_full(record):
        raise OSError("No space left on device")

    monkeypatch.setattr(ops_logging._state["handler"], "emit", disk_full)
    monkeypatch.setattr(logging, "raiseExceptions", False)
    sent = _call(_endpoint(before=lambda: logging.getLogger("tests.ops.full").error("x")))
    assert sent[0]["status"] == 200 and sent[1]["body"] == b'{"ok": true}'
    _call(_endpoint(status=403))