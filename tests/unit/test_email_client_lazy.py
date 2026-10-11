import asyncio
import importlib
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def email_service():
    fake_module = MagicMock()
    fake_module.PySendPulse = MagicMock(return_value=MagicMock())
    original = sys.modules.get("pysendpulse.pysendpulse")
    sys.modules["pysendpulse.pysendpulse"] = fake_module
    import app.service.email_service as module
    module = importlib.reload(module)
    yield module, fake_module.PySendPulse
    if original is not None:
        sys.modules["pysendpulse.pysendpulse"] = original
    importlib.reload(module)


def test_import_does_not_connect_to_sendpulse(email_service):
    _, client_class = email_service
    client_class.assert_not_called()


def test_client_created_once_on_first_send(email_service):
    module, client_class = email_service
    asyncio.run(module.send_reset_password_email("a@example.com", "token"))
    asyncio.run(module.send_registration_email("b@example.com", "token"))
    client_class.assert_called_once()
    assert client_class.return_value.smtp_send_mail.call_count == 2


def test_failed_connection_raises_on_send_and_retries_next_time(email_service):
    module, client_class = email_service
    client_class.side_effect = [Exception("Could not connect to API"), MagicMock()]
    with pytest.raises(Exception):
        asyncio.run(module.send_reset_password_email("a@example.com", "token"))
    asyncio.run(module.send_reset_password_email("a@example.com", "token"))
    assert client_class.call_count == 2
