from datetime import timedelta
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.user.services.authentication import (
    check_password,
    decode_access_token,
    encode_access_token,
    hash_password,
)


@pytest.fixture
def setup_database() -> Generator[Session, None, None]:
    engine = create_engine("postgresql:///:memory:")  # SQLite 메모리 데이터베이스
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()


@pytest.fixture
def sample_password() -> str:
    return "securepassword123"


@pytest.fixture
def hashed_password(sample_password: str) -> str:
    return hash_password(sample_password)


def test_hash_password(sample_password: str) -> None:
    hashed = hash_password(sample_password)
    assert hashed != sample_password
    assert hashed.startswith("$2b$")


def test_check_password(sample_password: str, hashed_password: str) -> None:
    assert check_password(sample_password, hashed_password) is True
    assert check_password("wrongpassword", hashed_password) is False


def test_encode_access_token() -> None:
    user_id = 123
    token = encode_access_token(user_id=user_id)
    assert isinstance(token, str)


def test_decode_access_token() -> None:
    user_id = 123
    token = encode_access_token(user_id=user_id)
    decoded = decode_access_token(token)
    assert decoded["user_id"] == user_id


def test_access_token_expiry() -> None:
    user_id = 123
    token = encode_access_token(user_id=user_id, expires_delta=timedelta(seconds=1))

    import time

    time.sleep(2)  # 만료 시간을 초과
    with pytest.raises(Exception):
        decode_access_token(token)
