from typing import List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy import Integer, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import Like  # type: ignore
from src.config.database.connection_async import get_async_session


class LikeRepo:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, like: Like) -> Optional[Like]:
        self.session.add(like)
        await self.session.commit()
        await self.session.refresh(like)
        return like

    async def get_by_user_review_id(self, review_id: int, user_id: str) -> Optional[Like]:
        like = await self.session.execute(select(Like).where(Like.review_id == review_id, Like.user_id == user_id))
        return like.scalars().one_or_none()

    async def get_by_id(self, like_id: int) -> Optional[Like]:
        place = await self.session.get(Like, like_id)
        if not place:
            raise HTTPException(status_code=404, detail="Item not found")
        return place

    async def get_all(self) -> List[Like]:
        result = await self.session.execute(select(Like))
        return list(result.scalars().all())

    async def delete(self, like: Like) -> None:
        await self.session.delete(like)
