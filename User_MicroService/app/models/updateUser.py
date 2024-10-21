from sqlalchemy import Column, Integer, String
from app.database import Base
from pydantic import BaseModel


class UpdateProfileSchema(BaseModel):
    name: str
    email: str
    role: str = None

    class Config:
        orm_mode = True