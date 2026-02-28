import logging
import uuid
from typing import Dict, Any
from datetime import datetime

from producer_manager import get_producer_manager


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


    def publish_user_created(self, user_id: int, user_data: Dict[str, Any], 
                            created_by: str) -> bool:
        """Publish user creation event"""
        message = {
            'correlation_id': str(uuid.uuid4()),
            'event_type': 'USER_CREATED',
            'user_id': user_id,
            'user_data': user_data,
            'created_by': created_by,
            'timestamp': datetime.now().isoformat()
        }

        routing_key = f"user.created.{user_id}"
        success = self.manager.publish(self.exchange, routing_key, message)
        
        if success:
            logger.info(f"Published USER_CREATED event for user {user_id}")
        else:
            logger.error(f"Failed to publish USER_CREATED event for user {user_id}")
            
        return success
    
    def close(self):
        """Close is handled by the producer manager"""
        # No need to close individual publishers
        # The producer manager handles the connection
        pass


# Singleton instance
_user_publisher = None

def get_user_publisher(testing: bool =False) -> UserPublisher:
    """Get or create the singleton user publisher instance"""
    global _user_publisher
    if _user_publisher is None:
        _user_publisher = UserPublisher(testing=testing)
    return _user_publisher


# Usage examples and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Patient Service Usage: python patient_publisher.py test")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    if sys.argv[1] == "test":
        # Test publisher
        publisher = UserPublisher(testing=True)
        
        # Test data
        test_user_data = {
            'id': 123,
            'name': 'John Doe',
            'nric': 'S1234567A',
            'isActive': '1',
            'startDate': '2024-01-01T00:00:00',
            'preferredName': 'Johnny'
        }
        
        # Test publishing events
        publisher.publish_user_created(123, test_user_data, "test_user")
                
        
        publisher.close()