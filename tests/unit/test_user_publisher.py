import uuid
from datetime import datetime

import pytest
from unittest.mock import patch, MagicMock

from app.messaging.user_publisher import UserPublisher


@pytest.fixture
def mock_producer_manager():
    """Fixture for mocked producer manager"""
    with patch('app.messaging.user_publisher.get_producer_manager') as mock:
        manager = MagicMock()
        manager.declare_exchange.return_value = None
        manager.publish.return_value = True
        mock.return_value = manager
        yield manager


@pytest.fixture
def sample_userconfig_data():
    """Sample userconfig payload as the outbox relay would send it"""
    return {
        'id': 1,
        'configBlob': {
            'SESSION_EXPIRE_MINUTES': 10,
            'MAX_PATIENT_PHOTO': 10,
            'MAX_ITEMS_TO_RETURN': 40,
        },
        'modifiedDate': '2025-01-01T00:00:00',
        'modifiedById': 'test-user',
    }



def test_init_success(mock_producer_manager):
    """Should initialise and declare the user.updates exchange"""
    publisher = UserPublisher(testing=True)

    assert publisher.exchange == 'user.updates'
    assert publisher.testing is True
    assert publisher.manager is mock_producer_manager
    mock_producer_manager.declare_exchange.assert_called_once_with('user.updates', 'topic')


def test_init_exchange_declaration_failure(mock_producer_manager):
    """Should not crash if exchange declaration fails at startup"""
    mock_producer_manager.declare_exchange.side_effect = Exception("Exchange error")

    publisher = UserPublisher(testing=True)   # must not raise

    assert publisher.exchange == 'user.updates'
    mock_producer_manager.declare_exchange.assert_called_once_with('user.updates', 'topic')



@patch('app.messaging.user_publisher.datetime')
@patch('app.messaging.user_publisher.uuid.uuid4')
def test_publish_userconfig_created_success(
    mock_uuid, mock_datetime, mock_producer_manager, sample_userconfig_data
):
    """Should publish a USERCONFIG_CREATED message with correct payload"""
    mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
    mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0, 0)

    publisher = UserPublisher(testing=True)
    result = publisher.publish_userconfig_created(
        userconfig_id=1,
        userconfig_data=sample_userconfig_data,
        created_by='test-user',
    )

    assert result is True

    expected_message = {
        'correlation_id': '12345678-1234-5678-1234-567812345678',
        'event_type': 'USERCONFIG_CREATED',
        'userconfig_id': 1,
        'userconfig_data': sample_userconfig_data,
        'created_by': 'test-user',
        'timestamp': '2025-01-01T12:00:00',
    }
    mock_producer_manager.publish.assert_called_once_with(
        'user.updates',
        'patient.user.config.created.1',   # routing key pattern from outbox tests
        expected_message,
    )


