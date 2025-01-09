from datetime import datetime, timedelta, timezone
from sys import exc_info

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import TravelRoute  # type: ignore
from src.reviews.dtos.request import CommentRequest
from src.reviews.dtos.response import CommentResponse
from src.reviews.models.models import Comment, Review
from src.reviews.repo.review_repo import CommentRepo, ReviewRepo
from src.reviews.router.comment_router import (
    comment_router,
    create_comment,
    delete_comment,
    get_comment,
    update_comment,
)
from src.user.models.models import User
from src.user.repo.repository import UserRepository


@pytest.mark.asyncio
async def test_create_comment(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # 주어진 User와 TravelRoute를 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="test title",
        rating=4.5,
        content="This is a test review",
        comment_count=3,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 요청 데이터 생성
    request_body = CommentRequest(content="This is a test comment.")
    comment_repo = CommentRepo(async_session)
    user_repo = UserRepository(async_session)

    # 핸들러 호출
    response = await create_comment(
        review_id=1,
        body=request_body,
        user_id=user.id,
        user_repo=user_repo,
        comment_repo=comment_repo,
    )

    # 검증
    assert isinstance(response, CommentResponse)
    assert response.nickname == user.nickname
    assert response.review_id == review.id
    assert response.content == request_body.content
    assert response.created_at is not None

    # 데이터베이스에 저장된 댓글 확인
    saved_comment = await async_session.get(Comment, response.comment_id)  # 수정된 부분
    assert saved_comment is not None
    assert saved_comment.user_id == user.id  # user_id가 일치하는지 확인
    assert saved_comment.review_id == response.review_id
    assert saved_comment.content == response.content
    assert saved_comment.created_at == response.created_at  # 생성된 시간이 일치하는지 확인


@pytest.mark.asyncio
async def test_get_comments(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # 주어진 User와 TravelRoute를 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        comment_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 댓글 객체 생성
    comment1 = Comment(
        review_id=review.id,
        user_id=user.id,
        content="Test comment 1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    comment2 = Comment(
        review_id=review.id,
        user_id=user.id,
        content="Test comment 2",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    async_session.add(comment1)
    async_session.add(comment2)
    await async_session.commit()

    # 요청 데이터 생성
    comment_repo = CommentRepo(async_session)
    user_repo = UserRepository(async_session)

    # 핸들러 호출
    response = await get_comment(
        review_id=review.id,
        comment_repo=comment_repo,
        user_repo=user_repo,
    )

    # 검증
    assert len(response) == 2
    assert response[0].comment_id == comment1.id
    assert response[0].content == comment1.content
    assert response[1].comment_id == comment2.id
    assert response[1].content == comment2.content
    assert response[0].nickname == user.nickname
    assert response[1].nickname == user.nickname
    # 생성된 시간 검증
    assert isinstance(response[0].created_at, datetime)
    assert isinstance(response[1].created_at, datetime)


@pytest.mark.asyncio
async def test_update_comment(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute
    seoul_tz = timezone(timedelta(hours=9))

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        comment_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 댓글 객체 생성
    comment = Comment(
        review_id=review.id,
        user_id=user.id,
        content="Test comment content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(comment)
    await async_session.commit()

    # 요청 데이터 생성
    request_body = CommentRequest(content="Updated comment content")
    comment_repo = CommentRepo(async_session)
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 테스트할 엔드포인트 호출
    response = await update_comment(
        comment_id=comment.id,
        body=request_body,
        user_id=user.id,
        user_repo=user_repo,
        review_repo=review_repo,
        comment_repo=comment_repo,
    )

    # 검증
    assert response.comment_id == comment.id
    assert response.nickname == user.nickname
    assert response.content == "Updated comment content"
    assert response.message == "댓글이 성공적으로 수정되었습니다"
    assert isinstance(response.updated_at, datetime)


@pytest.mark.asyncio
async def test_update_comment_user_not_found(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        comment_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 댓글 객체 생성
    comment = Comment(
        review_id=review.id,
        user_id=user.id,
        content="Test comment content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(comment)
    await async_session.commit()

    # 다른 사용자 ID 사용
    wrong_user_id = "wrong_user_id"
    request_body = CommentRequest(content="Updated comment content")
    comment_repo = CommentRepo(async_session)
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 잘못된 사용자로 수정 시도
    with pytest.raises(HTTPException):
        await update_comment(
            comment_id=comment.id,
            body=request_body,
            user_id=wrong_user_id,
            user_repo=user_repo,
            review_repo=review_repo,
            comment_repo=comment_repo,
        )


@pytest.mark.asyncio
async def test_delete_comment(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        comment_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 댓글 객체 생성
    comment = Comment(
        review_id=review.id,
        user_id=user.id,  # 자신의 댓글
        content="Test comment content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(comment)
    await async_session.commit()

    # 정상적인 댓글 삭제 시도
    comment_repo = CommentRepo(async_session)
    user_repo = UserRepository(async_session)

    # 삭제 전 댓글이 존재하는지 확인
    query_before_delete = select(Comment).where(Comment.id == comment.id)  # type: ignore
    result_before_delete = await async_session.execute(query_before_delete)
    assert result_before_delete.scalar_one_or_none() is not None  # 삭제 전 댓글이 있어야 함

    # 댓글 삭제
    await delete_comment(comment_id=comment.id, user_id=user.id, user_repo=user_repo, comment_repo=comment_repo)

    # 삭제 후 댓글이 존재하지 않아야 함
    query_after_delete = select(Comment).where(Comment.id == comment.id)  # type: ignore
    result_after_delete = await async_session.execute(query_after_delete)
    assert result_after_delete.scalar_one_or_none() is None  # 삭제 후 댓글이 없어야 함


@pytest.mark.asyncio
async def test_update_comment_comment_not_found(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        comment_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 잘못된 comment_id 사용
    wrong_comment_id = 999  # 존재하지 않는 댓글 ID
    request_body = CommentRequest(content="Updated comment content")
    comment_repo = CommentRepo(async_session)
    review_repo = ReviewRepo(async_session)
    user_repo = UserRepository(async_session)

    # 잘못된 댓글 ID로 수정 시도
    with pytest.raises(HTTPException):
        await update_comment(
            comment_id=wrong_comment_id,
            body=request_body,
            user_id=user.id,
            user_repo=user_repo,
            review_repo=review_repo,
            comment_repo=comment_repo,
        )


@pytest.mark.asyncio
async def test_delete_comment_comment_not_found(
    async_session: AsyncSession,
    setup_data: User,
    setup_travelroute: TravelRoute,
) -> None:
    # Setup: 주어진 User와 TravelRoute 사용하여 테스트용 데이터 설정
    user = setup_data
    travel_route = setup_travelroute

    # 사용자와 여행 정보를 데이터베이스에 추가
    async_session.add(user)
    await async_session.commit()

    # Review 객체 추가
    review = Review(
        id=1,
        user_id=user.id,
        travel_route_id=travel_route.id,
        title="Test review title",
        rating=4.5,
        content="Test review content",
        comment_count=2,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(review)
    await async_session.commit()

    # 댓글 객체 생성
    comment = Comment(
        review_id=review.id,
        user_id=user.id,
        content="Test comment content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    async_session.add(comment)
    await async_session.commit()

    # 존재하지 않는 comment_id 사용
    wrong_comment_id = 999  # 실제로 존재하지 않는 댓글 ID
    comment_repo = CommentRepo(async_session)
    user_repo = UserRepository(async_session)

    # 잘못된 댓글 ID로 댓글 삭제 시도
    with pytest.raises(HTTPException):
        await delete_comment(
            comment_id=wrong_comment_id, user_id=user.id, user_repo=user_repo, comment_repo=comment_repo
        )
