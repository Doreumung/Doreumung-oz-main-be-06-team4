# from typing import List
#
# from fastapi import Depends
# from sqlalchemy import select
# from sqlmodel.ext.asyncio.session import AsyncSession
#
# from src.config.database.connection_async import get_async_session
#
#
# class ReviewRepo:
#     def __init__(self, session: AsyncSession = Depends(get_async_session)):
#         self.session = session
#
#     async def save_review(self, review: Review):
#         self.session.add(review)
#         await self.session.commit()
#
#     async def get_review(self, review_id: int):
#         result = await self.session.exec(select(Review).filter_by(review_id=review_id))
#         return await result.scalar_one_or_none()
#
#     async def get_all_reviews(self, skip: int = 0, limit: int = 10) -> List[Review]:
#         result = await self.session.exec(select(Review).offset(skip).limit(limit))
#         return list(result.all())
#
#     async def delete_review(self, review: Review):
#         await self.session.delete(review)
