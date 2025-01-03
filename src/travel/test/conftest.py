import asyncio
import time
from typing import AsyncGenerator, Generator

import alembic
import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.config.database.connection_async import close_db_connection, get_async_session
from src.config.orm import Base
from src.travel.repo.place_repo import PlaceRepository
from src.travel.repo.travel_route_place_repo import TravelRoutePlaceRepository
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.user.repo.repository import UserRepository

engine = create_async_engine(settings.TEST_ASYNC_DATABASE_URL, echo=True, future=True)

# 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    # 세션 범위의 이벤트 루프를 설정
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    # 테스트용 데이터베이스 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    # 테스트 후 데이터베이스 정리
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def travel_route_place_repository(async_session: AsyncSession) -> TravelRoutePlaceRepository:
    return TravelRoutePlaceRepository(async_session)


@pytest.fixture
def travel_route_repository(async_session: AsyncSession) -> TravelRouteRepository:
    return TravelRouteRepository(async_session)


@pytest.fixture
def place_repository(async_session: AsyncSession) -> PlaceRepository:
    return PlaceRepository(async_session)


@pytest.fixture
def user_repository(async_session: AsyncSession) -> UserRepository:
    return UserRepository(async_session)
