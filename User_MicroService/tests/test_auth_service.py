import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import JWTError
from app.services.auth_service import get_current_user, get_cognito_public_keys
from app.models.models import User

@pytest.fixture
def mock_db_session():
    """Fixture for mocking the database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_user():
    """Fixture for creating a mock user."""
    return User(id=1, cognito_id="test123", name="John Doe", email="john.doe@test.com")

@pytest.fixture
def mock_token():
    """Fixture for a mock JWT token."""
    return "fake-jwt-token"

@pytest.fixture
def mock_payload():
    """Fixture for mock payload returned by a decoded JWT token."""
    return {
        "sub": "test123",
        "email": "john.doe@test.com",
        "name": "John Doe",
        "aud": "app-client-id"
    }


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_db_session, mock_token):
    """Test when the token is invalid (raises a JWTError)."""
    with patch("app.services.auth_service.get_cognito_public_keys", return_value=[{"kid": "fake-key-id"}]):
        with patch("jose.jwt.get_unverified_header", return_value={"kid": "fake-key-id"}):
            with patch("jose.jwt.decode", side_effect=JWTError("Invalid token")):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(token=mock_token, db=mock_db_session)

                # Check that the exception has a 500 status code
                assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_current_user_missing_claims(mock_db_session, mock_token):
    """Test when the token is missing required claims (e.g., 'sub')."""
    mock_payload = {"email": "john.doe@test.com", "name": "John Doe", "aud": "app-client-id"}

    with patch("app.services.auth_service.get_cognito_public_keys", return_value=[{"kid": "fake-key-id", "alg": "RS256"}]):
        with patch("jose.jwt.get_unverified_header", return_value={"kid": "fake-key-id"}):
            with patch("jose.jwt.decode", return_value=mock_payload):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(token=mock_token, db=mock_db_session)

                # Check that the exception has a 500 status code
                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "An error occurred while processing the token"

@pytest.mark.asyncio
async def test_get_current_user_key_not_found(mock_db_session, mock_token, mock_payload):
    """Test when the public key is not found."""
    with patch("app.services.auth_service.get_cognito_public_keys", return_value=[{"kid": "another-key-id"}]):
        with patch("jose.jwt.get_unverified_header", return_value={"kid": "fake-key-id"}):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=mock_token, db=mock_db_session)

            # Check that the exception has a 500 status code
            assert exc_info.value.status_code == 500

@pytest.mark.asyncio
async def test_get_current_user_error_fetching_keys(mock_db_session, mock_token):
    """Test when there is an error fetching the public keys."""
    with patch("app.services.auth_service.get_cognito_public_keys", side_effect=HTTPException(status_code=500, detail="Error fetching public keys")):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=mock_token, db=mock_db_session)

        # Check that the exception has a 500 status code
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Error fetching public keys"