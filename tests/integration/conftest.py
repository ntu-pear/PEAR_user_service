import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _no_real_producer():
    """
    Integration outbox tests only verify that an OutboxEvent row is written to
    the DB. Constructing OutboxService eagerly starts the real producer manager
    (thread + RabbitMQ connection + watchdog), which has no broker in CI and
    spews "connection failed" / watchdog-restart logs. Replace it with a no-op
    mock for these tests so the producer never starts.
    """
    with patch("app.service.outbox_service.get_producer_manager", return_value=MagicMock()):
        yield
