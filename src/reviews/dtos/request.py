from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ReviewRequestBase(BaseModel):
    user_id: str
    travelroute_id: Optional[int]
    nickname: str
    title: str
    rating: float
    content: str

    class Config:
        from_attributes = True


class CommentRequest(BaseModel):
    content: str

    class Config:
        from_attributes = True
