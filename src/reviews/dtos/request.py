from typing import List, Optional

from pydantic import BaseModel


class ReviewRequestBase(BaseModel):
    id: int
    user_id: str
    travelroute_id: int
    nickname: str
    title: str
    rating: float
    content: str
    images: Optional[List[str]]


class CommentRequest(BaseModel):
    content: str