def test_publish_userconfig_created_failure(mock_producer_manager, sample_userconfig_data):
    """Should return False when broker rejects the publish"""
    mock_producer_manager.publish.return_value = False

    publisher = UserPublisher(testing=True)
    result = publisher.publish_userconfig_created(
        userconfig_id=1,
        userconfig_data=sample_userconfig_data,
        created_by='test-user',
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()



@patch('app.messaging.user_publisher.datetime')
@patch('app.messaging.user_publisher.uuid.uuid4')
def test_publish_userconfig_updated_success(
    mock_uuid, mock_datetime, mock_producer_manager, sample_userconfig_data
):
    """Should publish a USERCONFIG_UPDATED message with correct changes payload"""
    mock_uuid.return_value = uuid.UUID('aabbccdd-1122-3344-5566-778899aabbcc')
    mock_datetime.now.return_value = datetime(2025, 6, 1, 9, 0, 0)

    publisher = UserPublisher(testing=True)

    old_data = sample_userconfig_data
    new_data = dict(old_data)
    new_data['configBlob'] = {
        'SESSION_EXPIRE_MINUTES': 30,
        'MAX_PATIENT_PHOTO': 20,
        'MAX_ITEMS_TO_RETURN': 80,
    }

    changes = {
        'SESSION_EXPIRE_MINUTES': {'old': 10, 'new': 30},
        'MAX_PATIENT_PHOTO':      {'old': 10, 'new': 20},
        'MAX_ITEMS_TO_RETURN':    {'old': 40, 'new': 80},
    }

    result = publisher.publish_userconfig_updated(
        userconfig_id=1,
        old_data=old_data,
        new_data=new_data,
        changes=changes,
        modified_by='test-user',
    )

    assert result is True

    expected_message = {
        'correlation_id': 'aabbccdd-1122-3344-5566-778899aabbcc',
        'event_type': 'USERCONFIG_UPDATED',
        'userconfig_id': 1,
        'old_data': old_data,
        'new_data': new_data,
        'changes': changes,
        'modified_by': 'test-user',
        'timestamp': '2025-06-01T09:00:00',
    }
    mock_producer_manager.publish.assert_called_once_with(
        'user.updates',
        'patient.user.config.updated.1',
        expected_message,
    )


def test_publish_userconfig_updated_failure(mock_producer_manager, sample_userconfig_data):
    """Should return False when broker rejects the publish"""
    mock_producer_manager.publish.return_value = False

    publisher = UserPublisher(testing=True)
    result = publisher.publish_userconfig_updated(
        userconfig_id=1,
        old_data={},
        new_data={},
        changes={},
        modified_by='test-user',
    )

    assert result is False
    mock_producer_manager.publish.assert_called_once()


# ── routing key format ───────────────────────────────────────────────────────

def test_created_routing_key_format(mock_producer_manager, sample_userconfig_data):
    """Routing key must be patient.user.config.created.<id>"""
    publisher = UserPublisher(testing=True)
    publisher.publish_userconfig_created(1, sample_userconfig_data, 'test-user')

    _, args, _ = mock_producer_manager.publish.mock_calls[0]
    assert args[1] == 'patient.user.config.created.1'


def test_updated_routing_key_format(mock_producer_manager, sample_userconfig_data):
    """Routing key must be patient.user.config.updated.<id>"""
    publisher = UserPublisher(testing=True)
    publisher.publish_userconfig_updated(1, {}, {}, {}, 'test-user')

    _, args, _ = mock_producer_manager.publish.mock_calls[0]
    assert args[1] == 'patient.user.config.updated.1'


# ── message structure ────────────────────────────────────────────────────────

def test_created_message_structure(mock_producer_manager, sample_userconfig_data):
    """USERCONFIG_CREATED payload must contain all required fields"""
    publisher = UserPublisher(testing=True)
    publisher.publish_userconfig_created(1, sample_userconfig_data, 'test-user')

    args, _ = mock_producer_manager.publish.call_args[0], {}
    message = mock_producer_manager.publish.call_args[0][2]

    for field in ['correlation_id', 'event_type', 'userconfig_id',
                  'userconfig_data', 'created_by', 'timestamp']:
        assert field in message

    assert message['event_type'] == 'USERCONFIG_CREATED'


def test_updated_message_structure(mock_producer_manager, sample_userconfig_data):
    """USERCONFIG_UPDATED payload must contain all required fields"""
    publisher = UserPublisher(testing=True)
    publisher.publish_userconfig_updated(1, {}, {}, {}, 'test-user')

    message = mock_producer_manager.publish.call_args[0][2]

    for field in ['correlation_id', 'event_type', 'userconfig_id',
                  'old_data', 'new_data', 'changes', 'modified_by', 'timestamp']:
        assert field in message

    assert message['event_type'] == 'USERCONFIG_UPDATED'



def test_close(mock_producer_manager):
    """close() should be a no-op (producer manager owns the connection)"""
    publisher = UserPublisher(testing=True)
    publisher.close()   # must not raise
