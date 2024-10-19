# from fastapi import FastAPI, HTTPException, Depends, status
# from pydantic import BaseModel
# import models
# from database import SessionLocal, engine
# from sqlalchemy.orm import Session

# app = FastAPI()
# models.Base.metadata.create_all(bind=engine)

# class UserBase(BaseModel):
#     cognito_id: str
#     name: str
#     email: str

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @app.post("/users/", status_code=status.HTTP_201_CREATED)
# async def create_user(user: UserBase, db: Session = Depends(get_db)):
#     db_user = models.User(**user.model_dump())
#     db.add(db_user)
#     db.commit()

# @app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
# async def get_user(user_id: int, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.id == user_id).first()
#     if user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user


from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routes import user_routes

app = FastAPI()

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Inclui as rotas de usuários
app.include_router(user_routes.router)