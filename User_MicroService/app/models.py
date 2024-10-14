from sqlalchemy import Boolean, Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    cognito_id = Column(String(255), index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)

