from typing import List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy import Integer, cast, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import Like  # type: ignore
from src.config.database.connection_async import get_async_session


class LikeRepo:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, like: Like) -> Optional[Like]:
        self.session.add(like)
        return like

    async def get_by_user_review_id(self, review_id: int, user_id: str) -> Optional[Like]:
        like = await self.session.execute(select(Like).where(Like.review_id == review_id, Like.user_id == user_id))
        return like.scalars().one_or_none()

    async def get_by_review_id(self, review_id: int) -> list[Like]:
        async with self.session as session:
            likes = await session.execute(select(Like).where(Like.review_id == review_id))
            return list(likes.scalars().all())

    async def get_by_id(self, like_id: int) -> Optional[Like]:
        place = await self.session.get(Like, like_id)
        if not place:
            raise HTTPException(status_code=404, detail="Item not found")
        return place

    async def get_all(self) -> List[Like]:
        result = await self.session.execute(select(Like))
        return list(result.scalars().all())

    async def delete(self, like: Like) -> None:
        stmt = delete(Like).where(Like.id == like.id)
        result = await self.session.execute(stmt)

        deleted_count = result.rowcount

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Like not found")
