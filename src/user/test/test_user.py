from datetime import date
from typing import Any, Dict, Generator
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.user.models.models import Gender, SocialProvider, User
from src.user.services.authentication import check_password


@pytest.fixture
def setup_database() -> Generator[Session, None, None]:
    engine = create_engine("postgresql:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()


@pytest.fixture
def user_data() -> Dict[str, Any]:
    return {
        "email": "test@example.com",
        "password": "plainpassword123",
        "username": "testuser",
        "nickname": "Tester",
        "birthday": date(1990, 1, 1),
        "gender": Gender.MALE,
        "phone_number": "010-1234-5678",
    }


@pytest.fixture
def mock_session() -> Mock:
    return Mock()


def test_create_user(user_data: Dict[str, Any], mock_session: Mock) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        username=user_data["username"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
        phone_number=user_data["phone_number"],
    )
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.nickname == user_data["nickname"]


def test_social_signup(mock_session: Mock) -> None:
    social_user = User.social_signup(
        social_provider=SocialProvider.GOOGLE,
        subject="google_unique_id",
        email="social@example.com",
        username="socialuser",
    )
    assert social_user.social_provider == SocialProvider.GOOGLE
    assert social_user.oauth_id is not None
    assert social_user.email == "social@example.com"


def test_update_password(user_data: Dict[str, Any]) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        username=user_data["username"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
        phone_number=user_data["phone_number"],
    )
    new_password = "newsecurepassword123"
    user.update_password(new_password)

    assert not check_password(user_data["password"], user.password)
    assert check_password(new_password, user.password)


def test_mark_as_deleted(user_data: Dict[str, Any]) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        username=user_data["username"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
        phone_number=user_data["phone_number"],
    )
    user.mark_as_deleted()
    assert user.is_deleted is True
    assert user.deleted_at is not None


def test_restore(user_data: Dict[str, Any]) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        username=user_data["username"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
        phone_number=user_data["phone_number"],
    )
    user.mark_as_deleted()
    user.restore()
    assert user.is_deleted is False
    assert user.deleted_at is None
