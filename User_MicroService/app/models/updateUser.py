from sqlalchemy import Column, Integer, String
from app.database import Base
from pydantic import BaseModel, ConfigDict


class UpdateProfileSchema(BaseModel):
    name: str
    email: str
    role: str = None

    model_config = ConfigDict(from_attributes=True)