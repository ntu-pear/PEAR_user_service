from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class SecretQuestion(Base):
    __tablename__ = 'SECRET_QUESTION'

    id = Column(Integer, primary_key=True)
    active = Column(String(1),default='Y',nullable=False)
    value = Column(String(255))
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    # modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(String(255), ForeignKey('TABLE_USER.id'), nullable=True)
    modifiedById = Column(String(255), ForeignKey('TABLE_USER.id'), nullable=True)


    # Use back_populates instead of backref
    userQuestions = relationship('UserSecretQuestion', back_populates='secretQuestion')
