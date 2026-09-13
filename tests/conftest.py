import sys
from unittest.mock import MagicMock

import pytest

# app/service/email_service.py constructs a real PySendPulse client at import
# time, which makes a live network call to authenticate. That's unreachable in
# this dev sandbox and breaks collection for any test file that transitively
# imports email_service (e.g. via app.crud.user_crud). Stub the module before
# anything imports it so collection succeeds without a real network call.
_fake_pysendpulse_module = MagicMock()
_fake_pysendpulse_module.PySendPulse = MagicMock(return_value=MagicMock())
sys.modules.setdefault("pysendpulse", MagicMock())
sys.modules["pysendpulse.pysendpulse"] = _fake_pysendpulse_module


@pytest.fixture(autouse=True)
def _no_real_rabbitmq_producer():
    """
    Some code paths (outbox_service.OutboxService, messaging.drift_consumer)
    call get_producer_manager() with no args, which eagerly builds a real
    RabbitMQClient and attempts a live broker connection -- unreachable and
    slow-to-timeout in this dev sandbox. Stub it globally the same way
    tests/integration/conftest.py already does for integration tests.
    """
    with pytest.MonkeyPatch.context() as mp:
        # Each module imported get_producer_manager by name (`from ... import
        # get_producer_manager`), binding it into its own namespace -- patch
        # every import site, not just the source module.
        for target in (
            "app.messaging.producer_manager.get_producer_manager",
            "app.service.outbox_service.get_producer_manager",
            "app.messaging.drift_consumer.get_producer_manager",
            "app.messaging.user_publisher.get_producer_manager",
        ):
            mp.setattr(target, lambda *args, **kwargs: MagicMock())

        # app/routers/__init__.py builds a module-level BackgroundScheduler
        # and starts it on FastAPI's lifespan/startup event, which any
        # TestClient(app) use triggers. The background thread it spawns is
        # non-daemon and never gets shut down in these tests, which hangs the
        # whole process at exit. Prevent it from actually starting.
        mp.setattr(
            "apscheduler.schedulers.background.BackgroundScheduler.start",
            lambda self, *args, **kwargs: None,
        )

        # Root-cause fix: `with TestClient(app) as client:` runs FastAPI's
        # real lifespan, which starts a RabbitMQ consumer (drift_consumer)
        # that calls RabbitMQClient.connect() -- a genuine blocking network
        # connect() with no broker reachable in this sandbox, which never
        # returns and then blocks teardown (stop_all_consumers joins the
        # stuck thread) forever. Stub connect() at the source so every
        # caller (producer or consumer) gets a harmless no-op instead of a
        # real socket attempt.
        mp.setattr(
            "app.messaging.rabbitmq_client.RabbitMQClient.connect",
            lambda self, *args, **kwargs: None,
        )
        yield
