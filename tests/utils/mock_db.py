# mock_db.py
from unittest.mock import MagicMock

def get_db_session_mock():
    """Create a mock of the database session."""
    db_session_mock = MagicMock()
    
    # Mock methods on the session
    db_session_mock.add = MagicMock()
    db_session_mock.commit = MagicMock()
    db_session_mock.refresh = MagicMock()
    db_session_mock.query = MagicMock()
    db_session_mock.rollback = MagicMock()
    
    return db_session_mock
