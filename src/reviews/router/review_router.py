import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import Integer, String, cast, func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import select

from src.reviews.dtos.request import ReviewRequestBase
from src.reviews.dtos.response import ReviewImageResponse, ReviewResponse
from src.reviews.models.models import (
    Comment,
    ImageSourceType,
    Like,
    Review,
    ReviewImage,
)
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.services.review_utils import (
    handle_file_upload,
    handle_image_urls,
    validate_order_by,
    validate_review_image,
)
from src.user.models.models import User
from src.user.repo.repository import UserRepository
from src.user.services.authentication import authenticate

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
async def create_review_handler(
    body: ReviewRequestBase = Body(...),  # 리뷰 본문 처리
    review_repo: ReviewRepo = Depends(),  # 의존성 주입
    current_user_id: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
) -> ReviewResponse:
    # 요청 바디 로깅
    logging.info(f"Received request body: {body}")
    # 사용자 확인
    user = await user_repo.get_user_by_id(user_id=current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 새로운 리뷰 객체 생성
    new_review = Review(
        user_id=current_user_id,
        travel_route_id=body.travel_route_id,
        title=body.title,
        rating=body.rating,
        content=body.content,
        thumbnail=body.thumbnail,
    )
    logging.info(f"Created Review object: {new_review}")

    # 리뷰 저장
    saved_review = await review_repo.save_review(new_review)
    if not saved_review or not saved_review.id:
        raise HTTPException(status_code=500, detail="Failed to save review")
    logging.info(f"Saved Review: {saved_review}")

    # 최종 응답 생성
    response = ReviewResponse(
        id=saved_review.id,
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
    )
    return response


"""
리뷰 단일 조회 API
"""


@review_router.get(
    "/reviews/{review_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
)
async def get_review_handler(
    review_id: int,
    user_id: str = Depends(authenticate),
    review_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
) -> ReviewResponse:
    user = await user_repo.get_user_by_id(user_id)

    # 사전 유효성 검사
    if not user or user.id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 수정된 쿼리
    query = select(Review).where(cast(Review.id, Integer) == review_id).options(joinedload(Review.user))  # type: ignore
    result = await review_repo.session.execute(query)
    review = result.unique().scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 단일 리뷰 반환
    return ReviewResponse.model_validate({**review.__dict__, "nickname": review.user.nickname})


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
        .outerjoin(Like, cast(Review.id, Integer) == Like.review_id)
        .group_by(cast(Review.id, Integer))
        .subquery()
    )

    # 댓글 개수 계산 서브 쿼리
    comment_count_subquery = (
        select(cast(Review.id, Integer), func.count("*").label("comment_count"))
        .outerjoin(Comment, cast(Review.id, Integer) == Comment.review_id)
        .group_by(cast(Review.id, Integer))
        .subquery()
    )

    # 리뷰와 좋아요 개수를 조인
    query = (
        select(
            Review.title.label("title"),  # type: ignore
            Review.rating.label("rating"),  # type: ignore
            User.nickname.label("nickname"),  # type: ignore
            Review.created_at.label("created_at"),  # type: ignore
            like_count_subquery.c.like_count.label("like_count"),
            comment_count_subquery.c.comment_count.label("comment_count"),
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
    total_reviews_result = await review_repo.session.execute(select(func.count()).select_from(query.subquery()))
    total_reviews = total_reviews_result.unique().scalar_one_or_none() or 0

    # 페이지네이션 처리
    offset = (page - 1) * size
    paginated_query = query.offset(offset).limit(size)
    result = await review_repo.session.execute(paginated_query)
    reviews = result.unique().mappings().all()

    # 리뷰 데이터 구성
    review_data = [
        {
            "title": review.title,
            "nickname": review.nickname,
            "like_count": review.like_count,
            "comment_count": review.comment_count,
            "rating": review.rating,
            "created_at": review.created_at.isoformat(),
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
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
)
async def update_review_handler(
    review_id: int,
    body: ReviewRequestBase,
    files: Optional[List[UploadFile]] = File(None),
    image_urls: Optional[List[str]] = None,
    review_repo: ReviewRepo = Depends(),
    user_id: str = Depends(authenticate),
) -> ReviewResponse:

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
    review.updated_at = datetime.now(ZoneInfo("Asia/Seoul"))

    # 기존 이미지 삭제
    existing_images = await review_repo.get_image_by_id(review_id)
    if existing_images:  # None이 아닌 경우에만 처리
        for image in existing_images:
            if image.source_type == "upload":
                file_path = Path(image.filepath)
                if file_path.exists():
                    file_path.unlink()
            await review_repo.delete_image(image.id)

    # 새 URL 및 파일 업로드 처리
    if image_urls:
        await handle_image_urls(image_urls, review_id, review_repo)
    if files:
        await handle_file_upload(files, review_id, review_repo)

    await review_repo.save_review(review)
    return ReviewResponse.model_validate({**review.__dict__, "nickname": nickname})


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


#
