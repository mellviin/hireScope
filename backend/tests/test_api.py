# Backend Tests
"""
Comprehensive test suite for HireScope backend
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.models.user import User
from app.utils.auth import hash_password

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestAuth:
    """Test authentication endpoints"""
    
    def test_signup(self):
        """Test user registration"""
        response = client.post("/api/auth/signup", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        })
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
    
    def test_signup_duplicate_email(self):
        """Test duplicate email handling"""
        # Create first user
        client.post("/api/auth/signup", json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "pass123",
        })
        
        # Try to create second user with same email
        response = client.post("/api/auth/signup", json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "pass123",
        })
        assert response.status_code == 400
    
    def test_login(self):
        """Test user login"""
        # Create user
        client.post("/api/auth/signup", json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "testpass123",
        })
        
        # Login
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "testpass123",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_password(self):
        """Test login with invalid password"""
        # Create user
        client.post("/api/auth/signup", json={
            "email": "invalid@example.com",
            "username": "invaliduser",
            "password": "correctpass",
        })
        
        # Try wrong password
        response = client.post("/api/auth/login", json={
            "email": "invalid@example.com",
            "password": "wrongpass",
        })
        assert response.status_code == 401


class TestHealth:
    """Test health endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "HireScope" in response.json()["message"]


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """Cleanup test database after tests"""
    yield
    import os
    if os.path.exists("test.db"):
        os.remove("test.db")
