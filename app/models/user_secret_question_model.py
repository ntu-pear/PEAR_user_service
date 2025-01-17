from sqlalchemy import Column, Integer,Boolean, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class UserSecretQuestion(Base):
    __tablename__ = 'USER_SECRET_QUESTION'

    id = Column(String(255), primary_key=True)
    active = Column(Boolean,default=True,nullable=False)
    userId = Column(String(255), ForeignKey('TABLE_USER.id'))  # FK to User
    secretQuestionId = Column(Integer, ForeignKey('SECRET_QUESTION.id'))  # FK to SecretQuestion
    secretQuestionAnswer = Column(String(255), nullable=False)
    createdDate = Column(DateTime, server_default=func.now(), nullable=False)
    modifiedDate = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # createdById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    # modifiedById = Column(Integer, ForeignKey('TABLE_USER.id'),nullable=False)
    createdById = Column(String(255), ForeignKey('TABLE_USER.id'), nullable=True)
    modifiedById = Column(String(255), ForeignKey('TABLE_USER.id'), nullable=True)


    # Specify foreign_keys explicitly for user relationship to avoid ambiguity
    user = relationship('User', foreign_keys=[userId], backref='secretQuestions')
    secretQuestion = relationship('SecretQuestion', back_populates='userQuestions')
