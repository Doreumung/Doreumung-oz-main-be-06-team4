from typing import List, Optional, Sequence

from fastapi import Depends, HTTPException
from sqlalchemy import Integer, and_, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_async_session
from src.reviews.models.models import Comment, ImageSourceType, Review, ReviewImage


class ReviewRepo:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save_review(self, review: Review) -> Optional[Review]:
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def get_review_by_id(self, review_id: int) -> Optional[Review]:
        result = await self.session.execute(select(Review).where(cast(Review.id, Integer) == review_id))
        review = result.unique().scalar_one_or_none()
        if not review:
            raise HTTPException(status_code=404, detail="Review does not exist")
        return review

    async def get_all_reviews(
        self, skip: int = 0, limit: int = 10, order_by: str = "created_at", order: str = "asc"
    ) -> List[Review]:
        # order_by 필드 존재 확인
        if not hasattr(Review, order_by):
            raise ValueError(f"Invalid order_by field: {order_by}")

        # 쿼리 작성
        query = select(Review)
        if order.lower() == "asc":
            query = query.order_by(getattr(Review, order_by).asc())
        else:
            query = query.order_by(getattr(Review, order_by).desc())

        # 데이터 가져오기
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.unique().scalars().all())

    async def delete_review(self, review: Review) -> None:
        await self.session.delete(review)
        await self.session.commit()

    async def get_review_like_count(self, like_count: int) -> Optional[Review]:
        result = await self.session.execute(select(Review).filter_by(like_count=like_count))
        return result.unique().scalar_one_or_none()

    async def add_review_like(self, review_id: int) -> Optional[Review]:
        review = await self.get_review_by_id(review_id)
        if review:
            review.like_count += 1
            await self.session.commit()
            await self.session.refresh(review)
        return review

    async def delete_review_like(self, review_id: int) -> Optional[Review]:
        review = await self.get_review_by_id(review_id)
        if review and review.like_count > 0:
            review.like_count -= 1
            await self.session.commit()
            await self.session.refresh(review)
        return review

    # 이미지 저장
    async def save_image(self, image: ReviewImage) -> Optional[ReviewImage]:
        self.session.add(image)
        await self.session.commit()
        await self.session.refresh(image)
        return image

    # 이미지 조회
    async def get_image_by_id(self, review_id: int) -> Sequence[ReviewImage]:
        result = await self.session.execute(
            select(ReviewImage).where(cast(ReviewImage.review_id, Integer) == review_id)
        )
        images = result.scalars().all()  # ReviewImage 객체의 리스트 반환
        return images

    # 이미지 삭제
    async def delete_image(self, image_id: int) -> None:
        query = select(ReviewImage).where(cast(ReviewImage.id, Integer) == image_id)
        result = await self.session.execute(query)
        image = result.scalars().first()
        if image:
            await self.session.delete(image)
            await self.session.commit()

    async def delete_image_by_filepath(self, filepath: str) -> None:
        query = select(ReviewImage).where(ReviewImage.filepath == filepath)  # type: ignore
        result = await self.session.execute(query)
        image = result.scalars().first()
        if image:
            await self.session.delete(image)
            await self.session.commit()

    async def get_existing_image_urls(self, review_id: int) -> List[str]:
        """
        특정 리뷰에 이미 저장된 이미지 URL을 가져옵니다.
        """
        # 조건을 and_로 묶어 더 명확하게 표현
        condition = and_(
            ReviewImage.review_id == review_id,  # type: ignore
            ReviewImage.source_type == ImageSourceType.LINK.value,  # type: ignore
        )

        # select 호출
        result = await self.session.execute(select(ReviewImage.filepath).where(condition))  # type: ignore

        # 결과 반환
        return [row[0] for row in result.all()]


class CommentRepo:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def create_comment(self, comment: Comment) -> Optional[Comment]:
        self.session.add(comment)
        await self.session.commit()
        await self.session.refresh(comment)
        return comment

    async def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        result = await self.session.execute(select(Comment).filter_by(id=comment_id))
        return result.scalar_one_or_none()

    async def get_all_comment(self, review_id: int, skip: int = 0, limit: int = 10) -> List[Comment]:
        result = await self.session.execute(
            select(Comment).where(cast(Comment.review_id, Integer) == review_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def delete_comment(self, comment_id: int) -> None:
        result = await self.session.execute(select(Comment).where(cast(Comment.id, Integer) == comment_id))
        comment = result.scalar_one_or_none()
        print(comment_id)
        if comment:
            print(comment_id)
            await self.session.delete(comment)
            await self.session.commit()
