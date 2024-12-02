# test_user_routes.py
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.schemas import UserBase
from app.models.models import User
from app.main import app
from fastapi import status

@pytest.fixture
def new_user():
    return UserBase(
        name="John Doe",
        email="johndoe@example.com",
        cognito_id="test_cognito_id",
        role="user"
    )

def test_create_user(client, db_session, new_user):
    # Test creating a new user
    response = client.post("/users/", json=new_user.model_dump())
    assert response.status_code == status.HTTP_201_CREATED

    # Verify user in database
    db_user = db_session.query(User).filter(User.email == new_user.email).first()
    assert db_user is not None
    assert db_user.name == new_user.name

def test_create_the_same_user(client, new_user):
    # Test creating the same user twice
    response = client.post("/users/", json=new_user.model_dump())
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post("/users/", json=new_user.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST