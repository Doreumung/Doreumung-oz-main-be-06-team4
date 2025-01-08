import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

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


# @pytest.mark.asyncio
# async def test_create_review_handler(
#     async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute
# ) -> None:
#     user = setup_data
#     travelroute = setup_travelroute
#
#     # 실제 데이터베이스에 ReviewRepo 초기화
#     review_repo = ReviewRepo(async_session)
#
#     # 요청 데이터 생성
#     body_data: Dict[str, Any] = {
#         "user_id": user.id,
#         "travelroute_id": travelroute.id,
#         "title": "Test Review",
#         "rating": 5.0,
#         "content": "This is a test review content.",
#         "nickname": "test_user",
#     }
#     body = json.dumps(body_data)
#
#     # 이미지 URL 데이터 준비
#     image_urls = ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
#
#     # 핸들러 호출
#     result = await create_review_handler(
#         body=str(body),
#         files=None,
#         image_urls=image_urls,
#         review_repo=review_repo,
#     )
#
#     # 결과 검증
#     assert result.user_id == body_data["user_id"]
#     assert result.travelroute_id == body_data["travelroute_id"]
#     assert result.title == body_data["title"]
#     assert result.rating == body_data["rating"]
#     assert result.content == body_data["content"]
#
#     # 이미지 URL 검증
#     assert len(result.images) == len(image_urls)
#     for i, image in enumerate(result.images):
#         assert image.review_id == result.id
#         assert image.filepath == image_urls[i]
#         assert image.source_type == "link"
#
#     # 데이터베이스에서 리뷰 확인
#     saved_review = await async_session.get(Review, result.id)
#     assert saved_review is not None
#     assert saved_review.title == body_data["title"]
#     assert saved_review.content == body_data["content"]
#
#     # 데이터베이스에서 이미지 확인
#     saved_images_query = await async_session.execute(
#         select(ReviewImage).where(cast(ReviewImage.review_id, Integer) == result.id)
#     )
#     saved_images = saved_images_query.scalars().all()
#     assert len(saved_images) == len(image_urls)
#     for i, saved_image in enumerate(saved_images):
#         assert saved_image.filepath == image_urls[i]
#         assert saved_image.source_type == "link"
#
#     #  이미지 없이 리뷰 생성
#     result_without_images = await create_review_handler(
#         body=str(body),
#         files=None,
#         image_urls=None,  # 이미지 URL 없음
#         review_repo=review_repo,
#     )
#
#     # 결과 검증 (이미지 없음)
#     assert result_without_images.user_id == body_data["user_id"]
#     assert result_without_images.travelroute_id == body_data["travelroute_id"]
#     assert result_without_images.title == body_data["title"]
#     assert result_without_images.rating == body_data["rating"]
#     assert result_without_images.content == body_data["content"]
#
#     # 이미지가 없는지 확인
#     assert len(result_without_images.images) == 0
#
#     # 데이터베이스에서 리뷰 확인
#     saved_review_without_images = await async_session.get(Review, result_without_images.id)
#     assert saved_review_without_images is not None
#     assert saved_review_without_images.title == body_data["title"]
#     assert saved_review_without_images.content == body_data["content"]
#
#     # 이미지가 없는지 데이터베이스에서 확인
#     saved_images_query_without_images = await async_session.execute(
#         select(ReviewImage).where(ReviewImage.review_id == result_without_images.id)  # type: ignore
#     )
#     saved_images_without_images = saved_images_query_without_images.scalars().all()
#     assert len(saved_images_without_images) == 0
@pytest.mark.asyncio
async def test_create_review_handler(
    async_session: AsyncSession, setup_data: User, setup_travelroute: TravelRoute
) -> None:
    user = setup_data
    travelroute = setup_travelroute

    # 실제 데이터베이스에 ReviewRepo 초기화
    review_repo = ReviewRepo(async_session)

    # 요청 데이터 생성
    body_data: Dict[str, Any] = {
        "user_id": user.id,
        "travelroute_id": travelroute.id,
        "title": "Test Review",
        "rating": 5.0,
        "content": "This is a test review content.",
        "nickname": "test_user",
    }
    body = ReviewRequestBase(**body_data)

    # 핸들러 호출
    result = await create_review_handler(
        body=body,
        review_repo=review_repo,
    )

    # 결과 검증
    assert result.user_id == body_data["user_id"]
    assert result.travelroute_id == body_data["travelroute_id"]
    assert result.title == body_data["title"]
    assert result.rating == body_data["rating"]
    assert result.content == body_data["content"]

    # 데이터베이스에서 리뷰 확인
    saved_review = await async_session.get(Review, result.id)
    assert saved_review is not None
    assert saved_review.title == body_data["title"]
    assert saved_review.content == body_data["content"]


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

    # 리뷰 데이터 생성
    reviews = [
        Review(
            id=i,
            user_id=user.id,
            travelroute_id=travelroute.id,
            title=f"Review {i}",
            rating=4.5,
            content="This is a test review",
            created_at=datetime.now() - timedelta(minutes=i),
            updated_at=datetime.now(),
        )
        for i in range(1, 16)
    ]
    async_session.add_all(reviews)

    # 좋아요 데이터 생성
    likes = [Like(user_id=user.id, review_id=i, created_at=datetime.now()) for i in range(1, 6)]
    async_session.add_all(likes)

    # 사용자 닉네임 설정
    user.nickname = "test_nickname"
    async_session.add(user)

    # 커밋
    await async_session.commit()

    # 레포지토리 인스턴스 생성
    review_repo = ReviewRepo(async_session)

    # 테스트 파라미터 설정
    page = 1
    size = 5
    order_by = "created_at"
    order = "desc"

    # 첫 번째 페이지 테스트
    response = await get_all_review_handler(
        page=page,
        size=size,
        order_by=order_by,
        order=order,
        review_repo=review_repo,
    )

    # 응답 데이터 검증
    assert response["page"] == page
    assert response["size"] == size
    assert response["total_pages"] == 3
    assert len(response["reviews"]) == size

    # 첫 번째 리뷰 데이터 검증
    assert response["reviews"][0]["title"] == "Review 1"
    assert response["reviews"][0]["nickname"] == "test_nickname"
    assert "created_at" in response["reviews"][0]
    assert response["reviews"][0]["like_count"] == 1  # 첫 리뷰 좋아요 수

    # 정렬 검증 (내림차순 created_at)
    created_times = [datetime.fromisoformat(r["created_at"]) for r in response["reviews"]]
    assert all(created_times[i] >= created_times[i + 1] for i in range(len(created_times) - 1))

    # 페이지네이션 추가 테스트 (2페이지)
    response_page_2 = await get_all_review_handler(
        page=2,
        size=size,
        order_by=order_by,
        order=order,
        review_repo=review_repo,
    )
    assert response_page_2["page"] == 2
    assert len(response_page_2["reviews"]) == size
    assert response_page_2["reviews"][0]["title"] == "Review 6"

    # 마지막 페이지 테스트
    response_page_3 = await get_all_review_handler(
        page=3,
        size=size,
        order_by=order_by,
        order=order,
        review_repo=review_repo,
    )
    assert response_page_3["page"] == 3
    assert len(response_page_3["reviews"]) == 5
    assert response_page_3["reviews"][0]["title"] == "Review 11"


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
