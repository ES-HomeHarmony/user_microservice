from pydantic import BaseModel

class UserBase(BaseModel):
    cognito_id: str
    name: str
    email: str

    class Config:
        from_attributes = True  # Atualização para Pydantic V2

class UserResponse(UserBase):
    id: int