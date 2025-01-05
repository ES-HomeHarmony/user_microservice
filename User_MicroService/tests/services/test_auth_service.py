import pytest
from unittest.mock import patch, Mock
from app.services.auth_service import exchange_code_for_tokens, decode_jwt, get_or_create_user, get_current_user
from app.models.models import User
from jose import jwt, JWTError
from fastapi import status, HTTPException


@patch("requests.post")
def test_exchange_code_for_tokens(mock_post, client):
    # Mocking the response from Cognito
    mock_post.return_value = Mock(status_code=200, json=lambda: {"access_token": "test_access_token", "id_token": "test_id_token"})

    code = "test_code"
    tokens = exchange_code_for_tokens(code)

    # Verify the response
    assert "access_token" in tokens
    assert "id_token" in tokens
    assert tokens["access_token"] == "test_access_token"
    assert tokens["id_token"] == "test_id_token"

@patch("requests.post")
def test_exchange_code_for_tokens_error(mock_post, client):
    # Mocking the response from Cognito
    mock_post.return_value = Mock(status_code=400)

    code = "test_code"
    with pytest.raises(HTTPException):
        exchange_code_for_tokens(code)

@patch("requests.get")
def test_decode_jwt(mock_get):
    # Mocking the response from Cognito keys endpoint
    mock_get.return_value = Mock(status_code=200, json=lambda: {"keys": [{"kid": "test_kid", "kty": "RSA", "alg": "RS256", "use": "sig", "n": "test_n", "e": "AQAB"}]})

    # Create a fake token header with the matching kid
    headers = {"kid": "test_kid"}
    jwt.get_unverified_headers = Mock(return_value=headers)

    # Mock token payload
    jwt.decode = Mock(return_value={"sub": "test_cognito_id"})

    token = "test_token"
    payload = decode_jwt(token, token)

    # Verify the payload
    assert "sub" in payload
    assert payload["sub"] == "test_cognito_id"

@patch("app.services.auth_service.decode_jwt")
def test_get_current_user(mock_decode_jwt, client, db_session):
    # Mock the decoded payload to simulate a valid token
    mock_decode_jwt.return_value = {"sub": "test_cognito_id"}

    # Create a user in the database
    user = User(cognito_id="test_cognito_id", email="testuser@example.com", name="Test User")
    db_session.add(user)
    db_session.commit()

    # Simulate a cookie being set in the client
    client.cookies.set("access_token", "test_token")

    # Simulate an authenticated request
    response = client.get("/user/profile")

    # Verify that the response is successful
    assert response.status_code == 200
    assert response.json()["cognito_id"] == "test_cognito_id"
    assert response.json()["email"] == "testuser@example.com"
    assert response.json()["name"] == "Test User"

@patch("app.services.auth_service.decode_jwt")
def test_get_current_user_user_not_found(mock_decode_jwt, client, db_session):
    # Mock the decoded payload to simulate a valid token
    mock_decode_jwt.return_value = {"sub": "test_cognito_id"}

    # Simulate a cookie being set in the client
    client.cookies.set("access_token", "test_token")

    # Simulate an authenticated request for a user that doesn't exist
    response = client.get("/user/profile")

    # Verify that the response indicates user not found
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"

@patch("app.services.auth_service.decode_jwt")
def test_get_current_user_invalid_token(mock_decode_jwt, client):
    # Mock the decode_jwt function to raise a JWTError
    mock_decode_jwt.side_effect = JWTError("Invalid token")

    # Simulate a cookie being set in the client
    client.cookies.set("access_token", "invalid_token")

    # Simulate an authenticated request with an invalid token
    response = client.get("/user/profile")

    # Verify that the response indicates invalid token
    assert response.status_code == 401
    assert response.json()["detail"] == "Token validation failed"

@patch("app.services.auth_service.get_current_user")
def test_get_current_user_no_access_token(mock_get_current_user, client):
    # Mock get_current_user to raise an HTTPException for missing access token
    mock_get_current_user.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token missing from cookies",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Simulate a request without setting an access token cookie
    response = client.get("/user/profile")

    # Verify that the response indicates access token missing
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token missing from cookies"

@patch("app.services.auth_service.get_current_user")
def test_get_current_user_no_cognito_id(mock_get_current_user, client):
    # Mock get_current_user to raise an HTTPException for missing access token
    mock_get_current_user.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token payloads",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Simulate a request without setting an access token cookie
    response = client.get("/user/profile")

    # Verify that the response indicates access token missing
    assert response.status_code == 401
    assert response.json()["detail"] == "Access token missing from cookies"


@patch("app.main.producer.send")
def test_get_or_create_user_creates_new_user(mock_producer, db_session):
    """
    Test that a new user is created when they do not exist in the database.
    """
    user_info = {
        "sub": "new_cognito_id",
        "email": "newuser@example.com",
        "given_name": "New User"
    }

    user = get_or_create_user(user_info, db_session)

    # Verify the new user is created
    assert user.cognito_id == "new_cognito_id"
    assert user.email == "newuser@example.com"
    assert user.name == "New User"

    # Ensure no Kafka messages are sent
    mock_producer.assert_not_called()

@patch("app.main.producer.send")
def test_get_or_create_user_existing_user_no_update(mock_producer, db_session):
    """
    Test that an existing user with a non-tenant role is not updated.
    """
    # Prepopulate a user with role "landlord"
    user = User(
        cognito_id="existing_cognito_id",
        email="testuser@example.com",
        name="Test User",
        role="landlord"
    )
    db_session.add(user)
    db_session.commit()

    user_info = {
        "sub": "new_cognito_id",
        "email": "testuser@example.com",
        "given_name": "Updated User"
    }

    result = get_or_create_user(user_info, db_session)

    # Verify the user is not updated
    assert result.cognito_id == "existing_cognito_id"
    assert result.email == "testuser@example.com"
    assert result.name == "Test User"

    # Ensure no Kafka messages are sent
    mock_producer.assert_not_called()

@patch("app.main.producer.send")
def test_get_or_create_user_tenant_role_updates_cognito_id(mock_producer, db_session):
    """
    Test that an existing tenant user's cognito_id is updated and a Kafka message is sent.
    """
    # Prepopulate a tenant user
    user = User(
        cognito_id="old_cognito_id",
        email="tenant@example.com",
        name="Tenant User",
        role="tenant"
    )
    db_session.add(user)
    db_session.commit()

    user_info = {
        "sub": "new_cognito_id",
        "email": "tenant@example.com",
        "given_name": "Updated Tenant User"
    }

    result = get_or_create_user(user_info, db_session)

    # Verify the cognito_id is updated
    assert result.cognito_id == "new_cognito_id"
    assert result.email == "tenant@example.com"
    assert result.name == "Tenant User"

    # Verify Kafka message is sent
    mock_producer.assert_called_once_with(
        'user-id-update',
        {
            "old_id": "old_cognito_id",
            "new_id": "new_cognito_id"
        }
    )