from datetime import date
from typing import Any, Dict, Generator
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.user.models.models import Gender, SocialProvider, User
from src.user.services.authentication import check_password


@pytest.fixture
def user_data() -> Dict[str, Any]:
    return {
        "email": "test@example.com",
        "password": "plainpassword123",
        "nickname": "Tester",
        "birthday": date(1990, 1, 1),
        "gender": Gender.MALE,
    }


@pytest.fixture
def mock_session() -> Mock:
    return Mock()


def test_create_user(user_data: Dict[str, Any], mock_session: Mock) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
    )
    assert user.email == user_data["email"]
    assert user.nickname == user_data["nickname"]


def test_social_signup(mock_session: Mock) -> None:
    social_user = User.social_signup(
        social_provider=SocialProvider.GOOGLE,
        subject="google_unique_id",
        email="social@example.com",
        nickname="tester",
    )
    assert social_user.social_provider == SocialProvider.GOOGLE
    assert social_user.oauth_id is not None
    assert social_user.email == "social@example.com"
    assert social_user.nickname == "tester"


def test_update_password(user_data: Dict[str, Any]) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
    )
    new_password = "newsecurepassword123"
    user.update_password(new_password)

    assert not check_password(user_data["password"], user.password)
    assert check_password(new_password, user.password)


def test_mark_as_deleted(user_data: Dict[str, Any]) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
    )
    user.mark_as_deleted()
    assert user.is_deleted is True
    assert user.deleted_at is not None


def test_restore(user_data: Dict[str, Any]) -> None:
    user = User.create(
        email=user_data["email"],
        password=user_data["password"],
        nickname=user_data["nickname"],
        birthday=user_data["birthday"],
        gender=user_data["gender"],
    )
    user.mark_as_deleted()
    user.restore()
    assert user.is_deleted is False
    assert user.deleted_at is None
