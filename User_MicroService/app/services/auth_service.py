import requests
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Header
from app.routes.user_routes import get_db
from sqlalchemy.orm import Session
from app.models import User
import os

# Carregar as variáveis de ambiente
REGION = os.getenv("AWS_REGION")
USERPOOL_ID = os.getenv("COGNITO_USERPOOL_ID")
APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_KEYS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USERPOOL_ID}/.well-known/jwks.json"

def get_cognito_public_keys():
    response = requests.get(COGNITO_KEYS_URL)
    response.raise_for_status()
    keys = response.json()["keys"]
    return keys

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    keys = get_cognito_public_keys()
    try:
        payload = jwt.decode(token, keys, algorithms=["RS256"], audience=APP_CLIENT_ID)
        cognito_id = payload.get("sub")
        if cognito_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Verificar se o usuário já existe no banco de dados
        user = db.query(User).filter(User.cognito_id == cognito_id).first()
        if not user:
            # Se não existir, cria um novo usuário
            user = User(
                cognito_id=cognito_id,
                email=payload.get("email"),
                name=payload.get("name")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")