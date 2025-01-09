import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tasks.db"

# Set up the test database engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the `get_db` dependency to use test database
def override_get_db() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)  # Set up tables
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)  # Clean up tables after tests

@pytest.fixture(scope="function")
def db_session():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)

    # Create a fresh session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

    # Clean up tables after tests
    Base.metadata.drop_all(bind=engine)
