from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.reviews.models.models import ImageSourceType


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
    id: int
    nickname: str
    user_id: str
    travel_route_id: int
    title: str
    rating: float
    content: str
    like_count: int
    liked_by_user: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    images: List[ReviewImageResponse]

    class Config:
        from_attributes = True


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
