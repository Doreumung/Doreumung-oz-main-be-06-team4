from typing import AsyncGenerator, Generator

import alembic
import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.connection_async import close_db_connection, get_async_session
from src.config import settings


@pytest.fixture(scope="function", autouse=True)
def setup_test_db() -> Generator[None, None, None]:
    engine = create_engine(settings.test_async_database_url.replace("asyncpg", "psycopg2"))
    # 테스트 DB 마이그레이션
    alembic_cfg = Config("alembic.ini")
    alembic.command.upgrade(alembic_cfg, "head")

    yield  # 테스트 실행

    # 테스트 후 DB 초기화
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    engine.dispose()
    # 매번 초기화하여 dev환경이랑 완전히 똑같이 스키마를 구성함


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        try:
            yield session
        finally:
            await session.close()
    await close_db_connection()
