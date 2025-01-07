from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import Integer, String, and_, cast, func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import select

from src.reviews.dtos.request import ReviewRequestBase
from src.reviews.dtos.response import ReviewImageResponse, ReviewResponse
from src.reviews.models.models import Like, Review, ReviewImage
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.services.review_utils import (
    handle_file_upload,
    handle_image_urls,
    validate_order_by,
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
    body: ReviewRequestBase,
    files: Optional[List[UploadFile]] = File(None),
    image_urls: Optional[List[str]] = None,
    review_repo: ReviewRepo = Depends(),
) -> ReviewResponse:

    # 새로운 리뷰 객체 생성
    new_review = Review(
        user_id=body.user_id,
        travelroute_id=body.travelroute_id,
        title=body.title,
        rating=body.rating,
        content=body.content,
    )

    # 리뷰 저장
    saved_review = await review_repo.save_review(new_review)
    if not saved_review or not saved_review.id:
        raise HTTPException(status_code=500, detail="Failed to save review or review ID is None")

    # 이미지 응답 리스트 초기화
    image_responses = []

    # 파일 업로드 처리
    if files:
        try:
            await handle_file_upload(files, saved_review.id, review_repo)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    # URL 이미지 처리
    if image_urls:
        try:
            for url in image_urls:
                new_image = await review_repo.save_image(
                    ReviewImage(
                        review_id=saved_review.id,
                        filepath=url,
                        source_type="LINK",
                    )
                )
                # ReviewImageResponse 객체로 변환하여 추가
                if new_image is not None:
                    image_responses.append(
                        ReviewImageResponse(
                            id=new_image.id,
                            filepath=new_image.filepath,
                            source_type=new_image.source_type,
                        )
                    )
                else:
                    pass
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image URL handling failed: {e}")

    return ReviewResponse(
        id=saved_review.id,
        nickname=body.nickname,
        user_id=saved_review.user_id,
        travelroute_id=saved_review.travelroute_id,
        title=saved_review.title,
        rating=saved_review.rating,
        content=saved_review.content,
        like_count=saved_review.like_count or 0,
        liked_by_user=False,
        created_at=saved_review.created_at,
        updated_at=saved_review.updated_at,
        images=image_responses,
    )


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
    order_by: str = Query("created_at"),
    order: str = Query("desc"),
    user_id: str = Depends(authenticate),
    travelroute_id: Optional[int] = None,
    review_repo: ReviewRepo = Depends(),
) -> Dict[str, Any]:
    query = select(Review)

    # 조건 필터링
    conditions = []  # 조건을 저장할 리스트

    if user_id:  # user_id가 None이 아니고 유효한 경우
        conditions.append(Review.user_id == user_id)

    if travelroute_id:  # travelroute_id가 None이 아니고 유효한 경우
        conditions.append(Review.travelroute_id == travelroute_id)

    # 조건을 쿼리에 적용
    if conditions:  # 조건이 하나 이상 있을 경우에만 where 절 추가
        query = query.where(and_(*conditions))  # type: ignore

    # 정렬 컬럼 및 방향 설정
    order_column = validate_order_by(order_by, VALID_ORDER_BY_COLUMNS)
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
    reviews = result.unique().scalars().all()

    # 좋아요 여부 확인
    liked_reviews_query = await review_repo.session.execute(
        select(Like.review_id).where(Like.user_id == user_id)  # type: ignore
    )
    liked_reviews = {like for like in liked_reviews_query.scalars().all()}

    # 닉네임
    uesr_query = await review_repo.session.execute(select(User.nickname).where(User.id == user_id))  # type: ignore
    nickname = uesr_query.unique().scalar_one_or_none()

    return {
        "page": page,
        "size": size,
        "total_pages": (total_reviews + size - 1) // size,
        "reviews": [
            ReviewResponse(
                **review.__dict__,  # ORM 객체를 딕셔너리로 변환
                nickname=str(nickname),
                liked_by_user=review.id in liked_reviews,
            ).model_dump()
            for review in reviews
        ],
    }


# """
# 리뷰 수정 api
# """
# @review_router.patch(
#     "/reviews/{review_id}",
#     response_model=ReviewResponse,
#     status_code=status.HTTP_200_OK,
# )
# async def update_review_handler(
#     review_id: int,
#     body: ReviewRequestBase,
#     files: Optional[List[UploadFile]] = File(None),
#     image_urls: Optional[List[str]] = None,
#     review_repo: ReviewRepo = Depends(),
#     user_id: str = Depends(authenticate),
# ) -> ReviewResponse:
#
#     if not isinstance(review_id, int):
#         raise ValueError("review_id must be an integer")
#     query = select(Review).where(cast(Review.id, Integer) == review_id)
#     result = await review_repo.session.execute(query)
#     review = result.scalar_one_or_none()
#     if not review:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No review found")
#
#     if review.user_id != user_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission")
#
#     # 수정 가능한 필드 업데이트
#     if body.title is not None:
#         review.title = body.title
#     if body.content is not None:
#         review.content = body.content
#     if body.rating is not None:
#         review.rating = body.rating
#     review.updated_at = datetime.now(ZoneInfo("Asia/Seoul"))
#
#     # 기존 이미지 삭제
#     existing_images = await review_repo.get_image_by_id(review_id)
#     if existing_images:  # None이 아닌 경우에만 처리
#         for image in existing_images:
#             if image.source_type == "upload":
#                 file_path = Path(image.filepath)
#                 if file_path.exists():
#                     file_path.unlink()
#             await review_repo.delete_image(image.id)
#
#     # 새 URL 및 파일 업로드 처리
#     if image_urls:
#         await handle_image_urls(image_urls, review_id, review_repo)
#     if files:
#         await handle_file_upload(files, review_id, review_repo)
#
#     await review_repo.save_review(review)
#     return ReviewResponse.model_validate(obj=review)
#
#
# """
# 리뷰 삭제 API
# """
#
#
# @review_router.delete(
#     "/reviews/{review_id}",
#     response_model=Dict[str, str],
#     status_code=status.HTTP_200_OK,
# )
# async def delete_review_handler(
#     review_id: int,
#     review_repo: ReviewRepo = Depends(),
#     user_id: str = Depends(authenticate),
# ) -> dict[str, str]:
#
#     query = select(Review).where(cast(Review.id, Integer) == review_id)
#     result = await review_repo.session.execute(query)
#     review = result.scalar_one_or_none()
#     if not review:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No review found")
#
#     if review.user_id != user_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission")
#
#     async with review_repo.session.begin():
#         images = await review_repo.get_image_by_id(review_id)
#         for image in images:
#             if image.source_type == "upload":
#                 file_path = Path(image.filepath)
#                 if file_path.exists():
#                     file_path.unlink()
#             await review_repo.delete_image(image.id)
#
#         await review_repo.delete_review(review)
#
#     return {"message": "Review deleted"}
