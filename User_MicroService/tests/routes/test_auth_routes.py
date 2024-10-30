# test_auth.py
from unittest.mock import patch
from fastapi import status

@patch("app.services.auth_service.exchange_code_for_tokens")
@patch("app.services.auth_service.decode_jwt")
def test_login_logout_flow(mock_decode_jwt, mock_exchange_code_for_tokens, client):

    # Log to verify the mocked methods
    print("Testing Login Flow...")

    # Mock the exchange_code_for_tokens function to return fake tokens
    mock_exchange_code_for_tokens.return_value = {
        "id_token": "test_id_token",
        "access_token": "test_access_token"
    }

    # Mock decode_jwt to return a sample user payload
    mock_decode_jwt.return_value = {
        "sub": "test_cognito_id",
        "email": "testuser@example.com",
        "name": "Test User"
    }

    # Test login redirect
    login_response = client.get("/auth/login", follow_redirects=False)
    assert login_response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    
    # Test callback endpoint with mocked code
    code = "test_authorization_code"
    callback_response = client.get(f"/callback?code={code}", follow_redirects=False)
    assert callback_response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert callback_response.cookies.get("access_token") == "test_access_token"

    # Test logout functionality
    logout_response = client.get("/auth/logout", follow_redirects=False)
    assert logout_response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert logout_response.cookies.get("access_token") is None

def test_callback_missing_code(client):
    response = client.get("/callback")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Authorization code missing"}

@patch("app.services.auth_service.exchange_code_for_tokens")
def test_callback_missing_tokens(mock_exchange_code_for_tokens, client):
    # Configurar o mock para retornar um dicionário sem os tokens
    mock_exchange_code_for_tokens.return_value = {
        "id_token": None,
        "access_token": None
    }

    # Fazer uma requisição ao endpoint /callback com um código de autorização simulado
    code = "test_authorization_code"
    response = client.get(f"/callback?code={code}")

    # Verificar se o código de status da resposta é 400 (Bad Request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verificar se a mensagem de erro é a correta
    assert response.json() == {"detail": "ID or Access Token missing"}
