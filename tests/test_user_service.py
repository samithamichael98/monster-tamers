
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.user_service.main import app
from services.user_service.database import Base, get_db


# Separate in-memory database for testing
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


def register_test_user(client):
    return client.post(
        "/register",
        json={
            "username": "testplayer",
            "email": "testplayer@example.com",
            "password": "SecurePass123!",
        },
    )


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user_success(client):
    response = register_test_user(client)

    assert response.status_code == 201
    assert response.json()["username"] == "testplayer"
    assert response.json()["email"] == "testplayer@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_duplicate_username(client):
    register_test_user(client)

    response = client.post(
        "/register",
        json={
            "username": "testplayer",
            "email": "another@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 409


def test_register_duplicate_email(client):
    register_test_user(client)

    response = client.post(
        "/register",
        json={
            "username": "anotherplayer",
            "email": "testplayer@example.com",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 409


def test_register_invalid_email(client):
    response = client.post(
        "/register",
        json={
            "username": "testplayer",
            "email": "not-an-email",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/register",
        json={
            "username": "testplayer",
            "email": "testplayer@example.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_login_success(client):
    register_test_user(client)

    response = client.post(
        "/login",
        json={
            "username": "testplayer",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register_test_user(client)

    response = client.post(
        "/login",
        json={
            "username": "testplayer",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post(
        "/login",
        json={
            "username": "unknownplayer",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 401


def test_get_profile_without_token(client):
    register_test_user(client)

    response = client.get("/me")

    assert response.status_code == 401


def test_get_profile_with_invalid_token(client):
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_get_profile_with_valid_token(client):
    register_test_user(client)

    login_response = client.post(
        "/login",
        json={
            "username": "testplayer",
            "password": "SecurePass123!",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "testplayer"
    assert response.json()["email"] == "testplayer@example.com"
