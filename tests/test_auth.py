import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from pokeapi_fastapi.database.connection import get_db
from pokeapi_fastapi.database.models import Base
from pokeapi_fastapi.main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_register_user():
    response = client.post(
        "/auth/register",
        json={
            "username": "ash",
            "email": "ash@example.com",
            "password": "pikachu123",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "username": "ash",
        "email": "ash@example.com",
    }


def test_register_user_with_existing_email():
    user_data = {
        "username": "ash",
        "email": "ash@example.com",
        "password": "pikachu123",
    }

    client.post("/auth/register", json=user_data)
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


def test_login_user():
    client.post(
        "/auth/register",
        json={
            "username": "misty",
            "email": "misty@example.com",
            "password": "togepi123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "misty@example.com",
            "password": "togepi123",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Login successful",
        "user": {
            "id": 1,
            "username": "misty",
            "email": "misty@example.com",
        },
    }


def test_login_user_with_invalid_password():
    client.post(
        "/auth/register",
        json={
            "username": "brock",
            "email": "brock@example.com",
            "password": "onix123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "brock@example.com",
            "password": "wrong123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}
