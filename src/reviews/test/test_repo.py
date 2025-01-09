import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator, Optional

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import select

from src.config.orm import Base
from src.reviews.models.models import Comment, Review, ReviewImage
from src.reviews.repo.review_repo import CommentRepo, ReviewRepo
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User


@pytest.fixture(scope="function")
def sample_review(setup_data: User, setup_travelroute: TravelRoute) -> list[Review]:
    review1 = Review(
        id=1,
        user_id=setup_data.id,
        travel_route_id=setup_travelroute.id,
        title="Test Review1",
        rating=4.5,
        content="This is the first test review",
        like_count=0,
        created_at=datetime(2025, 1, 1, 10, 0, 0),
    )
    review2 = Review(
        id=2,
        user_id=setup_data.id,
        travel_route_id=setup_travelroute.id,
        title="Test Review2",
        rating=4.0,
        content="This is the second test review",
        like_count=1,
        created_at=datetime(2025, 1, 2, 12, 0, 0),
    )
    return [review1, review2]


@pytest.mark.asyncio(scope="function")
async def test_save_review(async_session: AsyncSession, sample_review: list[Review]) -> None:
    repo = ReviewRepo(session=async_session)
    sample_review_test = await repo.save_review(sample_review[0])

    assert sample_review_test is not None
    assert sample_review_test.title == "Test Review1"


