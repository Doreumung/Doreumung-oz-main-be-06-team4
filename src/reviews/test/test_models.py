import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator, Optional, cast

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.orm import Base
from src.reviews.models.models import Comment, Like, Review, ReviewImage
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User

DATABASE_URL = "postgresql+asyncpg://postgres:0000@localhost:5432/testdb"

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


@pytest.mark.asyncio
async def test_review_model(async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute) -> None:
    user = setup_data

    # 테스트 데이터 생성
    review = Review(
        user_id=str(user.id),
        travelroute_id=int(cast(int, setup_travelroute.id)),
        title="Test Review",
        rating=5,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()

    # 데이터 확인
    result = await async_session.execute(select(Review).filter_by(title="Test Review"))
    retrieved_review = result.scalars().first()

    assert retrieved_review is not None
    assert retrieved_review.user_id == user.id
    assert retrieved_review.rating == 5


@pytest.mark.asyncio
async def test_image_relationship(
    async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute
) -> None:
    user = setup_data
    review = Review(
        user_id=str(user.id),
        travelroute_id=int(cast(int, setup_travelroute.id)),
        title="Test Review",
        rating=5,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()

    # 이미지 생성
    review_image_upload = ReviewImage(review_id=review.id, filepath="/images/test_upload.jpg", source_type="upload")
    review_image_link = ReviewImage(review_id=review.id, filepath="https://example.com/image.jpg", source_type="link")

    async_session.add_all([review_image_upload, review_image_link])
    await async_session.commit()

    # 데이터 검증
    result = await async_session.execute(select(Review).filter_by(title="Test Review"))
    retrieved_review = result.scalars().first()

    assert retrieved_review is not None
    assert len(retrieved_review.images) == 2

    # 업로드 된 이미지 확인
    uploaded_image = next((img for img in retrieved_review.images if img.source_type == "upload"), None)
    assert uploaded_image is not None
    assert uploaded_image.filepath == "/images/test_upload.jpg"
    # 링크 이미지 확인
    liked_image = next((img for img in retrieved_review.images if img.source_type == "link"), None)
    assert liked_image is not None
    assert liked_image.filepath == "https://example.com/image.jpg"


@pytest.mark.asyncio
async def test_comment_model(async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute) -> None:
    user = setup_data
    review = Review(
        user_id=str(user.id),
        travelroute_id=int(cast(int, setup_travelroute.id)),
        title="Test Review",
        rating=5,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()

    comment = Comment(
        user_id=str(user.id),
        review_id=review.id,
        content="Test content",
    )
    async_session.add(comment)
    await async_session.commit()
    result = await async_session.execute(select(Comment).filter_by(content="Test content"))
    retrieved_comment = result.scalars().first()
    assert retrieved_comment is not None
    assert retrieved_comment.user_id == user.id
    assert retrieved_comment.content == "Test content"
    assert retrieved_comment.created_at == comment.created_at
    assert retrieved_comment.updated_at == comment.updated_at


@pytest.mark.asyncio
async def test_like_model(async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute) -> None:
    user = setup_data

    review = Review(
        user_id=str(user.id),
        travelroute_id=int(cast(int, setup_travelroute.id)),
        title="Test Review",
        rating=5,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()

    like = Like(
        user_id=str(user.id),
        review_id=review.id,
    )
    async_session.add(like)
    await async_session.commit()
    result = await async_session.execute(select(Like).filter_by(id=like.id))
    retrieved_like = result.scalars().first()

    assert retrieved_like is not None
    assert retrieved_like.user_id == user.id
