from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(Base):
    __tablename__ = 'USER_ROLES'

    id = Column(Integer, primary_key=True)
    userId = Column(Integer, ForeignKey('TABLE_USER.id'), nullable=False)  # FK to User
    roleId = Column(Integer, ForeignKey('ROLES.id'), nullable=False)  # FK to Role
    # createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    # modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    #createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    #modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    # createdById = Column(Integer, ForeignKey('TABLE_USER.id'), default=1, nullable=True)
    # modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'), default=1, nullable=True) 

    user = relationship('User', back_populates='roles', foreign_keys=[userId])
    role = relationship('Role', foreign_keys=[roleId])
