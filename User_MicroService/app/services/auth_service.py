from jose import jwt, JWTError, jwk
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
import requests
import os

# Environment variables
REGION = os.getenv("AWS_REGION")
USERPOOL_ID = os.getenv("COGNITO_USERPOOL_ID")
APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_KEYS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USERPOOL_ID}/.well-known/jwks.json"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") 

def get_cognito_public_keys():
    try:
        response = requests.get(COGNITO_KEYS_URL)
        response.raise_for_status()
        keys = response.json()["keys"]
        return keys
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail="Error fetching public keys")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    keys = get_cognito_public_keys()
    try:
        # Get the kid (Key ID) from the JWT header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        # Find the appropriate public key
        key = next((key for key in keys if key["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Construct the public key
        public_key = jwk.construct(key)

        # Decode and validate the token
        try:
            payload = jwt.decode(token, key=public_key, algorithms=["RS256"], audience=APP_CLIENT_ID)
            cognito_id = payload.get("sub")
            
            if not cognito_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        except JWTError as e:
            print(f"JWT Error: {e}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Check if the user exists in the database
        user = db.query(User).filter(User.cognito_id == cognito_id).first()
        if not user:
            # If user doesn't exist, create a new user
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
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing the token")