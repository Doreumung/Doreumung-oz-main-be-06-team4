import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import Integer, String, cast, delete, func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import select
from uvicorn.protocols.utils import ClientDisconnected

from src import TravelRoute, TravelRoutePlace  # type: ignore
from src.config import settings
from src.config.database.connection_async import get_async_session
from src.reviews.dtos.request import ReviewRequestBase, ReviewUpdateRequest
from src.reviews.dtos.response import (
    GetReviewResponse,
    ReviewResponse,
    ReviewUpdateResponse,
)
from src.reviews.models.models import (
    Comment,
    ImageSourceType,
    Like,
    Review,
    ReviewImage,
)
from src.reviews.repo.review_repo import CommentRepo, ReviewImageManager, ReviewRepo
from src.reviews.router.comment_router import delete_comment
from src.reviews.services.image_utils import (
    finalize_review_images,
    handle_image_urls,
    process_image_deletion,
    process_image_upload,
    s3_client,
)
from src.reviews.services.review_utils import validate_order_by
from src.reviews.services.travel_routes_info import generate_schedule_info
from src.travel.models.enums import RegionEnum, ThemeEnum
from src.user.models.models import User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import authenticate, authenticate_optional

# 라우터 정의
review_router = APIRouter(prefix="/api/v1", tags=["Reviews"])


# 유효한 정렬 컬럼 설정
VALID_ORDER_BY_COLUMNS = {"created_at", "rating", "title"}


"""
리뷰 생성 api 
"""


