
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship

from src.config.orm import Base


class ReviewImage(Base):
    __tablename__ = "review_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    filepath = Column(String(255), nullable=False)  # 이미지 파일 경로

    review = relationship("Review", back_populates="images")  # 부모 관계

"""
리뷰와 이미지 를 1:n으로 정의 해서 한 리뷰에 여러 이미지 넣도록 테이블 정의
"""
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    title = Column(String(255), nullable=False)
    rating = Column(Float, nullable=False)  # 범위 제약은 애플리케이션 레벨에서 처리
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 정의
    images = relationship("ReviewImage", back_populates="review")  # 자식 관계
    comments = relationship("Comment", back_populates="review")  # 댓글 관계 추가
    likes = relationship("Like", back_populates="review")  # 좋아요 관계 추가

class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 관계 정의
    user = relationship("User", back_populates="likes", lazy="select")
    review = relationship("Review", back_populates="likes", lazy="select")

    # 한 사용자는 한 리뷰에 대해 한 번만 좋아요를 누를 수 있음
    __table_args__ = (UniqueConstraint("user_id", "review_id", name="unique_user_review_like"),)

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 정의
    user = relationship("User", back_populates="comments", lazy="select")
    review = relationship("Review", back_populates="comments", lazy="select")