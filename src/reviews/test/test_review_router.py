from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pytest
from fastapi import UploadFile
from sqlalchemy import Integer, cast, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.reviews.dtos.request import ReviewRequestBase
from src.reviews.dtos.response import ReviewResponse
from src.reviews.models.models import Like, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.router.review_router import (
    create_review_handler,
    delete_review_handler,
    get_all_review_handler,
    get_review_handler,
    update_review_handler,
)
from src.reviews.test.conftest import KST
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User
from src.user.repo.repository import UserRepository

"""
리뷰 생성 test code
"""


@pytest.mark.asyncio
async def test_create_review_handler(
    async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute
) -> None:
    user = setup_data
    travelroute = setup_data

    # 실제 데이터베이스에 ReviewRepo 초기화
    review_repo = ReviewRepo(async_session)

    # 요청 데이터 생성
    body_data = {
        "user_id": user.id,
        "travelroute_id": travelroute.id,
        "title": "Test Review",
        "rating": 5.0,
        "content": "This is a test review content.",
        "nickname": "test_user",
        "images": [],
    }
    body = ReviewRequestBase(**body_data)  # type: ignore

    # 이미지 URL 데이터 준비
    image_urls = ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]

    # 핸들러 호출
    result = await create_review_handler(
        body=body,
        files=None,
        image_urls=image_urls,
        review_repo=review_repo,
    )

    # 결과 검증
    assert result.user_id == body.user_id
    assert result.travelroute_id == body.travelroute_id
    assert result.title == body.title
    assert result.rating == body.rating
    assert result.content == body.content

    # 데이터베이스에서 리뷰 확인
    saved_review = await async_session.get(Review, result.id)
    assert saved_review is not None
    assert saved_review.title == body.title


"""
리뷰 단일 조회 test code
"""


@pytest.mark.asyncio
async def test_get_review_handler(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    user = setup_data
    travelroute = setup_travelroute
    review_data = {
        "id": 1,
        "user_id": user.id,
        "travelroute_id": travelroute.id,
        "title": "Test Review",
        "rating": 5.0,
        "content": "This is a test review content.",
        "like_count": 0,
        "created_at": datetime.now(),  # 현재 시간으로 설정
        "updated_at": datetime.now(),
    }
    await async_session.execute(insert(Review).values(review_data))
    await async_session.commit()

    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    response = await get_review_handler(
        review_id=1,
        user_id=user.id,
        review_repo=review_repo,
        user_repo=user_repo,
    )
    assert isinstance(response, ReviewResponse)
    assert response.id == review_data["id"]
    assert response.title == review_data["title"]
    assert response.nickname == user.nickname


"""
review list 조회 테스트
"""


@pytest.mark.asyncio
async def test_get_all_review_handler(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    user = setup_data
    travelroute = setup_travelroute
    reviews = [
        Review(
            id=i,
            user_id=user.id,
            travelroute_id=travelroute.id,
            title=f"Review {i}",
            rating=4.5,
            content="This is a test review",
            like_count=0,
            created_at=datetime.now() - timedelta(minutes=i),
            updated_at=datetime.now(),
        )
        for i in range(1, 16)
    ]
    async_session.add_all(reviews)
    like = Like(
        user_id=user.id,
        review_id=1,
        created_at=datetime.now(),
    )
    async_session.add(like)

    user.nickname = "test_nickname"
    async_session.add(user)

    await async_session.commit()
    review_repo = ReviewRepo(async_session)

    # 테스트 파라미터 설정
    page = 1
    size = 5
    order_by = "created_at"
    order = "desc"

    response = await get_all_review_handler(
        page=page,
        size=size,
        order_by=order_by,
        order=order,
        user_id=user.id,
        travelroute_id=travelroute.id,
        review_repo=review_repo,
    )
    # 결과
    assert response["page"] == page
    assert response["size"] == size
    assert response["total_pages"] == 3
    assert len(response["reviews"]) == size

    # 좋아요 확인
    assert response["reviews"][0]["id"] == 1
    assert response["reviews"][0]["liked_by_user"] is True

    # 정렬
    assert response["reviews"][0]["created_at"] > response["reviews"][1]["created_at"]

    # 페이지네이션 추가 테스트
    response_page_2 = await get_all_review_handler(
        page=2,
        size=size,
        order_by=order_by,
        order=order,
        user_id=user.id,
        travelroute_id=travelroute.id,
        review_repo=review_repo,
    )
    assert response_page_2["page"] == 2
    assert len(response_page_2["reviews"]) == size


"""
# 리뷰 수정 테스트
"""


@pytest.mark.asyncio
async def test_update_review_handler(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    user = setup_data
    travelroute = setup_travelroute
    review_id = 1
    review = Review(
        id=review_id,
        user_id=user.id,
        travelroute_id=travelroute.id,
        title="Test Review",
        content="This is a test review content.",
        rating=4.0,
        created_at=datetime.now(KST),
        updated_at=datetime.now(KST),
    )
    async_session.add(review)
    await async_session.commit()
    review_repo = ReviewRepo(async_session)

    body = ReviewRequestBase(
        user_id=user.id,
        travelroute_id=travelroute.id,
        nickname=user.nickname,
        title="Update Title",
        content="Update Content",
        rating=5.0,
    )
    image_urls = ["https://example.com/image1.jpg"]
    files: List[UploadFile] = []

    response = await update_review_handler(
        review_id=review_id,
        body=body,
        files=files,
        image_urls=image_urls,
        review_repo=review_repo,
        user_id=user.id,
    )
    assert response.title == "Update Title"
    assert response.content == "Update Content"
    assert response.rating == 5.0

    # 데이터베이스에서 업데이트 된 리뷰 확인
    updated_review = await async_session.get(Review, review_id)
    assert updated_review is not None
    assert updated_review.title == "Update Title"
    assert updated_review.content == "Update Content"
    assert updated_review.rating == 5.0
    assert updated_review.updated_at > updated_review.created_at

    # 이미지 URL 확인
    images = await async_session.execute(select(ReviewImage).where(cast(ReviewImage.review_id, Integer) == review_id))
    image_list = images.scalars().all()
    assert len(image_list) == 1
    assert image_list[0].filepath == "https://example.com/image1.jpg"
    assert image_list[0].source_type == "link"


"""
review 삭제 
"""


@pytest.mark.asyncio
async def test_delete_review_handler(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    user = setup_data
    travelroute = setup_travelroute
    review_id = 1
    review = Review(
        id=review_id,
        user_id=user.id,
        travelroute_id=travelroute.id,
        title="Test Review",
        content="This is a test review content.",
        rating=4.0,
        created_at=datetime.now(KST),
        updated_at=datetime.now(KST),
    )
    async_session.add(review)
    await async_session.commit()

    image = ReviewImage(id=1, review_id=review_id, source_type="upload", filepath="/tmp/test_image.jpg")
    async_session.add(image)
    await async_session.commit()

    # 가상 파일 생성
    test_file = Path(image.filepath)
    test_file.touch()

    review_repo = ReviewRepo(async_session)

    # 삭제 요청
    response = await delete_review_handler(
        review_id=review_id,
        review_repo=review_repo,
        user_id=user.id,
    )

    assert response["message"] == "Review deleted"
    # 삭제 확인
    deleted_review = await async_session.get(Review, review_id)
    assert deleted_review is None
    # 이미지 삭제 확인
    deleted_image = await async_session.get(ReviewImage, image.id)
    assert deleted_image is None
    # 파일 삭제 확인
    assert not test_file.exists()
