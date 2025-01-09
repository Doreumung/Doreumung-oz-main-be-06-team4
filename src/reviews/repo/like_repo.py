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

    async def get_by_id(self, like_id: int) -> Optional[Like]:
        place = await self.session.get(Like, like_id)
        if not place:
            raise HTTPException(status_code=404, detail="Item not found")
        return place

    async def get_all(self) -> List[Like]:
        result = await self.session.execute(select(Like))
        return list(result.scalars().all())

    async def delete(self, like_id: int) -> None:
        result = await self.session.get(Like, like_id)
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        await self.session.delete(result)
        await self.session.commit()
