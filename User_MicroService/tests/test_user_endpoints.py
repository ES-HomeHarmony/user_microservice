# Now import the necessary modules
import pytest
from app.database import Base, engine
from fastapi import Depends
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.models.models import User
from app.services.auth_service import get_current_user

client = TestClient(app)

# Mock user data
mock_user = User(id=1, cognito_id="test123", name="John", email="john@test.com")

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield  # Run the test
    # Drop the tables after the test is complete
    Base.metadata.drop_all(bind=engine)

def test_create_user():
    response = client.post("/users/", json={"cognito_id": "test123", "name": "John", "email": "john@test.com"})
    assert response.status_code == 201



def test_create_user_when_already_exist():
    response = client.post("/users/", json={"cognito_id": "test123", "name": "John", "email": "john@test.com"})
    response = client.post("/users/", json={"cognito_id": "test123", "name": "John", "email": "john@test.com"})
    assert response.status_code == 400

def test_get_user_when_Exist():
    response = client.post("/users/", json={"cognito_id": "test123", "name": "John", "email": "john@test.com"})
    response = client.get("/users/test123")
    assert response.status_code == 200

def test_get_user_when_Not_Exist():
    response = client.get("/users/1")
    assert response.status_code == 404

def override_get_current_user():
    return mock_user

def test_get_user_profile():
    # Correctly override the get_current_user dependency
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Make the request to the /user/profile endpoint
    response = client.get("/user/profile")
    
    # Verify that the response was successful
    assert response.status_code == 200
    
    # Validate the returned user data
    data = response.json()
    assert data["cognito_id"] == "test123"
    assert data["name"] == "John"
    assert data["email"] == "john@test.com"
    
    # Reset dependency overrides after testing
    app.dependency_overrides = {}

def test_update_user_profile():
    # Override the get_current_user dependency
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Create a new user using a POST request
    client.post("/users/", json={"cognito_id": "test123", "name": "John", "email": "john@test.com"})

    # Update the user's profile using a PUT request
    update_data = {
        "name": "John Doe",
        "email": "john.doe@test.com",
        "role": "admin"
    }

    response = client.put("/user/profile/update", json=update_data)

    # Verify that the response is successful
    assert response.status_code == 200

    # Validate that the returned user profile has been updated
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john.doe@test.com"

    # Reset the dependency overrides
    app.dependency_overrides = {}