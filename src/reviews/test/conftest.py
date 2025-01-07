import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator, Optional

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.orm import Base
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User

DATABASE_URL = "postgresql+asyncpg://postgres:0000@localhost:5432/doreumung"

# 비동기 엔진 생성
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

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


@pytest_asyncio.fixture(scope="function")
async def setup_data(async_session: AsyncSession) -> Optional[User]:
    user = User(
        id="1",
        email="test@example.com",
        password="test",
        nickname="test",
        updated_at=datetime.now(),
        created_at=datetime.now(),
    )
    async_session.add(user)
    await async_session.commit()

    return await async_session.get(User, "1")


@pytest_asyncio.fixture(scope="function")
async def setup_travelroute(async_session: AsyncSession, setup_data: User) -> Optional[TravelRoute]:
    route = TravelRoute(
        id=1,
        user_id="1",
        regions="제주시",
        themes="자연",
        breakfast=True,
        morning=1,
        lunch=True,
        afternoon=1,
        dinner=True,
    )
    async_session.add(route)
    await async_session.commit()
    return await async_session.get(TravelRoute, 1)
