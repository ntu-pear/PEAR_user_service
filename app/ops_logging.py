"""Operational logs (errors, requests, auth events) for PEAR services.

Dark by default: nothing in this module does anything unless the OPS_LOGGING
environment variable is on ("true", "1", "yes" or "on", any case). With it
off there is no handler, no middleware, no response header and no new file.

Every line is one JSON object in the "pear-app-v1" shape, written to
logs/ops_<service>_<host>-<pid>.log (50 MB x 5 rotation). A line never
carries user, table, action or log_text, the fields the logging service uses
to find audit entries, so ops lines can never appear in the audit log views.

This file is copied, unchanged, into every PEAR backend service. Keep the
copies identical.
"""
import base64
import contextvars
import json
import logging
import os
import re
import socket
import time
import traceback
import uuid
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional
from urllib.parse import quote_plus, unquote_plus

SCHEMA = "pear-app-v1"
OPS_LOGGER_NAME = "pear.ops"
MAX_BYTES = 50 * 1024 * 1024
BACKUP_COUNT = 5
TRUTHY = frozenset({"true", "1", "yes", "on"})

MASK = "***"
# Query parameters whose name contains one of these words are masked.
SENSITIVE_QUERY_KEYS = ("nric", "email", "phone", "name", "token", "password")
# A path segment that follows one of these segments is a sensitive value,
# e.g. /internal/user/check-nric/{nric} or /admin/get_email/{email}.
SENSITIVE_PATH_PARENTS = frozenset({
    "check-nric",
    "get_guardian",
    "get_email",
    "verify_account",
    "confirm_email",
    "reset_user_password",
})
# Machine traffic: liveness probes and API docs.
EXCLUDED_PATHS = frozenset({
    "/",
    "/health",
    "/healthz",
    "/livez",
    "/readyz",
    "/docs",
    "/docs/oauth2-redirect",
    "/openapi.json",
    "/redoc",
})
# Token-verification calls other services make to User service.
VERIFIER_PATH_SUFFIX = "/current_user"
LIBRARY_USER_AGENTS = ("python-httpx/", "python-requests/")

# Personal data that can turn up in free text (exception messages, 401 details).
NRIC_PATTERN = re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
# SQLAlchemy appends the statement and its bound values to database errors.
SQL_TAIL_PATTERN = re.compile(r"\s*\[(?:SQL|parameters):.*", re.IGNORECASE | re.DOTALL)

REQUEST_ID_HEADER = "x-request-id"
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,64}")
MAX_MESSAGE_CHARS = 2000
MAX_QUERY_CHARS = 1024
MAX_PATH_CHARS = 512
MAX_REASON_CHARS = 200
MAX_STACK_CHARS = 8000
MAX_BODY_SNIFF = 2048
AUDIT_FIELDS = ("user", "table", "action", "log_text")
OPTIONAL_FIELDS = ("method", "path", "query", "status", "duration_ms", "event", "reason")

_APP_MARKER = "_pear_ops_logging_handler"
_request_id = contextvars.ContextVar("pear_request_id", default=None)
_state: Dict[str, Any] = {"installed": False, "handler": None, "forwarder": None}


# ---------------------------------------------------------------- flags --

def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUTHY


def is_enabled() -> bool:
    return _flag("OPS_LOGGING")


# ----------------------------------------------------------- request id --

def get_request_id() -> Optional[str]:
    return _request_id.get()


def outbound_headers() -> Dict[str, str]:
    """Headers to add to an inter-service HTTP call: the current X-Request-ID.

    Empty when ops logging is off or there is no current request, so callers
    send exactly what they sent before.
    """
    if not _state["installed"]:
        return {}
    request_id = _request_id.get()
    return {"X-Request-ID": request_id} if request_id else {}


def _incoming_request_id(headers: Dict[str, str]) -> str:
    candidate = headers.get(REQUEST_ID_HEADER, "").strip()
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


# -------------------------------------------------------------- masking --

def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(word in lowered for word in SENSITIVE_QUERY_KEYS)


def _scrub(text: str) -> str:
    """Remove personal data from free text: NRIC/FIN, emails, SQL statements and bound values."""
    text = SQL_TAIL_PATTERN.sub("", text)
    text = EMAIL_PATTERN.sub(MASK, text)
    return NRIC_PATTERN.sub(MASK, text)


