from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

from sqlalchemy import Integer, cast, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.reviews.dtos.request import ReviewRequestBase, ReviewUpdateRequest
from src.reviews.dtos.response import GetReviewResponse, ReviewUpdateResponse
from src.reviews.models.models import Comment, Like
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.router.review_router import (
    create_review,
    delete_review_handler,
    get_all_review_handler,
    get_review_handler,
    update_review_handler,
)
from src.reviews.test.fixtures import KST
from src.travel.models.travel_route_place import TravelRoute
from src.user.models.models import User
from src.user.repo.repository import UserRepository

"""
리뷰 생성 test code
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from src.reviews.models.models import ImageSourceType, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.router.review_router import create_review


@pytest.mark.asyncio
async def test_create_review_with_deleted_urls() -> None:
    # Mock 데이터 설정
    mock_user_repo = AsyncMock()
    mock_review_repo = AsyncMock()

    # Mock된 사용자 데이터
    mock_user_repo.get_user_by_id.return_value = AsyncMock(id="user1", nickname="test_user")

    # Mock된 Travel Route 데이터
    mock_review_repo.get_travel_route_by_id.return_value = True

    # Mock된 삭제할 이미지 데이터
    mock_image = ReviewImage(
        id=1,
        filepath="https://bucket-name.s3.amazonaws.com/old_image.jpg",
        source_type=ImageSourceType.LINK.value,
    )
    mock_scalars = Mock(one_or_none=Mock(return_value=mock_image))
    mock_review_repo.session.execute.return_value = Mock(scalars=Mock(return_value=mock_scalars))
    mock_review_repo.delete_image = AsyncMock()

    # Mock된 리뷰 저장
    mock_saved_review = AsyncMock(
        id=1,
        user_id="user1",
        travel_route_id=1,
        title="Test Review",
        rating=4.5,
        content="This is a test review",
        like_count=0,
        created_at="2025-01-10T00:00:00",
        updated_at="2025-01-10T00:00:00",
        thumbnail="http://example.com/thumbnail.jpg",
        images=[],
    )
    mock_review_repo.save_review.return_value = mock_saved_review

    # Mock된 handle_image_urls
    with patch("src.reviews.router.review_router.handle_image_urls", AsyncMock(return_value=[])), patch(
        "src.reviews.router.review_router.s3_client.delete_object", return_value=None
    ):
        # 요청 데이터
        review_request = ReviewRequestBase(
            travel_route_id=1,
            title="Test Review",
            rating=4.5,
            content="This is a test review",
            thumbnail="http://example.com/thumbnail.jpg",
        )
        uploaded_urls = ["https://bucket-name.s3.amazonaws.com/new_image.jpg"]
        deleted_urls = ["https://bucket-name.s3.amazonaws.com/old_image.jpg"]

        # 테스트 실행
        response = await create_review(
            body=review_request,
            uploaded_urls=uploaded_urls,
            deleted_urls=deleted_urls,
            review_repo=mock_review_repo,
            user_repo=mock_user_repo,
            current_user_id="user1",
        )

    # Assertions
    assert response.review_id == 1
    assert response.nickname == "test_user"
    assert response.travel_route_id == 1
    assert response.title == "Test Review"
    assert response.rating == 4.5
    assert response.content == "This is a test review"
    assert response.like_count == 0
    assert response.thumbnail == "http://example.com/thumbnail.jpg"
    assert response.images == []

    # Mock 호출 확인
    mock_review_repo.get_travel_route_by_id.assert_called_once_with(1)
    mock_user_repo.get_user_by_id.assert_called_once_with(user_id="user1")
    mock_review_repo.delete_image.assert_called_once_with(1)  # `mock_image.id`의 값을 1로 설정


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
    travel_route = setup_travelroute
    # 리뷰 데이터 생성
    review_data = {
        "id": 1,
        "user_id": user.id,
        "travel_route_id": travel_route.id,
        "title": "Test Review",
        "rating": 5.0,
        "content": "This is a test review content.",
        "like_count": 0,
        "created_at": datetime.now(),  # 현재 시간으로 설정
        "updated_at": datetime.now(),
    }
    await async_session.execute(insert(Review).values(review_data))
    await async_session.commit()

    # 레포지토리 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 핸들러 호출
    response = await get_review_handler(
        review_id=1,
        user_id=user.id,
        review_repo=review_repo,
    )

    # 검증
    assert isinstance(response, GetReviewResponse)  # 반환값 검증
    assert response.review_id == review_data["id"]
    assert response.user_id == user.id
    assert response.title == review_data["title"]
    assert response.rating == review_data["rating"]
    assert response.content == review_data["content"]
    assert response.nickname == user.nickname
    assert response.travel_route_id == travel_route.id
    # assert len(response.travel_route) == travel_route.breakfast + travel_route.morning + travel_route.lunch + travel_route.afternoon + travel_route.dinner
    assert response.regions == [travel_route.regions]  # type: ignore
    assert response.themes == [travel_route.themes]  # type: ignore
    assert response.like_count == 0
    assert response.liked_by_user is False

    # 검증
    assert isinstance(response, GetReviewResponse)
    assert response.review_id == review_data["id"]
    assert response.user_id == review_data["user_id"]
    assert response.title == review_data["title"]
    assert response.rating == review_data["rating"]
    assert response.content == review_data["content"]
    assert response.nickname == user.nickname

    # 새로 추가된 필드 검증
    assert response.regions == ["제주시"]
    assert response.themes == ["자연"]


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
    travel_route = setup_travelroute

    # 리뷰 데이터 생성
    reviews = [
        Review(
            id=i,
            user_id=user.id,
            travel_route_id=travel_route.id,
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

    # 댓글 데이터 생성
    comments = [
        Comment(
            user_id=user.id,
            review_id=i,
            content=f"This is a comment for review {i}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        for i in range(1, 16)  # 각 리뷰에 댓글 1개씩 추가
        for _ in range(3)  # 각 리뷰에 3개의 댓글 생성
    ]
    async_session.add_all(comments)

    # 사용자 닉네임 설정
    user.nickname = "test_nickname"
    async_session.add(user)

    # 데이터베이스 커밋
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
    assert response["total_pages"] == 3  # 총 리뷰 개수 15, 페이지당 5개, 총 3페이지
    assert response["total_reviews"] == len(reviews)
    assert len(response["reviews"]) == size

    # 첫 번째 리뷰 데이터 검증
    assert response["reviews"][0]["title"] == "Review 1"  # 최신 리뷰 확인
    assert response["reviews"][0]["user_id"] == str(user.id)
    assert response["reviews"][0]["nickname"] == "test_nickname"
    assert "created_at" in response["reviews"][0]
    assert response["reviews"][0]["like_count"] == 1  # 첫 리뷰 좋아요 수
    assert response["reviews"][0]["comment_count"] == 3  # 첫 리뷰 댓글 수

    # 정렬 검증 (내림차순 created_at)
    created_times = [r["created_at"] for r in response["reviews"]]
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
    assert len(response_page_3["reviews"]) == 5  # 마지막 페이지에 5개 리뷰
    assert response_page_3["reviews"][0]["title"] == "Review 11"

    # 경계값 테스트 (없는 페이지)
    response_page_4 = await get_all_review_handler(
        page=4,  # 없는 페이지
        size=size,
        order_by=order_by,
        order=order,
        review_repo=review_repo,
    )
    assert response_page_4["page"] == 4
    assert len(response_page_4["reviews"]) == 0  # 데이터 없음


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
    travel_route = setup_travelroute
    review_id = 1

    # 기존 리뷰 생성
    initial_time = datetime.now(KST)
    review = Review(
        id=review_id,
        user_id=user.id,  # user_id를 올바르게 설정
        travel_route_id=travel_route.id,
        title="Test Review",
        content="This is a test review content.",
        rating=4.0,
        thumbnail="Old Thumbnail",
        created_at=initial_time,
        updated_at=initial_time,
    )
    async_session.add(review)
    await async_session.commit()

    # 리뷰 레포지토리 생성
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 업데이트 요청 데이터
    body = ReviewUpdateRequest(
        title="Updated Title",
        content="Updated Content",
        rating=5.0,
        thumbnail="Updated Thumbnail",
    )

    # 핸들러 호출
    response = await update_review_handler(
        review_id=review.id,
        body=body,
        review_repo=review_repo,
        user_id=user.id,
        user_repo=user_repo,
        deleted_images=[],
    )

    # 응답 데이터 검증
    assert isinstance(response, ReviewUpdateResponse)
    assert response.review_id == review.id
    assert response.title == "Updated Title"
    assert response.content == "Updated Content"
    assert response.rating == 5.0
    assert response.thumbnail == "Updated Thumbnail"
    assert response.nickname == user.nickname
    assert response.updated_at > initial_time

    # 데이터베이스에서 업데이트 된 리뷰 확인
    updated_review = await async_session.get(Review, review_id)
    assert updated_review is not None
    assert updated_review.title == "Updated Title"
    assert updated_review.content == "Updated Content"
    assert updated_review.rating == 5.0
    assert updated_review.thumbnail == "Updated Thumbnail"
    assert updated_review.updated_at > updated_review.created_at


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
    travel_route = setup_travelroute
    review_id = 1
    review = Review(
        id=review_id,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test Review",
        content="This is a test review content.",
        rating=4.0,
        created_at=datetime.now(KST),
        updated_at=datetime.now(KST),
    )
    async_session.add(review)
    await async_session.commit()

    # 댓글 생성
    comments = [
        Comment(
            id=i,
            review_id=review_id,
            user_id=user.id,
            content=f"Test comment {i}",
            created_at=datetime.now(KST),
            updated_at=datetime.now(KST),
        )
        for i in range(1, 4)  # 댓글 3개 생성
    ]
    async_session.add_all(comments)
    await async_session.commit()

    image = ReviewImage(
        id=1, user_id=user.id, review_id=review_id, source_type="upload", filepath="/tmp/test_image.jpg"
    )
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
    # 댓글 삭제 확인
    for comment in comments:
        deleted_comment = await async_session.get(Comment, comment.id)
        assert deleted_comment is None

    # 이미지 삭제 확인
    deleted_image = await async_session.get(ReviewImage, image.id)
    assert deleted_image is None
    # 파일 삭제 확인
    assert not test_file.exists()
