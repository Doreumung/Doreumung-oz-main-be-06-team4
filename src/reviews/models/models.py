from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Text, UniqueConstraint, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.user.models.models import User


class ImageSourceType(StrEnum):
    UPLOAD = "upload"
    LINK = "link"


KST = timezone(timedelta(hours=9))


class ReviewImage(SQLModel, table=True):
    __tablename__ = "review_images"
    id: int = Field(default=None, primary_key=True)
    review_id: int = Field(foreign_key="reviews.id", nullable=True)
    filepath: str = Field(sa_column=Column(Text, nullable=True))
    source_type: ImageSourceType = Field(sa_type=SqlEnum(ImageSourceType), nullable=True)  # type: ignore # 이미지 출처 (업로드/링크)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"onupdate": lambda: datetime.now(KST)},
    )

    # 부모 관계
    review: Optional["Review"] = Relationship(back_populates="images")


"""
리뷰와 이미지를 1:N으로 정의해서 한 리뷰에 여러 이미지를 넣도록 테이블 정의
"""


if TYPE_CHECKING:
    from src.travel.models.travel_route_place import TravelRoute


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    travel_route_id: int = Field(foreign_key="travelroute.id", nullable=False)
    title: str = Field(max_length=255, nullable=False)
    rating: float = Field(nullable=False)  # 범위 제약은 애플리케이션 레벨에서 처리
    content: str = Field(default=None, sa_column=Column(Text, nullable=False))  # Pydantic 기본값
    like_count: int = Field(default=0, nullable=True)
    thumbnail: Optional[str] = Field(nullable=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"onupdate": lambda: datetime.now(KST)},
    )

    # 관계 정의
    images: List["ReviewImage"] = Relationship(
        back_populates="review", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"}
    )
    likes: List["Like"] = Relationship(back_populates="review", sa_relationship_kwargs={"lazy": "joined"})
    comments: List["Comment"] = Relationship(
        back_populates="review", sa_relationship_kwargs={"lazy": "joined", "cascade": "all, delete-orphan"}
    )
    user: Optional["User"] = Relationship(back_populates="review", sa_relationship_kwargs={"lazy": "select"})
    travel_route: Optional["TravelRoute"] = Relationship(back_populates="reviews")


class Like(SQLModel, table=True):
    __tablename__ = "likes"

    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    review_id: int = Field(foreign_key="reviews.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    # 관계 정의
    user: Optional["User"] = Relationship(back_populates="likes", sa_relationship_kwargs={"lazy": "select"})
    review: Optional["Review"] = Relationship(back_populates="likes", sa_relationship_kwargs={"lazy": "select"})

    # 한 사용자는 한 리뷰에 대해 한 번만 좋아요를 누를 수 있음
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="unique_user_review_like"),)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id", nullable=False)
    review_id: int = Field(foreign_key="reviews.id", nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(KST),
        nullable=False,
        sa_type=DateTime(timezone=True),  # type: ignore
        sa_column_kwargs={"onupdate": lambda: datetime.now(KST)},
    )

    # 관계 정의
    user: Optional["User"] = Relationship(back_populates="comments", sa_relationship_kwargs={"lazy": "select"})
    review: Optional["Review"] = Relationship(back_populates="comments", sa_relationship_kwargs={"lazy": "select"})
