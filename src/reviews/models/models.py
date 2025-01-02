from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

class ReviewImage(SQLModel, table=True):
    __tablename__ = "review_images"
    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: int = Field(foreign_key="reviews.id", nullable=False)
    filepath: str = Field(max_length=255, nullable=False)  # 이미지 파일 경로

    # 부모 관계
    review: Optional["Review"] = Relationship(back_populates="images")


"""
리뷰와 이미지를 1:N으로 정의해서 한 리뷰에 여러 이미지를 넣도록 테이블 정의
"""


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    title: str = Field(max_length=255, nullable=False)
    rating: float = Field(nullable=False)  # 범위 제약은 애플리케이션 레벨에서 처리
    content: str = Field(nullable=False)
    like_count: int = Field(default=0, nullable=True)
    created_at: datetime = Field(default_factory=func.now, nullable=False, sa_type=DateTime)
    updated_at: datetime = Field(
        default_factory=func.now, nullable=False, sa_type=DateTime, sa_column_kwargs={"onupdate": func.now()}
    )

    # 관계 정의
    images: List["ReviewImage"] = Relationship(back_populates="review", sa_relationship_kwargs={"lazy": "joined"})
    likes: List["Like"] = Relationship(back_populates="review", sa_relationship_kwargs={"lazy": "joined"})
    comments: List["Comment"] = Relationship(back_populates="review", sa_relationship_kwargs={"lazy": "joined"})


class Like(SQLModel, table=True):
    __tablename__ = "likes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    review_id: int = Field(foreign_key="reviews.id", nullable=False)
    created_at: datetime = Field(default_factory=func.now, nullable=False, sa_type=DateTime)


    # 관계 정의
    user: Optional["User"] = Relationship(back_populates="likes", sa_relationship_kwargs={"lazy": "select"})
    review: Optional["Review"] = Relationship(back_populates="likes", sa_relationship_kwargs={"lazy": "select"})

    # 한 사용자는 한 리뷰에 대해 한 번만 좋아요를 누를 수 있음
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="unique_user_review_like"),)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    review_id: int = Field(foreign_key="reviews.id", nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=func.now, nullable=False, sa_type=DateTime)
    updated_at: datetime = Field(
        default_factory=func.now, nullable=False, sa_type=DateTime, sa_column_kwargs={"onupdate": func.now()}
    )

    # 관계 정의
    user: Optional["User"] = Relationship(back_populates="comments", sa_relationship_kwargs={"lazy": "select"})
    review: Optional["Review"] = Relationship(back_populates="comments", sa_relationship_kwargs={"lazy": "select"})
