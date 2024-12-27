from typing import Any, Generator
from unittest.mock import AsyncMock

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.main import app
from src.user.models.models import User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import encode_refresh_token


@pytest.fixture
def setup_database() -> Generator[Session, None, None]:
    engine = create_engine("postgresql:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()


@pytest.fixture
def mock_user_repo() -> Any:
    repo = AsyncMock(UserRepository)
    repo.get_user_by_email = AsyncMock(return_value=None)
    repo.get_user_by_id = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    return repo


def test_sign_up(mock_user_repo: AsyncMock) -> None:
    app.dependency_overrides[UserRepository] = lambda: mock_user_repo

    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "username": "testuser",
        "nickname": "tester",
        "phone_number": "010-1234-5678",
        "gender": "male",
        "birthday": "1990-01-01",
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/user/signup", json=signup_data)

    assert response.status_code == 201
    assert response.json()["email"] == signup_data["email"]
    mock_user_repo.save.assert_awaited_once()

    app.dependency_overrides = {}


def test_login(mock_user_repo: AsyncMock) -> None:
    app.dependency_overrides[UserRepository] = lambda: mock_user_repo
    plain_password = "password123"
    hashed_password = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    mock_user = User(
        id=1,
        email="test@example.com",
        password=hashed_password,
        username="testuser",
        nickname="tester",
        phone_number="010-1234-5678",
        gender="male",
        birthday="1990-01-01",
    )
    mock_user_repo.get_user_by_email.return_value = mock_user
    login_data = {"email": "test@example.com", "password": plain_password}

    with TestClient(app) as client:
        response = client.post("/api/v1/user/login", json=login_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    mock_user_repo.get_user_by_email.assert_called_once_with(email="test@example.com")

    app.dependency_overrides = {}


def test_refresh_token(mock_user_repo: AsyncMock) -> None:
    app.dependency_overrides[UserRepository] = lambda: mock_user_repo
    refresh_token = encode_refresh_token(user_id=1)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/refresh",
            json={"refresh_token": refresh_token},
        )

    assert response.status_code == 200
    assert "access_token" in response.json()
    app.dependency_overrides = {}
