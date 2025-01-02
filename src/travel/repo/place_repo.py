import os

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_async_session
from src.travel.models.place import Place, PlaceUpdate


class PlaceRepository:
    def __init__(self, async_session: AsyncSession = Depends(get_async_session)):
        self.async_session = async_session

    async def save(self, place: Place) -> Place:
        self.async_session.add(place)
        await self.async_session.commit()
        return place

    async def save_bulk(self, place_list: list[Place]) -> list[Place]:
        self.async_session.add_all(place_list)
        await self.async_session.commit()
        return place_list

    async def update(self, place: PlaceUpdate, place_id: int) -> Place:
        result = await self.async_session.get(Place, place_id)
        if not result:
            raise HTTPException(status_code=404, detail="Place not found")

        place_data = place.model_dump(exclude_unset=True)
        result.sqlmodel_update(place_data)
        await self.async_session.commit()
        return result

    async def get_place_list(self) -> list[Place]:
        result = await self.async_session.execute(select(Place))
        return list(result.scalars().all())

    async def get_by_theme_and_region(self, theme: str, region: str) -> Place:
        place = await self.async_session.execute(select(Place).filter_by(theme=theme, region=region))
        place = place.scalars().first()  # type: ignore
        if not place:
            raise HTTPException(status_code=404, detail="Item not found")
        return place  # type: ignore

    async def get_by_id(self, place_id: int) -> Place:
        place = await self.async_session.get(Place, place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Item not found")
        return place

    async def delete(self, place_id: int) -> bool:
        result = await self.async_session.get(Place, place_id)
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        await self.async_session.delete(result)
        await self.async_session.commit()
        return True
