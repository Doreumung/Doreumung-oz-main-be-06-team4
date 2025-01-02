from typing import List, Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_async_session
from src.reviews.models.models import Review


class ReviewRepo:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save_review(self, review: Review) -> Optional[Review]:
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def get_review_by_id(self, review_id: int) -> Optional[Review]:
        result = await self.session.execute(select(Review).filter_by(review_id=review_id))
        return result.scalar_one_or_none()

    async def get_all_reviews(self, skip: int = 0, limit: int = 10) -> List[Review]:
        result = await self.session.execute(select(Review).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def delete_review(self, review: Review) -> None:
        await self.session.delete(review)
        await self.session.commit()

    async def get_review_like_count(self, like_count: int) -> Optional[Review]:
        result = await self.session.execute(select(Review).filter_by(like_count=like_count))
        return result.scalar_one_or_none()

    async def add_like(self, like_count: int) -> Optional[Review]:
        review = await self.get_review_like_count(like_count)
        if review:
            review.like_count += 1
            await self.session.commit()
        return review

    async def delete_review_like(self, like_count: int) -> Optional[Review]:
        review = await self.get_review_like_count(like_count)
        if review and review.like_count > 0:
            review.like_count -= 1
            await self.session.commit()
        return review
