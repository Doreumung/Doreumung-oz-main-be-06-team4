from typing import Generator
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository


@pytest.fixture
def setup_database() -> Generator[Session, None, None]:
    engine = create_engine("postgresql:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    yield db

    db.close()


@pytest.fixture
def mock_session() -> Mock:
    session = Mock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def sample_user() -> User:
    return User(
        id=1,
        email="test@example.com",
        password="hashedpassword123",
        username="testuser",
        nickname="Tester",
        birthday=None,
        gender=None,
        phone_number="010-1234-5678",
        social_provider=None,
    )


@pytest.mark.asyncio
async def test_save_user(mock_session: Mock, sample_user: User) -> None:
    repo = UserRepository(session=mock_session)
    await repo.save(sample_user)

    mock_session.add.assert_called_once_with(sample_user)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_id(mock_session: Mock, sample_user: User) -> None:
    mock_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=sample_user)

    repo = UserRepository(session=mock_session)
    user = await repo.get_user_by_id(user_id=1)

    mock_session.execute.assert_called_once()
    assert await mock_session.execute.return_value.scalar_one_or_none() == sample_user


@pytest.mark.asyncio
async def test_get_user_by_email(mock_session: Mock, sample_user: User) -> None:
    mock_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=sample_user)

    repo = UserRepository(session=mock_session)
    user = await repo.get_user_by_email(email="test@example.com")

    mock_session.execute.assert_called_once()
    assert await mock_session.execute.return_value.scalar_one_or_none() == sample_user


@pytest.mark.asyncio
async def test_get_user_by_social_email(mock_session: Mock, sample_user: User) -> None:
    mock_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=sample_user)

    repo = UserRepository(session=mock_session)
    user = await repo.get_user_by_social_email(social_provider=SocialProvider.KAKAO, email="test@example.com")

    mock_session.execute.assert_called_once()
    assert await mock_session.execute.return_value.scalar_one_or_none() == sample_user


@pytest.mark.asyncio
async def test_delete_user(mock_session: Mock, sample_user: User) -> None:
    repo = UserRepository(session=mock_session)
    await repo.delete(sample_user)

    mock_session.delete.assert_called_once_with(sample_user)
    mock_session.commit.assert_called_once()
