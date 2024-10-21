from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    cognito_id = Column(String(255), index=True, unique=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    role = Column(String(100), nullable=True)