@review_router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    body: ReviewRequestBase,
    uploaded_urls: List[str] = Body(default_factory=list),  # 업로드된 이미지 URL 목록
    deleted_urls: List[str] = Body(default_factory=list),  # 삭제된 이미지 URL
    review_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
    current_user_id: str = Depends(authenticate),
) -> ReviewResponse:
    """
    리뷰 작성 시 업로드된 이미지 URL을 연결하는 API.
    """
    # 사용자 확인
    user = await user_repo.get_user_by_id(user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 업로드된 URL 처리
    review_images = await handle_image_urls(uploaded_urls, deleted_urls)

    # 리뷰 생성
    new_review = Review(
        user_id=user.id,
        travel_route_id=body.travel_route_id,
        title=body.title,
        rating=body.rating,
        content=body.content,
        thumbnail=body.thumbnail,
        images=review_images,  # ReviewImage 객체 리스트 추가
    )
    saved_review = await review_repo.save_review(new_review)
    if not saved_review or not saved_review.id:
        raise HTTPException(status_code=500, detail="Failed to save review")

    # 응답 생성
    return ReviewResponse(
        review_id=saved_review.id,
        nickname=user.nickname,
        travel_route_id=saved_review.travel_route_id,
        title=saved_review.title,
        rating=saved_review.rating,
        content=saved_review.content,
        like_count=saved_review.like_count or 0,
        liked_by_user=False,
        created_at=saved_review.created_at,
        updated_at=saved_review.updated_at,
        thumbnail=saved_review.thumbnail,
        images=[image.filepath for image in review_images],  # 응답에 이미지 URL 포함
    )


"""
리뷰 단일 조회 API
"""


@review_router.get(
    "/reviews/{review_id}",
    response_model=GetReviewResponse,
    status_code=status.HTTP_200_OK,
)
async def get_review_handler(
    review_id: int,
    user_id: Optional[str] = Depends(authenticate_optional),
    review_repo: ReviewRepo = Depends(),
) -> GetReviewResponse:

    query = (
        select(Review)
        .where(cast(Review.id, Integer) == review_id)
        .options(
            joinedload(Review.user),  # type: ignore
            joinedload(Review.travel_route).joinedload(TravelRoute.travel_route_places).joinedload(TravelRoutePlace.place),  # type: ignore
        )
    )
    result = await review_repo.session.execute(query)
    review = result.unique().scalar_one_or_none()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    regions: List[RegionEnum] = (
        review.travel_route.regions
        if review.travel_route and isinstance(review.travel_route.regions, list)
        else (
            [review.travel_route.regions]  # type: ignore
            if review.travel_route and review.travel_route.regions is not None
            else []
        )
    )

    themes: List[ThemeEnum] = (
        review.travel_route.themes
        if review.travel_route and isinstance(review.travel_route.themes, list)
        else (
            [review.travel_route.themes]  # type: ignore
            if review.travel_route and review.travel_route.themes is not None
            else []
        )
    )
    if review.user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if review.travel_route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Travel route not found")

    # 현재 사용자가 좋아요 했는지 확인
    liked_by_user = False
    if user_id:  # 로그인한 사용자에 대해서만 확인
        liked_by_user = any(like.user_id == user_id for like in review.likes)
    place_names = []
    for i in review.travel_route.travel_route_places:
        place_names.append(i.place.name)

    return GetReviewResponse(
        review_id=review.id,
        user_id=review.user_id,
        nickname=review.user.nickname,
        travel_route_id=review.travel_route.id,
        title=review.title,
        rating=review.rating,
        content=review.content,
        like_count=len(review.likes),  # 좋아요 수
        liked_by_user=liked_by_user,  # 현재 사용자가 좋아요 했는지 여부
        regions=regions,
        travel_route=place_names,
        themes=themes,
        thumbnail=review.thumbnail,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


"""
리뷰 리스트 조회 api (필터링 정렬, 페이징 처리 포함)
"""


@review_router.get(
    "/reviews",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
)
async def get_all_review_handler(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    order_by: str = Query("created_at", description="정렬 기준 (created_at, title, likes)"),
    order: str = Query("desc", description="정렬 방향 (asc or desc)"),
    review_repo: ReviewRepo = Depends(),
) -> Dict[str, Any]:
    # 리뷰와 좋아요 개수 계산 서브 쿼리
    like_count_subquery = (
        select(cast(Review.id, Integer), func.count("*").label("like_count"))
        .join(Like, cast(Review.id, Integer) == Like.review_id)
        .group_by(cast(Review.id, Integer))
        .subquery()
    )
    # 댓글 개수 계산 서브 쿼리
    comment_count_subquery = (
        select(cast(Review.id, Integer), func.count("*").label("comment_count"))
        .join(Comment, cast(Review.id, Integer) == Comment.review_id)
        .group_by(cast(Review.id, Integer))
        .subquery()
    )

    # 리뷰와 좋아요 개수를 조인
    query = (
        select(
            Review.id.label("review_id"),  # type: ignore
            Review.user_id.label("user_id"),  # type: ignore
            Review.title.label("title"),  # type: ignore
            Review.rating.label("rating"),  # type: ignore
            User.nickname.label("nickname"),  # type: ignore
            Review.created_at.label("created_at"),  # type: ignore
            like_count_subquery.c.like_count.label("like_count"),
            comment_count_subquery.c.comment_count.label("comment_count"),
            Review.thumbnail.label("thumbnail"),  # type: ignore
        )
        .join(User, User.id == Review.user_id)  # type: ignore
        .outerjoin(like_count_subquery, cast(Review.id, Integer) == like_count_subquery.c.id)
        .outerjoin(comment_count_subquery, cast(Review.id, Integer) == comment_count_subquery.c.id)
    )

    # 정렬 컬럼 및 방향 설정
    valid_order_by_columns = ["created_at", "title", "like_count", "comment_count", "rating"]
    if order_by == "likes":
        order_column = like_count_subquery.c.like_count
    elif order_by == "comments":
        order_column = comment_count_subquery.c.comment_count
    elif order_by == "rating":
        order_column = Review.rating  # type: ignore
    else:
        order_column = validate_order_by(order_by, set(valid_order_by_columns))

    if order.lower() == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    # 총 리뷰 개수 계산
    total_reviews_result = await review_repo.session.execute(select(func.count()).select_from(Review))
    total_reviews = total_reviews_result.unique().scalar_one_or_none() or 0

    # 페이지네이션 처리
    offset = (page - 1) * size
    paginated_query = query.offset(offset).limit(size)
    result = await review_repo.session.execute(paginated_query)
    reviews = result.unique().mappings().all()
    # 리뷰 데이터 구성
    review_data = [
        {
            "review_id": review["review_id"],
            "user_id": review["user_id"],
            "title": review["title"],
            "nickname": review["nickname"],
            "like_count": review["like_count"] if review["like_count"] else 0,
            "comment_count": review["comment_count"] if review["comment_count"] else 0,
            "rating": review["rating"],
            "thumbnail": review["thumbnail"],
            "created_at": review["created_at"],
        }
        for review in reviews
    ]
    return {
        "page": page,
        "size": size,
        "total_pages": (total_reviews + size - 1) // size,
        "total_reviews": total_reviews,
        "reviews": review_data,
    }


"""
리뷰 수정 api
"""


@review_router.patch(
    "/reviews/{review_id}",
    response_model=ReviewUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_review_handler(
    review_id: int,
    body: ReviewUpdateRequest,
    review_repo: ReviewRepo = Depends(),
    deleted_images: List[str] = Body(default_factory=list),
    user_id: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
) -> ReviewUpdateResponse:
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not isinstance(review_id, int):
        raise ValueError("review_id must be an integer")
    query = (
        select(Review, User.nickname)  # type: ignore
        .join(User, cast(User.id, String) == Review.user_id)
        .where(cast(Review.id, Integer) == review_id)
    )

    result = await review_repo.session.execute(query)
    review, nickname = result.unique().one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No review found")

    if review.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission")

    # 수정 가능한 필드 업데이트
    if body.title is not None:
        review.title = body.title
    if body.content is not None:
        review.content = body.content
    if body.rating is not None:
        review.rating = body.rating
    if body.thumbnail is not None:
        review.thumbnail = body.thumbnail
    review.updated_at = datetime.now(ZoneInfo("Asia/Seoul"))

    # 삭제된 이미지 처리
    if deleted_images:
        for file_name in deleted_images:
            try:
                # S3에서 삭제
                s3_client.delete_object(Bucket=settings.BUCKET_NAME, Key=file_name)
                # 데이터베이스에서 삭제
                await review_repo.delete_image_by_filepath(file_name)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete image: {str(e)}",
                )

    await review_repo.save_review(review)
    return ReviewUpdateResponse(
        review_id=review.id,
        title=review.title,
        content=review.content,
        rating=review.rating,
        thumbnail=review.thumbnail,
        nickname=nickname,
        updated_at=review.updated_at,
    )


"""
리뷰 삭제 API
"""


@review_router.delete(
    "/reviews/{review_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
)
async def delete_review_handler(
    review_id: int,
    review_repo: ReviewRepo = Depends(),
    user_id: str = Depends(authenticate),
) -> dict[str, str]:

    query = select(Review).where(cast(Review.id, Integer) == review_id)
    result = await review_repo.session.execute(query)
    review = result.unique().scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No review found")

    if review.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission")

    images = await review_repo.get_image_by_id(review_id)
    for image in images:
        if image.source_type == "upload":
            file_path = Path(image.filepath)
            if file_path.exists():
                file_path.unlink()
        await review_repo.delete_image(image.id)

    await review_repo.delete_review(review)

    return {"message": "Review deleted"}
