import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from .producer_manager import get_producer_manager

logger = logging.getLogger(__name__)

class UserPublisher:
    """Publisher for User Service events"""

    def __init__(self, testing: bool = False):
        self.manager = get_producer_manager(testing=testing)
        self.exchange = 'user.updates'
        self.testing = testing

        # Declare the exchange
        try:
            self.manager.declare_exchange(self.exchange, 'topic')
            logger.info("User publisher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize user publisher: {str(e)}")


    def publish_userconfig_created(self, userconfig_id: int, userconfig_data: Dict[str, Any],
                                   created_by: str) -> bool:
        """Publish user config creation event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'USERCONFIG_CREATED',
            'userconfig_id': userconfig_id,
            'userconfig_data': userconfig_data,
            'created_by': created_by,
            'timestamp': datetime.now().isoformat()
        }

        routing_key = f"patient.user.config.created.{userconfig_id}"
        success = self.manager.publish(self.exchange, routing_key, message)

        if success:
            logger.info(f"Published USERCONFIG_CREATED event for userconfig {userconfig_id}")
        else:
            logger.error(f"Failed to publish USERCONFIG_CREATED event for userconfig {userconfig_id}")

        return success


    def publish_userconfig_updated(self, userconfig_id: int, old_data: Dict[str, Any],
                                   new_data: Dict[str, Any], changes: Dict[str, Any],
                                   modified_by: str) -> bool:
        """Publish user config update event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'USERCONFIG_UPDATED',
            'userconfig_id': userconfig_id,
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'modified_by': modified_by,
            'timestamp': datetime.now().isoformat()
        }

        routing_key = f"patient.user.config.updated.{userconfig_id}"
        success = self.manager.publish(self.exchange, routing_key, message)

        if success:
            logger.info(f"Published USERCONFIG_UPDATED event for userconfig {userconfig_id}")
        else:
            logger.error(f"Failed to publish USERCONFIG_UPDATED event for userconfig {userconfig_id}")

        return success


    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_user_publisher = None

def get_user_publisher(testing: bool = False) -> UserPublisher:
    """Get or create the singleton user publisher instance"""
    global _user_publisher
    if _user_publisher is None:
        _user_publisher = UserPublisher(testing=testing)
    return _user_publisher


# Usage examples and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("User Service Usage: python user_publisher.py test")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    if sys.argv[1] == "test":
        publisher = UserPublisher(testing=True)

        test_userconfig_data = {
            'id': 999,
            'configBlob': {
                'SESSION_EXPIRE_MINUTES': 10,
                'MAX_PATIENT_PHOTO': 10,
                'MAX_ITEMS_TO_RETURN': 40,
            },
            'modifiedDate': '2025-01-01T00:00:00',
            'modifiedById': 'test_user',
        }

        publisher.publish_userconfig_created(999, test_userconfig_data, "test_user")
        publisher.publish_userconfig_updated(
            999,
            old_data=test_userconfig_data,
            new_data=test_userconfig_data,
            changes={},
            modified_by="test_user",
        )

        publisher.close()
