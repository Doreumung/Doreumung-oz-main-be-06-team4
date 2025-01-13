from typing import cast

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.reviews.models.models import Comment, Like, Review, ReviewImage
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User


@pytest.mark.asyncio
async def test_review_model(async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute) -> None:
    user = setup_data

    # 테스트 데이터 생성
    review = Review(
        user_id=str(user.id),
        travel_route_id=int(cast(int, setup_travelroute.id)),
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
        travel_route_id=int(cast(int, setup_travelroute.id)),
        title="Test Review",
        rating=5,
        content="Test content",
    )
    async_session.add(review)
    await async_session.commit()

    # 이미지 생성
    review_image_upload = ReviewImage(
        user_id=str(user.id), review_id=review.id, filepath="/images/test_upload.jpg", source_type="upload"
    )
    review_image_link = ReviewImage(
        user_id=str(user.id), review_id=review.id, filepath="https://example.com/image.jpg", source_type="link"
    )

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
        travel_route_id=int(cast(int, setup_travelroute.id)),
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
        travel_route_id=int(cast(int, setup_travelroute.id)),
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


#
