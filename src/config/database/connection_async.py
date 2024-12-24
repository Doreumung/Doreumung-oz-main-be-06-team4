from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import settings

async_engine = create_async_engine(settings.async_database_url)
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine, autocommit=False, autoflush=False, expire_on_commit=False
)

async def get_async_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()  # db에 커넥션 종료