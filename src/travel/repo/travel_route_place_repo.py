from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_async_session
from src.travel.models.travel_route_place import TravelRoutePlace


class TravelRoutePlaceRepository:
    def __init__(self, async_session: AsyncSession = Depends(get_async_session)):
        self.async_session = async_session

    async def save(self, travel_route_place: TravelRoutePlace) -> TravelRoutePlace:
        self.async_session.add(travel_route_place)
        await self.async_session.commit()
        return travel_route_place

    async def save_bulk(self, travel_route_place_list: list[TravelRoutePlace]) -> list[TravelRoutePlace]:
        self.async_session.add_all(travel_route_place_list)
        await self.async_session.commit()
        return travel_route_place_list

    async def get_by_id(self, travel_route_place_id: int) -> TravelRoutePlace:
        travel = await self.async_session.get(TravelRoutePlace, travel_route_place_id)
        if not travel:
            raise HTTPException(status_code=404, detail="Item not found")
        return travel

    async def get_travel_route_list(self) -> list[TravelRoutePlace]:
        result = await self.async_session.execute(select(TravelRoutePlace))
        return list(result.scalars().all())

    async def get_travel_route_place_list_by_travel_route(self, travel_route_id: int) -> list[TravelRoutePlace]:
        result = await self.async_session.execute(
            select(TravelRoutePlace).where(TravelRoutePlace.travel_route_id == travel_route_id)  # type: ignore
        )
        travel = result.scalars().all()
        if not travel:  # if not result.scalars().all(): 하면 오류가 발생하지않음
            raise HTTPException(status_code=404, detail="Item not found")
        return list(travel)

    async def delete(self, travel_route_id: int) -> None:
        travel = await self.async_session.get(TravelRoutePlace, travel_route_id)
        if not travel:
            raise HTTPException(status_code=404, detail="Item not found")
        await self.async_session.delete(travel)
        await self.async_session.commit()
