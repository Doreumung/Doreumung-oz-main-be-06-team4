from typing import List, Optional

from pydantic import BaseModel


class ReviewRequestBase(BaseModel):
    travel_route_id: Optional[int]
    title: str
    rating: float
    content: str
    images: Optional[List[str]] = None
    thumbnail: Optional[str] = None

    class Config:
        from_attributes = True


class CommentRequest(BaseModel):
    content: str

    class Config:
        from_attributes = True


#
