# Now import the necessary modules
import pytest
from app.database import Base, engine
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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

def test_get_user_when_Exist():
    response = client.post("/users/", json={"cognito_id": "test123", "name": "John", "email": "john@test.com"})
    response = client.get("/users/1")
    assert response.status_code == 200

def test_get_user_when_Not_Exist():
    response = client.get("/users/1")
    assert response.status_code == 404