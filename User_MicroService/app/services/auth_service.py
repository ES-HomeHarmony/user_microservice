import requests
import os
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
import base64
from app.database import get_db
from app.models.models import User

# Load environment variables
CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
AWS_REGION = os.getenv("AWS_REGION")
COGNITO_USERPOOL_ID = os.getenv("COGNITO_USERPOOL_ID")
TOKEN_URL = f"https://{os.getenv('COGNITO_DOMAIN')}/oauth2/token"
COGNITO_KEYS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}/.well-known/jwks.json"
CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET")

def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange authorization code for tokens from Cognito.
    """

    client_auth = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(client_auth.encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_auth}"
    }
    
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": os.getenv("REDIRECT_URI"),
            "code": code
        },
        headers=headers
    )

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Token exchange failed")

    return response.json()

def decode_jwt(token: str, access_token: str) -> dict:
    keys = requests.get(COGNITO_KEYS_URL).json().get("keys", [])

    headers = jwt.get_unverified_headers(token)
    kid = headers["kid"]
    key = next((key for key in keys if key["kid"] == kid), None)
    
    if key is None:
        raise ValueError("Public key not found")

    issuer = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USERPOOL_ID}"

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=issuer,
            access_token = access_token
        )

    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

    return payload

def get_or_create_user(user_info: dict, db: Session) -> User:
    """
    Retrieve user from the database or create a new one based on Cognito ID.
    """

    from app.main import producer
    
    user = db.query(User).filter(User.email == user_info["email"]).first()
    print("user:", user.email, user.cognito_id)
    if not user:
        user = User(
            cognito_id=user_info["sub"],
            email=user_info.get("email"),
            name=user_info.get("given_name")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else: 
        if user.role == "tenant":
            print("HEREEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
            old_id = user.cognito_id
            print("old_id", old_id)
            user.cognito_id = user_info["sub"]
            db.commit()
            db.refresh(user)

            message = {
                "old_id": old_id,
                "new_id": user.cognito_id
            }

            producer.send('user-id-update', message)

    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Extracts and verifies the JWT token from the cookie to retrieve the current user.
    """
    # Retrieve the access token from cookies
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing from cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode the JWT token to retrieve the payload
        payload = decode_jwt(access_token, access_token)
        cognito_id = payload.get("sub")
        if cognito_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Find the user in the database
        user = db.query(User).filter(User.cognito_id == cognito_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )