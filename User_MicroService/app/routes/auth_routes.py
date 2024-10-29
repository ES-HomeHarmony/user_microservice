from fastapi import APIRouter, Response, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from urllib.parse import urlencode
from sqlalchemy.orm import Session
from app.database import get_db
import requests
from app.services import auth_service  # Import the service here
import os

router = APIRouter()

COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_APP_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@router.get("/auth/login", status_code=302)
async def login_redirect():
    query_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": REDIRECT_URI
    }
    cognito_url = f"https://{COGNITO_DOMAIN}/oauth2/authorize"
    return Response(status_code=302, headers={"Location": f"{cognito_url}?{urlencode(query_params)}"})

@router.get("/callback")
async def callback(request: Request, response: Response, db: Session = Depends(get_db)):
    
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    # Exchange code for tokens
    tokens = auth_service.exchange_code_for_tokens(code)
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    if not id_token or not access_token:
        raise HTTPException(status_code=400, detail="ID or Access Token missing")

    # Decode the id_token, passing access_token for at_hash validation
    user_info = auth_service.decode_jwt(id_token, access_token)
    # user = auth_service.get_or_create_user(user_info, db)

    # Store access token in a secure, HTTP-only cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)
    return {"message": "Login successful"}

@router.get("/auth/logout")
async def logout():
    response = JSONResponse(content={"message": "User logged out successfully"})
    response.delete_cookie(key="access_token")
    return response
