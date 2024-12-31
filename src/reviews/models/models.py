# from datetime import datetime
# from typing import Optional, List
#
# from sqlalchemy import func, Column, DateTime
# from sqlalchemy.orm import relationship
# from sqlmodel import SQLModel, Field
#
#
#
# class ReviewImage(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     review_id: int = Field(foreign_key="review.id")
#     filepath: str = Field(nullable=False) # 이미지 파일 경로
#
#     review: Optional["Review"] = relationship(back_populates="images") # 부모 관계
#
#
# class Review(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     user_id: int = Field(foreign_key="user.id", nullable=False)
#     route_id: int = Field(foreign_key="route.id", nullable=False)
#     title: str = Field(nullable=False)
#     rating: float = Field(..., gt=0, le=5, description="Rating between 0 and 5")  # 범위 제약 추가
#     content: str = Field(nullable=False)
#     images: List["ReviewImage"] =relationship(back_populates="review") # 자식 관계
#     created_at: datetime = Field(default=func.now(), nullable=False)
#     updated_at: datetime = Column(
#         DateTime, default=func.now(), onupdate=func.now(), nullable=False
#     )
#
