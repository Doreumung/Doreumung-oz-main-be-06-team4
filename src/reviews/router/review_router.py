from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import Integer, String, cast, func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import select

from src import TravelRoute, TravelRoutePlace  # type: ignore
from src.config import settings
from src.reviews.dtos.request import ReviewRequestBase, ReviewUpdateRequest
from src.reviews.dtos.response import (
    GetReviewResponse,
    ReviewImageResponse,
    ReviewResponse,
    ReviewUpdateResponse,
    UploadImageResponse,
)
from src.reviews.models.models import (
    KST,
    Comment,
    ImageSourceType,
    Like,
    Review,
    ReviewImage,
)
from src.reviews.repo.review_repo import ReviewRepo
from src.reviews.services.image_utils import handle_image_urls, s3_client
from src.reviews.services.review_utils import validate_order_by
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
    response_model=ReviewResponse | dict[str, int],
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    body: ReviewRequestBase,
    uploaded_urls: List[str] = Body(default_factory=list),
    deleted_urls: List[str] = Body(default_factory=list),
    review_repo: ReviewRepo = Depends(),
    user_repo: UserRepository = Depends(),
    current_user_id: str = Depends(authenticate),
) -> ReviewResponse | dict[str, int]:
    """
    리뷰 작성 시 업로드된 이미지 URL을 연결하는 API.
    """
    # 사용자 확인
    user = await user_repo.get_user_by_id(user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 리뷰 생성 전에 travel_route_id 유효성 확인
    route_id = body.travel_route_id
    if route_id is None:
        raise HTTPException(status_code=400, detail="Travel route ID cannot be null")

    route = await review_repo.get_travel_route_by_id(route_id)
    if not route:
        raise HTTPException(status_code=400, detail="Invalid travel route ID")

    # deleted_urls 처리
    for url in deleted_urls:
        query = select(ReviewImage).where(
            ReviewImage.filepath == url,  # type: ignore
            ReviewImage.user_id == user.id,  # type: ignore
        )
        result = await review_repo.session.execute(query)
        image = result.scalars().first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        # 이미지 삭제
        if image.source_type == ImageSourceType.LINK:
            key = Path(image.filepath).name
            s3_client.delete_object(Bucket="bucket-name", Key=key)
        await review_repo.delete_image(image.id)

    # 업로드된 URL 처리
    review_images = []
    if uploaded_urls or deleted_urls:
        review_images = await handle_image_urls(uploaded_urls, deleted_urls, current_user_id)

    # 리뷰 생성
    new_review = Review(
        user_id=user.id,
        travel_route_id=body.travel_route_id,
        title=body.title,
        rating=body.rating,
        content=body.content,
        thumbnail=body.thumbnail,
        images=review_images,
    )

    # 리뷰 저장
    saved_review = await review_repo.save_review(new_review)
    if saved_review is None:
        raise HTTPException(status_code=404, detail="Saved review not found")

    # # 이미지를 리뷰에 연결하기 위한 추가 로직
    # if review_images:
    #     images = await review_repo.get_image_by_id(saved_review.id)
    #     if not images:
    #         raise HTTPException(status_code=404, detail="No images found for the review")
    #
    #     # `UploadImageResponse` 생성
    #     uploaded_image_response = UploadImageResponse(
    #         uploaded_image=ReviewImageResponse(
    #             id=images[0].id,
    #             review_id=saved_review.id,
    #             filepath=str(images[0].filepath),
    #             source_type=images[0].source_type,  # 올바른 enum 값을 반환
    #             created_at=images[0].created_at,
    #             updated_at=images[0].updated_at,
    #         ),
    #         all_images=[
    #             ReviewImageResponse(
    #                 id=image.id,
    #                 review_id=image.review_id,
    #                 filepath=str(image.filepath),
    #                 source_type=image.source_type,
    #                 created_at=image.created_at,
    #                 updated_at=image.updated_at,
    #             )
    #             for image in images
    #         ],
    #         uploaded_url=images[0].filepath,
    #     )
    #
    #     return uploaded_image_response
    #
    # else:
    #     return {"review_id": saved_review.id}
    # 리뷰 응답 데이터 구성
    review_response = ReviewResponse(
        review_id=saved_review.id,
        user_id=saved_review.user_id,
        nickname=user.nickname,
        travel_route_id=saved_review.travel_route_id,
        title=saved_review.title,
        rating=saved_review.rating,
        content=saved_review.content,
        like_count=saved_review.like_count,
        thumbnail=saved_review.thumbnail,
        created_at=saved_review.created_at,
        updated_at=saved_review.updated_at,
    )

    return review_response


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
    order_by: str = Query("created_at", description="정렬 기준 (created_at, title, comment_count, like_count)"),
    order: str = Query("desc", description="정렬 방향 (asc or desc)"),
    review_repo: ReviewRepo = Depends(),
) -> Dict[str, Any]:
    # 리뷰와 좋아요 개수 계산 서브 쿼리
    # like_count_subquery = (
    #     select(cast(Review.id, Integer), func.count("*").label("like_count"))
    #     .join(Like, cast(Review.id, Integer) == Like.review_id)
    #     .group_by(cast(Review.id, Integer))
    #     .subquery()
    # )
    # 댓글 개수 계산 서브 쿼리
    comment_count_subquery = (
        select(
            cast(Review.id, Integer).label("review_id"), func.count(Comment.id).label("comment_count")  # type: ignore
        )
        .outerjoin(Comment, Comment.review_id == Review.id)  # type: ignore
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
            Review.like_count.label("like_count"),  # type: ignore
            func.coalesce(comment_count_subquery.c.comment_count, 0).label("comment_count"),  # COALESCE 처리
            Review.thumbnail.label("thumbnail"),  # type: ignore
        )
        .join(User, User.id == Review.user_id)  # type: ignore
        .outerjoin(comment_count_subquery, cast(Review.id, Integer) == comment_count_subquery.c.review_id)
        # .outerjoin(like_count_subquery, cast(Review.id, Integer) == like_count_subquery.c.id)
    )

    # 정렬 컬럼 및 방향 설정
    valid_order_by_columns = ["created_at", "title", "like_count", "comment_count", "rating"]
    if order_by == "like_count":
        order_column = Review.like_count
    elif order_by == "comment_count":
        order_column = comment_count_subquery.c.comment_count  # type:ignore
    elif order_by == "rating":
        order_column = Review.rating  # type: ignore
    elif order_by in valid_order_by_columns:
        order_column = getattr(Review, order_by)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid order_by field: {order_by}")

    if order.lower() == "asc":
        query = query.order_by(order_column.asc())  # type:ignore
    else:
        query = query.order_by(order_column.desc())  # type:ignore

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
    uploaded_urls: List[str] = Body(default_factory=list),
    deleted_images: List[str] = Body(default_factory=list),
    user_id: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
) -> ReviewUpdateResponse:
    # 사용자 확인
    user = await user_repo.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 리뷰 존재 확인
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

    # 수정 필드 업데이트
    if body.title:
        review.title = body.title
    if body.content:
        review.content = body.content
    if body.rating:
        review.rating = body.rating
    if body.thumbnail:
        review.thumbnail = body.thumbnail
    review.updated_at = datetime.now(KST)

    # 업로드된 이미지 처리
    review_images = []
    for url in uploaded_urls:
        # 업로드된 이미지가 URL로 제공되면 ReviewImage 객체로 처리
        review_image = ReviewImage(
            filepath=url,
            source_type=ImageSourceType.LINK,  # 업로드된 이미지의 경우 링크로 저장
            user_id=user_id,
            is_temporary=False,
            created_at=datetime.now(KST),
            updated_at=datetime.now(KST),
        )
        # 이미지 저장
        review_images.append(review_image)

    # 삭제된 이미지 처리
    for file_name in deleted_images:
        try:
            s3_client.delete_object(Bucket=settings.BUCKET_NAME, Key=file_name)
            await review_repo.delete_image_by_filepath(file_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image: {str(e)}",
            )

    # 리뷰에 업로드된 이미지 연결
    review.images.extend(review_images)

    # 리뷰 저장
    await review_repo.save_review(review)

    # 응답 반환
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
