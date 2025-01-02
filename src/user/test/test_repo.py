from typing import Generator
from unittest.mock import AsyncMock, Mock
from sqlalchemy.future import select

import pytest
from select import select
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker

from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository


@pytest.fixture(scope="function")
def setup_database() -> Generator[Session, None, None]:
    engine = create_engine("postgresql://user:password@localhost/test_db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    User.metadata.create_all(engine)

    try:
        yield db
    finally:
        # Clean up database state after each test
        db.query(User).delete()
        db.commit()
        db.close()



@pytest.fixture
def sample_user() -> User:
    return User(
        id="1",
        email="test@example.com",
        password="hashedpassword123",
        nickname="Tester",
        birthday=None,
        gender=None,
        social_provider=None,
    )


@pytest.mark.asyncio
async def test_save_user(setup_database: AsyncSession, sample_user: User) -> None:
    repo = UserRepository(session=setup_database)
    await repo.save(sample_user)

    # Verify that the user was saved
    result = await setup_database.execute(select(User).filter_by(User.id == sample_user.id))
    saved_user = result.scalar().first()
    assert saved_user is not None
    assert saved_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id(mock_session: Mock, sample_user: User) -> None:
    mock_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=sample_user)

    repo = UserRepository(session=mock_session)
    user = await repo.get_user_by_id(user_id="1")

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