@pytest.mark.asyncio(scope="function")
async def test_get_review_by_id(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add(sample_review[0])
    await async_session.commit()

    repo = ReviewRepo(session=async_session)
    retrieved_review = await repo.get_review_by_id(sample_review[0].id)

    assert retrieved_review is not None
    assert retrieved_review.title == sample_review[0].title


@pytest.mark.asyncio
async def test_get_all_reviews(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()

    repo = ReviewRepo(session=async_session)

    # 모든 리뷰 조회
    retrieved_reviews = await repo.get_all_reviews(order_by="created_at", order="asc")

    assert retrieved_reviews is not None
    assert len(retrieved_reviews) == len(sample_review)

    assert retrieved_reviews[0].title == sample_review[0].title
    assert retrieved_reviews[1].title == sample_review[1].title


@pytest.mark.asyncio
async def test_delete_review(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()
    repo = ReviewRepo(session=async_session)
    # 첫 번째 리뷰 삭제
    await repo.delete_review(sample_review[0])

    # 삭제된 리뷰를 다시 조회
    with pytest.raises(HTTPException) as exc_info:
        await repo.get_review_by_id(sample_review[0].id)

    # 검증: 404 에러 발생 여부 확인
    assert exc_info.value.status_code == 404
    assert "Review does not exist" in exc_info.value.detail

    # 남은 리뷰 확인
    remaining_reviews = await repo.get_all_reviews()
    assert len(remaining_reviews) == len(sample_review) - 1


@pytest.mark.asyncio
async def test_add_review_like(async_session: AsyncSession, sample_review: list[Review]) -> None:
    # 샘플 리뷰 데이터 초기화
    for review in sample_review:
        review.like_count = 0
    async_session.add_all(sample_review)
    await async_session.commit()

    repo = ReviewRepo(session=async_session)
    review = sample_review[0]
    like = review.like_count

    updated_like = await repo.add_review_like(review.id)
    assert updated_like is not None
    assert updated_like.like_count == like + 1


@pytest.mark.asyncio
async def test_delete_like(async_session: AsyncSession, sample_review: list[Review]) -> None:
    # 샘플 리뷰 데이터 초기화
    for review in sample_review:
        review.like_count = 1
    async_session.add_all(sample_review)
    await async_session.commit()

    repo = ReviewRepo(session=async_session)
    review = sample_review[0]
    like = review.like_count

    updated_like = await repo.delete_review_like(review.id)
    assert updated_like is not None
    assert updated_like.like_count == like - 1


@pytest.mark.asyncio
async def test_save_image(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()
    image_data = ReviewImage(
        id=1,
        review_id=sample_review[0].id,
        filepath="images/test_image.jpg",
        source_type="upload",
    )
    repo = ReviewRepo(session=async_session)
    saved_image = await repo.save_image(image_data)

    assert saved_image is not None
    assert saved_image.review_id == sample_review[0].id
    assert saved_image.filepath == "images/test_image.jpg"
    assert saved_image.source_type == "upload"


@pytest.mark.asyncio
async def test_get_image_by_id(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()
    image_data = ReviewImage(
        id=1,
        review_id=sample_review[0].id,
        filepath="images/test_image.jpg",
        source_type="upload",
    )
    repo = ReviewRepo(session=async_session)
    saved_image = await repo.save_image(image_data)

    # ID로 이미지 가져오기
    if saved_image is not None:
        images = await repo.get_image_by_id(saved_image.id)
    else:
        images = None

    # 반환된 이미지 리스트 확인
    assert images is not None  # None이 아님을 확인
    assert len(images) > 0  # 적어도 하나 이상의 이미지가 있어야 함

    # 리스트 내 각 이미지 검증
    for image in images:
        assert image.review_id == sample_review[0].id
        assert image.filepath == "images/test_image.jpg"
        assert image.source_type == "upload"


@pytest.mark.asyncio
async def test_delete_image(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()
    image_data = ReviewImage(
        id=1,
        review_id=sample_review[0].id,
        filepath="images/test_image.jpg",
        source_type="upload",
    )
    repo = ReviewRepo(session=async_session)
    saved_image = await repo.save_image(image_data)

    assert saved_image is not None

    await repo.delete_image(saved_image.id)
    result = await async_session.execute(select(ReviewImage).where(ReviewImage.id == saved_image.id))
    deleted_image = result.scalars().first()
    assert deleted_image is None


@pytest.mark.asyncio
async def test_create_comment(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()

    comment_data = Comment(
        id=1,
        user_id=sample_review[0].user_id,
        review_id=sample_review[0].id,
        content="Test comment",
    )
    repo = CommentRepo(session=async_session)
    save_comment = await repo.create_comment(comment_data)
    assert save_comment is not None
    result = await async_session.execute(select(Comment).where(Comment.id == save_comment.id))
    comment = result.scalars().first()
    assert comment is not None
    assert comment.content == "Test comment"
    assert comment.review_id == sample_review[0].id


@pytest.mark.asyncio
async def test_get_comment_by_id(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()
    # 댓글 생성
    comment_data = Comment(
        id=1,
        user_id=sample_review[0].user_id,
        review_id=sample_review[0].id,
        content="Test comment",
    )
    async_session.add(comment_data)
    await async_session.commit()

    # 댓글 조회
    repo = CommentRepo(async_session)
    retrieved_comment = await repo.get_comment_by_id(comment_data.id)

    assert retrieved_comment is not None
    assert retrieved_comment.content == "Test comment"
    assert retrieved_comment.id == comment_data.id


@pytest.mark.asyncio
async def test_get_all_comment(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()

    comments = [
        Comment(user_id=sample_review[0].user_id, review_id=sample_review[0].id, content=f"Comment {i}")
        for i in range(5)
    ]
    async_session.add_all(comments)
    await async_session.commit()

    repo = CommentRepo(session=async_session)
    retrieved_comments = await repo.get_all_comment(review_id=sample_review[0].id)
    assert len(retrieved_comments) == 5
    assert retrieved_comments[0].content == "Comment 0"


@pytest.mark.asyncio
async def test_delete_comment(async_session: AsyncSession, sample_review: list[Review]) -> None:
    async_session.add_all(sample_review)
    await async_session.commit()
    # 댓글 생성
    comment_data = Comment(
        id=1,
        user_id=sample_review[0].user_id,
        review_id=sample_review[0].id,
        content="Test comment",
    )
    async_session.add(comment_data)
    await async_session.commit()

    repo = CommentRepo(session=async_session)
    await repo.delete_comment(comment_data.id)

    deleted_comment = await repo.get_comment_by_id(comment_data.id)
    assert deleted_comment is None


#
