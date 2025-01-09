from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from rich.region import Region

from src.reviews.models.models import ImageSourceType
from src.travel.models.enums import RegionEnum, ThemeEnum


class ReviewImageResponse(BaseModel):
    id: int
    review_id: int
    filepath: str
    source_type: ImageSourceType

    class Config:
        from_attributes = True


class UploadImageResponse(BaseModel):
    uploaded_image: ReviewImageResponse
    all_images: List[ReviewImageResponse]


class ReviewResponse(BaseModel):
    review_id: int
    nickname: str
    travel_route_id: int
    title: str
    rating: float
    content: str
    like_count: int
    liked_by_user: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    thumbnail: Optional[str]

    class Config:
        from_attributes = True


class GetReviewResponse(BaseModel):
    review_id: int
    nickname: str
    travel_route_id: int | None
    title: str
    rating: float
    content: str
    like_count: int
    liked_by_user: Optional[bool] = False
    regions: List[str] | List[RegionEnum]
    travel_route: str
    themes: List[str] | List[ThemeEnum]
    thumbnail: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ReviewUpdateResponse(BaseModel):
    review_id: int
    title: str
    content: str
    rating: float
    thumbnail: Optional[str] = None  # 업데이트된 썸네일 이미지 (Optional)
    nickname: str  # 작성자 닉네임
    updated_at: datetime  # 리뷰 수정된 시간

    class Config:
        orm_mode = True


class CommentResponse(BaseModel):
    id: int
    user_id: str
    review_id: int
    nickname: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


#
