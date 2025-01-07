import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import select

from src.config import settings
from src.config.orm import Base
from src.user.models.models import SocialProvider, User
from src.user.repo.repository import UserRepository


@pytest.fixture(scope="function")
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


@pytest.mark.asyncio(loop_scope="function")
async def test_save_user(async_session: AsyncSession, sample_user: User) -> None:
    repo = UserRepository(session=async_session)
    await repo.save(sample_user)

    result = await async_session.execute(select(User).where(User.id == sample_user.id))
    saved_user = result.unique().scalars().first()
    assert saved_user is not None
    assert saved_user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id(async_session: AsyncSession, sample_user: User) -> None:
    async_session.add(sample_user)
    await async_session.commit()

    repo = UserRepository(session=async_session)
    user = await repo.get_user_by_id(user_id=sample_user.id)

    assert user is not None
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email(async_session: AsyncSession, sample_user: User) -> None:
    # 샘플 사용자 추가
    async_session.add(sample_user)
    await async_session.commit()

    # UserRepository를 통해 사용자 조회
    repo = UserRepository(session=async_session)
    user_email = await repo.get_user_by_email(email=sample_user.email)  # 중복 결과가 없다면 이 단계에서 처리 가능

    # 검증
    assert user_email is not None
    assert user_email.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_social_email(async_session: AsyncSession, sample_user: User) -> None:
    sample_user.social_provider = SocialProvider.KAKAO
    async_session.add(sample_user)
    await async_session.commit()
    # 리포지토리 메서드 호출
    repo = UserRepository(session=async_session)
    social_user = await repo.get_user_by_social_email(
        social_provider=sample_user.social_provider, email=sample_user.email
    )
    # 결과 검증
    assert social_user is not None
    assert social_user.email == sample_user.email
    assert social_user.social_provider == sample_user.social_provider


@pytest.mark.asyncio
async def test_delete_user(async_session: AsyncSession, sample_user: User) -> None:
    async_session.add(sample_user)
    await async_session.commit()

    repo = UserRepository(session=async_session)
    await repo.delete(sample_user)

    result = await async_session.execute(select(User).where(User.id == sample_user.id))
    deleted_user = result.unique().scalar_one_or_none()
    assert deleted_user is None
