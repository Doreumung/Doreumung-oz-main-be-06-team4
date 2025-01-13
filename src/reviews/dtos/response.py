from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.reviews.models.models import ImageSourceType
from src.travel.dtos.base_travel_route import Schedule
from src.travel.models.enums import RegionEnum, ThemeEnum


class ReviewImageResponse(BaseModel):
    id: int
    review_id: int
    filepath: str
    source_type: ImageSourceType
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UploadImageResponse(BaseModel):
    uploaded_image: ReviewImageResponse
    all_images: List[ReviewImageResponse]
    uploaded_url: str

    class Config:
        from_attributes = True


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
    images: Optional[List[str]]
    uploaded_image: UploadImageResponse

    class Config:
        from_attributes = True


class GetReviewResponse(BaseModel):
    review_id: int
    user_id: str
    nickname: str
    travel_route_id: int | None
    title: str
    rating: float
    content: str
    like_count: int
    liked_by_user: Optional[bool] = False
    regions: List[str] | List[RegionEnum]
    travel_route: list[str]
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
    comment_id: int
    review_id: int
    nickname: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class GetCommentResponse(BaseModel):
    comment_id: int
    user_id: str
    nickname: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateCommentResponse(BaseModel):
    comment_id: int
    nickname: str
    content: str
    updated_at: datetime
    message: str

    class Config:
        orm_mode = True


#
