# from datetime import datetime
#
# import pytest
# from fastapi import HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src import TravelRoute
# from src.reviews.dtos.request import CommentRequest
# from src.reviews.dtos.response import CommentResponse
# from src.reviews.models.models import Comment, Review
# from src.reviews.repo.review_repo import CommentRepo
# from src.reviews.router.comment_router import create_comment
# from src.user.models.models import User
# from src.user.repo.repository import UserRepository
#
#
# @pytest.mark.asyncio
# async def test_create_comment(
#     async_session: AsyncSession,
#     setup_data: User,
#     setup_travelroute: TravelRoute,
# ) -> None:
#     user = setup_data
#     travel_route = setup_travelroute
#
#     # 가짜 유저 및 리뷰 데이터 생성
#     other_user = User(
#         id="test_user_id",
#         email="testuser@example.com",
#         password="password",
#         nickname="test_user",
#         created_at=datetime.now(),
#         updated_at=datetime.now(),
#     )
#     async_session.add(other_user)
#     await async_session.commit()
#
#     review = Review(
#         id=1,
#         user_id=other_user.id,
#         travel_route_id=travel_route.id,
#         title="test title",
#         rating=4.5,
#         content="This is a test review",
#         comment_count=3,
#         created_at=datetime.now(),
#         updated_at=datetime.now(),
#     )
#     async_session.add(review)
#     await async_session.commit()
#
#     # 요청 데이터 생성
#     request_body = CommentRequest(content="This is a test comment.")
#     comment_repo = CommentRepo(async_session)
#     user_repo = UserRepository(async_session)
#
#     # 핸들러 호출
#     response = await create_comment(
#         review_id=1,
#         body=request_body,
#         user_id=user.id,
#         user_repo=user_repo,
#         comment_repo=comment_repo,
#     )
#
#     # 검증
#     assert isinstance(response, CommentResponse)
#     assert response.nickname == other_user.nickname
#     assert response.review_id == review.id
#     assert response.content == request_body.content
#     assert response.created_at is not None
#
#     # 데이터베이스에 저장된 댓글 확인
#     saved_comment = await async_session.get(Comment, response.id)
#     assert saved_comment is not None
#     assert saved_comment.nickname == response.nickname
#     assert saved_comment.review_id == response.review_id
#     assert saved_comment.content == response.content
