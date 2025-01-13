from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database.connection_async import get_async_session
from src.travel.models.travel_route_place import TravelRoute, TravelRoutePlace


class TravelRouteRepository:
    def __init__(self, async_session: AsyncSession = Depends(get_async_session)):
        self.async_session = async_session

    async def save(self, travel_route: TravelRoute) -> TravelRoute:
        self.async_session.add(travel_route)
        await self.async_session.commit()
        return travel_route

    async def save_bulk(self, travel_route_list: list[TravelRoute]) -> list[TravelRoute]:
        self.async_session.add_all(travel_route_list)
        await self.async_session.commit()
        return travel_route_list

    async def get_by_id(self, travel_route_id: int) -> TravelRoute | None:
        travel = await self.async_session.execute(
            select(TravelRoute)
            .options(selectinload(TravelRoute.travel_route_places).selectinload(TravelRoutePlace.place), selectinload(TravelRoute.reviews))  # type: ignore
            .where(TravelRoute.id == travel_route_id)  # type: ignore
        )
        travel = travel.scalars().one_or_none()  # type: ignore
        if not travel:
            raise HTTPException(status_code=404, detail="Item not found")
        return travel  # type: ignore

    async def get_place_list(self) -> list[TravelRoute]:
        result = await self.async_session.execute(select(TravelRoute))
        return list(result.scalars().all())

    async def get_tarvel_route_list_by_user(self, user_id: str) -> list[TravelRoute]:
        if user_id is None:
            raise HTTPException(status_code=404, detail="user_id is required")
        else:
            travel = await self.async_session.execute(select(TravelRoute).options(selectinload(TravelRoute.travel_route_places).selectinload(TravelRoutePlace.place), selectinload(TravelRoute.reviews)).where(TravelRoute.user_id == user_id))  # type: ignore
        if not travel:
            raise HTTPException(status_code=404, detail="Item not found")
        return list(travel.scalars().all())

    async def delete(self, travel_route_id: int) -> bool:
        result = await self.async_session.get(TravelRoute, travel_route_id)
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        await self.async_session.delete(result)
        await self.async_session.commit()
        return True
