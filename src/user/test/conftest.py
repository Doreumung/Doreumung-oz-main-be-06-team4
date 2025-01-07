import asyncio
from typing import AsyncGenerator, Generator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.config.orm import Base

DATABASE_URL = settings.TEST_ASYNC_DATABASE_URL

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
