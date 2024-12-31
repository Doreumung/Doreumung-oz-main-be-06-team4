import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings


def get_url():
    if os.getenv("TEST_ENV") == "true":
        return settings.test_async_database_url
    return settings.async_database_url


# 비동기 엔진 생성
async_engine = create_async_engine(get_url())

# 비동기 세션 팩토리
AsyncSessionFactory = async_sessionmaker(bind=async_engine, autocommit=False, autoflush=False, expire_on_commit=False)


# 세션을 생성하고 종료하는 비동기 제너레이터
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
        # 세션이 종료되면 자동으로 커넥션이 닫힘


# 애플리케이션 종료 시 엔진 정리
async def close_db_connection():
    await async_engine.dispose()
