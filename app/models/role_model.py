from sqlalchemy import Column, Boolean, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import pytz

class Role(Base):
    __tablename__ = "TABLE_ROLES"

    id = Column(String(8), primary_key=True)
    isDeleted = Column(Boolean, default=False, nullable=False)
    roleName = Column(String(255), unique=True, nullable=False)
    description = Column(String(1000), nullable=True)

    accessLevelId = Column(String(8), ForeignKey("TABLE_ACCESS_LEVELS.id"), nullable=False)

    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    createdById = Column(String(255), nullable=False)
    modifiedById = Column(String(255), nullable=False)

    accessLevel = relationship("AccessLevel", back_populates="roles", lazy="joined")
    users = relationship("User", back_populates="role")

    @property
    def accessLevelSensitive(self):
        """Numeric sensitivity rank of this role's access level.

        The Patient service compares this against a patient's own
        accessLevelSensitive to decide whether social history comes back in
        full or masked. Its PrivacyStatus enum is LOW=1, MEDIUM=2, HIGH=3,
        which lines up with levelRank here (NONE=0, LOW=1, MEDIUM=2, HIGH=3),
        so the rank is what goes over the wire rather than the code string.

        None when a role has no access level. Callers must treat that as
        "no access" rather than comparing it.
        """
        return self.accessLevel.levelRank if self.accessLevel else None

    def get_created_date_sgt(self):
        return self.createdDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))

    def get_modified_date_sgt(self):
        return self.modifiedDate.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("Asia/Singapore"))