def mask_query(query_string: str) -> str:
    """Mask a query string. Anything that is not a plain key=value pair (a bare
    token, or an item with ';' in it) is masked whole."""
    if not query_string:
        return ""
    items = []
    for item in query_string.split("&"):
        if not item:
            continue
        key, separator, value = item.partition("=")
        if not separator or ";" in item:
            items.append(MASK)
            continue
        key = unquote_plus(key)
        value = MASK if _is_sensitive_key(key) else _scrub(unquote_plus(value))
        items.append(f"{quote_plus(_scrub(key), safe='*')}={quote_plus(value, safe='*')}")
    return _scrub("&".join(items))[:MAX_QUERY_CHARS]


def mask_path(path: str) -> str:
    parts = path.split("/")
    for index in range(1, len(parts)):
        if parts[index] and parts[index - 1].lower() in SENSITIVE_PATH_PARENTS:
            parts[index] = MASK
    return "/".join(parts)[:MAX_PATH_CHARS]


def claimed_user_id(authorization: Optional[str]) -> Optional[str]:
    """userId from the bearer token's payload, without verifying it.

    Only used to label log lines. Returns None for anything unexpected.
    """
    if not authorization:
        return None
    try:
        token = authorization.split(" ", 1)[1] if " " in authorization else authorization
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
        subject = data.get("sub")
        if isinstance(subject, str):
            subject = json.loads(subject)
        user_id = subject.get("userId") if isinstance(subject, dict) else None
        return str(user_id)[:64] if user_id is not None else None
    except Exception:
        return None


# ------------------------------------------------------------ formatting --

def _utc_iso(created: float) -> str:
    stamp = datetime.fromtimestamp(created, tz=timezone.utc).isoformat(timespec="milliseconds")
    return stamp.replace("+00:00", "Z")


def _message(record: logging.LogRecord) -> str:
    try:
        text = record.getMessage()
    except Exception:
        text = str(record.msg)
    return _scrub(text)[:MAX_MESSAGE_CHARS]


def _ops_type(record: logging.LogRecord) -> str:
    explicit = getattr(record, "ops_type", None)
    if explicit:
        return str(explicit)
    return "auth" if hasattr(record, "auth_event") else "error"


def _user_id(record: logging.LogRecord) -> Optional[str]:
    value = getattr(record, "user_id", None) or getattr(record, "auth_claimed_user_id", None)
    return str(value) if value else None


class OpsJsonFormatter(logging.Formatter):
    """Formats any record as one pear-app-v1 JSON line.

    Only the fields listed here are written, so arbitrary `extra` keys on a
    record (such as an audit record's user/table/action/log_text) never leak
    into an ops line.
    """

    def __init__(self, service: str, environment: str):
        super().__init__()
        self.service = service
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        line: Dict[str, Any] = {
            "schema": SCHEMA,
            "timestamp": _utc_iso(record.created),
            "level": record.levelname,
            "service": self.service,
            "environment": self.environment,
            "ops_type": _ops_type(record),
            "logger": record.name,
            "message": _message(record),
            "request_id": getattr(record, "request_id", None),
            "user_id": _user_id(record),
        }
        for field in OPTIONAL_FIELDS:
            value = getattr(record, "ops_" + field, None)
            if value is not None:
                line[field] = value
        if line["ops_type"] == "request":
            line.setdefault("status", None)  # null when no response was started
        if hasattr(record, "auth_event"):
            # Shadow-mode events from app/auth/token_verifier.py (logger "pear.auth").
            line.setdefault("event", getattr(record, "auth_event", None))
            auth_reason = getattr(record, "auth_reason", None)
            line.setdefault("reason", _scrub(str(auth_reason))[:MAX_REASON_CHARS] if auth_reason is not None else None)
            endpoint = getattr(record, "auth_endpoint", None)
            if endpoint:
                line.setdefault("path", mask_path(str(endpoint)))
        if record.exc_info and record.exc_info[0] is not None:
            line["exception_type"] = record.exc_info[0].__name__
            stack = "".join(traceback.format_exception(*record.exc_info))
            line["stack_trace"] = _scrub(stack)[-MAX_STACK_CHARS:]
        return json.dumps(line, default=str)


class RequestIdFilter(logging.Filter):
    """Stamps the current request ID on every record the ops handler writes."""

    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(record, "request_id", None) is None:
            record.request_id = _request_id.get()
        return True


class _NotAuditFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not all(hasattr(record, field) for field in AUDIT_FIELDS)


class _ForwardHandler(logging.Handler):
    """Root-logger handler (WARNING and up) that writes through the one ops file handler.

    Two RotatingFileHandlers on one file would corrupt rotation, so the
    root logger forwards to the same handler instance instead.
    """

    def __init__(self, target: logging.Handler):
        super().__init__(level=logging.WARNING)
        self.target = target
        self.addFilter(_NotAuditFilter())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.target.handle(record)
        except Exception:
            self.handleError(record)


