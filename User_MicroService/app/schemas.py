from pydantic import BaseModel

class UserBase(BaseModel):
    cognito_id: str
    name: str
    email: str

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id: int
    role: str | None