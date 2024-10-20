from sqlalchemy.orm import Session
from app.models import User
from app.schemas import UserBase

# Funções relacionadas ao gerenciamento dos usuários no banco de dados.

def get_user_by_id(db: Session, user_id: int):
    """
    Retorna um usuário a partir do seu ID.
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_cognito_id(db: Session, cognito_id: str):
    """
    Retorna um usuário a partir do seu Cognito ID.
    """
    return db.query(User).filter(User.cognito_id == cognito_id).first()

def get_user_by_email(db: Session, email: str):
    """
    Retorna um usuário a partir do seu email.
    """
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserBase):
    """
    Cria um novo usuário no banco de dados.
    """
    db_user = User(cognito_id=user.cognito_id, name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, updated_data: dict):
    """
    Atualiza os dados de um usuário existente.
    """
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in updated_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    """
    Remove um usuário do banco de dados.
    """
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
    return user