# ----------------------------------------------------------------- setup --

def _process_tag() -> str:
    host = re.sub(r"[^A-Za-z0-9.-]", "-", socket.gethostname() or "host")[:63]
    return f"{host}-{os.getpid()}"


def ops_file_name(service: str) -> str:
    return f"ops_{service}_{_process_tag()}.log"


def _install_handlers(service: str, log_dir: str) -> None:
    os.makedirs(log_dir, exist_ok=True)
    environment = os.getenv("OPS_ENVIRONMENT") or os.getenv("ENVIRONMENT") or "unknown"
    handler = RotatingFileHandler(
        os.path.join(log_dir, ops_file_name(service)),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(OpsJsonFormatter(service, environment))
    handler.addFilter(RequestIdFilter())

    ops_logger = logging.getLogger(OPS_LOGGER_NAME)
    ops_logger.setLevel(logging.INFO)
    ops_logger.propagate = False
    ops_logger.addHandler(handler)

    forwarder = _ForwardHandler(handler)
    logging.getLogger().addHandler(forwarder)
    _state.update(installed=True, handler=handler, forwarder=forwarder)


def _register_debug_routes(app: Any) -> None:
    from fastapi import HTTPException

    def ops_debug_error():
        raise RuntimeError("Deliberate error from /ops-debug/error (OPS_DEBUG_ROUTES is on)")

    def ops_debug_forbidden():
        raise HTTPException(status_code=403, detail="Deliberate 403 from /ops-debug/forbidden")

    app.add_api_route("/ops-debug/error", ops_debug_error, methods=["GET"], include_in_schema=False)
    app.add_api_route("/ops-debug/forbidden", ops_debug_forbidden, methods=["GET"], include_in_schema=False)


def setup_ops_logging(app: Any, service: str, log_dir: str) -> bool:
    """Install ops logging on `app` when OPS_LOGGING is on.

    Call once, after every other app.add_middleware(...), so the request
    middleware is the outermost one. Returns True when installed. Never
    raises: if anything goes wrong the service runs exactly as before.
    """
    if not is_enabled():
        return False
    try:
        handler = _state["handler"]
        if handler is not None and getattr(app, _APP_MARKER, None) is handler:
            return True  # this app is already set up
        if not _state["installed"]:
            _install_handlers(service, log_dir)
        app.add_middleware(OpsRequestMiddleware)
        if _flag("OPS_DEBUG_ROUTES"):
            _register_debug_routes(app)
        setattr(app, _APP_MARKER, _state["handler"])
        return True
    except Exception:
        _safe(shutdown_ops_logging)
        logging.getLogger(__name__).warning("Ops logging could not be set up; continuing without it", exc_info=True)
        return False


def shutdown_ops_logging() -> None:
    """Remove the ops handlers (used by tests)."""
    handler, forwarder = _state["handler"], _state["forwarder"]
    if forwarder is not None:
        logging.getLogger().removeHandler(forwarder)
    if handler is not None:
        logging.getLogger(OPS_LOGGER_NAME).removeHandler(handler)
        handler.close()
    _state.update(installed=False, handler=None, forwarder=None)


# ----------------------------------------------------------- auth events --

def auth_event(
    event: str,
    reason: Optional[str] = None,
    user_id: Optional[str] = None,
    level: int = logging.WARNING,
    **fields: Any,
) -> None:
    """Write one auth event (failed login, refresh failure, 401/403).

    No-op when ops logging is off. Never raises.
    """
    if not _state["installed"]:
        return
    try:
        reason_text = _scrub(str(reason))[:MAX_REASON_CHARS] if reason is not None else None
        extra: Dict[str, Any] = {
            "ops_type": "auth",
            "user_id": user_id,
            "ops_event": event,
            "ops_reason": reason_text,
        }
        for key in ("method", "path", "status"):
            if fields.get(key) is not None:
                extra["ops_" + key] = mask_path(str(fields[key])) if key == "path" else fields[key]
        message = f"Auth {event}: {reason_text}" if reason_text else f"Auth {event}"
        logging.getLogger(OPS_LOGGER_NAME).log(level, message, extra=extra)
    except Exception:
        pass


# ------------------------------------------------------------ middleware --

def _safe(func: Any, *args: Any) -> None:
    try:
        func(*args)
    except Exception:
        pass


def _headers(scope: Dict[str, Any]) -> Dict[str, str]:
    return {
        bytes(name).decode("latin-1").lower(): bytes(value).decode("latin-1")
        for name, value in scope.get("headers") or []
    }


def _is_excluded(scope: Dict[str, Any], headers: Dict[str, str]) -> bool:
    if scope.get("method") == "OPTIONS":
        return True
    path = str(scope.get("path") or "/")
    normalised = path.rstrip("/") or "/"
    if normalised in EXCLUDED_PATHS:
        return True
    return normalised.endswith(VERIFIER_PATH_SUFFIX) and headers.get("user-agent", "").startswith(LIBRARY_USER_AGENTS)


def _detail(body: bytes) -> Optional[str]:
    if not body:
        return None
    try:
        detail = json.loads(body.decode("utf-8")).get("detail")
    except Exception:
        return None
    if detail is None:
        return None
    text = detail if isinstance(detail, str) else json.dumps(detail, default=str)
    return _scrub(text)[:MAX_REASON_CHARS]


def _observe(message: Dict[str, Any], seen: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    try:
        if message.get("type") == "http.response.start":
            seen["status"] = int(message.get("status", 500))
            headers = list(message.get("headers") or [])
            if not any(bytes(name).lower() == b"x-request-id" for name, _ in headers):
                headers.append((b"x-request-id", request_id.encode("latin-1")))
            return {**message, "headers": headers}
        if (
            message.get("type") == "http.response.body"
            and seen["status"] in (401, 403)
            and len(seen["body"]) < MAX_BODY_SNIFF
        ):
            chunk = bytes(message.get("body", b""))
            seen["body"] += chunk[: MAX_BODY_SNIFF - len(seen["body"])]
    except Exception:
        pass
    return message


def _log_request(scope: Dict[str, Any], headers: Dict[str, str], seen: Dict[str, Any], started: float) -> None:
    status = seen["status"]  # None when no response was started (e.g. client disconnect)
    method = str(scope.get("method", ""))
    path = mask_path(str(scope.get("path", "")))
    query = mask_query(bytes(scope.get("query_string", b"")).decode("latin-1"))
    user_id = claimed_user_id(headers.get("authorization"))
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    if status is None:
        level = logging.INFO
    elif status >= 500:
        level = logging.ERROR
    elif status >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO
    logging.getLogger(OPS_LOGGER_NAME).log(
        level,
        f"{method} {path} -> {status if status is not None else 'no response'} ({duration_ms} ms)",
        extra={
            "ops_type": "request",
            "user_id": user_id,
            "ops_method": method,
            "ops_path": path,
            "ops_query": query,
            "ops_status": status,
            "ops_duration_ms": duration_ms,
        },
    )
    if status in (401, 403):
        auth_event(f"http_{status}", reason=_detail(seen["body"]), user_id=user_id, method=method, path=path, status=status)


def _is_client_disconnect(exc: BaseException) -> bool:
    try:
        from starlette.requests import ClientDisconnect
        return isinstance(exc, ClientDisconnect)
    except Exception:
        return type(exc).__name__ == "ClientDisconnect"


def _log_unhandled(scope: Dict[str, Any], headers: Dict[str, str], exc: BaseException) -> None:
    method = str(scope.get("method", ""))
    path = mask_path(str(scope.get("path", "")))
    logging.getLogger(OPS_LOGGER_NAME).error(
        f"Unhandled error at {method} {path}",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "ops_type": "error",
            "user_id": claimed_user_id(headers.get("authorization")),
            "ops_method": method,
            "ops_path": path,
        },
    )


class OpsRequestMiddleware:
    """Pure ASGI middleware: request ID, one request line per request made by
    a person, and an auth event for every 401/403 response.

    Anything that fails inside it is swallowed. The wrapped app's responses
    and exceptions pass through unchanged (apart from the added
    X-Request-ID response header).
    """

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or not _state["installed"]:
            await self.app(scope, receive, send)
            return
        try:
            headers = _headers(scope)
            request_id = _incoming_request_id(headers)
            skip = _is_excluded(scope, headers)
        except Exception:
            await self.app(scope, receive, send)
            return

        token = _request_id.set(request_id)
        started = time.perf_counter()
        seen: Dict[str, Any] = {"status": None, "body": b""}

        async def send_wrapper(message: Dict[str, Any]) -> None:
            await send(_observe(message, seen, request_id))

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            if not _is_client_disconnect(exc):
                if seen["status"] is None:
                    seen["status"] = 500
                if not skip:
                    _safe(_log_unhandled, scope, headers, exc)
            raise
        finally:
            if not skip:
                _safe(_log_request, scope, headers, seen, started)
            _request_id.reset(token)
