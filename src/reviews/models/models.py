from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.orm import Base
from src.user.models.models import User


class ReviewImage(Base):  # type: ignore
    __tablename__ = "review_images"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    filepath: Mapped[str] = mapped_column(String(255), nullable=False)  # 이미지 파일 경로

    review: Mapped["Review"] = relationship("Review", back_populates="images")  # 부모 관계


"""
리뷰와 이미지를 1:N으로 정의해서 한 리뷰에 여러 이미지를 넣도록 테이블 정의
"""


class Review(Base):  # type: ignore
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[float] = mapped_column(nullable=False)  # 범위 제약은 애플리케이션 레벨에서 처리
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(default=0, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 정의
    images: Mapped[list["ReviewImage"]] = relationship(
        "ReviewImage", back_populates="review", lazy="joined"
    )  # 자식 관계
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="review", lazy="joined"
    )  # 댓글 관계 추가
    likes: Mapped[list["Like"]] = relationship("Like", back_populates="review", lazy="joined")  # 좋아요 관계 추가


class Like(Base):  # type: ignore
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    # 관계 정의
    user: Mapped["User"] = relationship("User", back_populates="likes", lazy="select")
    review: Mapped["Review"] = relationship("Review", back_populates="likes")

    # 한 사용자는 한 리뷰에 대해 한 번만 좋아요를 누를 수 있음
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="unique_user_review_like"),)


class Comment(Base):  # type: ignore
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 정의
    user: Mapped["User"] = relationship("User", back_populates="comments")
    review: Mapped["Review"] = relationship("Review", back_populates="comments")
