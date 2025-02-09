from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Session(Base):
    __tablename__ = 'TABLE_SESSIONS'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # Unique session identifier
    user_id = Column(Integer, ForeignKey('users.id'))  # Link to the user table
    created_at = Column(DateTime, default=datetime.utcnow)  # Session creation time
    expired_at = Column(DateTime, nullable=True)  # Time when session expires
    status = Column(String, default="active")  # Session status ('active', 'expired', 'logged_out')

    # Relationship to the User model
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(session_id={self.session_id}, user_id={self.user_id}, status={self.status})>"