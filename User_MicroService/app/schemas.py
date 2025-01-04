from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    cognito_id: str
    name: str
    email: str
    role: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: int