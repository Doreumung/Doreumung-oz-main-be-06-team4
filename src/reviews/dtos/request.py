from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ReviewRequestBase(BaseModel):
    user_id: str
    travelroute_id: int
    nickname: str
    title: str
    rating: float
    content: str
    images: Optional[List[str]] | None = None

    class Config:
        from_attributes = True


class CommentRequest(BaseModel):
    content: str

    class Config:
        from_attributes = True
