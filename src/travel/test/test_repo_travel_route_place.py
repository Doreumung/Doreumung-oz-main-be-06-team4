from datetime import datetime, time

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import Place, User  # type: ignore
from src.travel.models.travel_route_place import TravelRoute, TravelRoutePlace
from src.travel.repo.place_repo import PlaceRepository
from src.travel.repo.travel_route_place_repo import TravelRoutePlaceRepository
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.user.repo.repository import UserRepository


async def travel_route_place_init(
    user_repository: UserRepository,
    place_repository: PlaceRepository,
    travel_route_repository: TravelRouteRepository,
    travel_route_place_repository: TravelRoutePlaceRepository,
) -> None:
    user = User(
        id="1",
        email="<EMAIL>",
        password="<PASSWORD>",
        birthday=datetime.now(),
        gender="MALE",
        oauth_id="12",
        is_superuser=False,
        social_provider="KAKAO",
        is_deleted=False,
        nickname="dwaf",
    )
    await user_repository.save(user)
    travel_route_place_list = []
    place = Place(id=1, name="한라산", theme="자연", address="서귀포시", latitude=123.21314214, longitude=123.21314214)
    await place_repository.save(place)
    travel_route = TravelRoute(
        id=1,
        user_id="1",
        regions="제주시",
        themes="자연",
        breakfast=True,
        morning=1,
        lunch=True,
        afternoon=1,
        dinner=True,
    )
    await travel_route_repository.save(travel_route)
    travel_route_place_list.append(
        TravelRoutePlace(travel_route_id=1, place_id=1, priority=5, route_time=time(hour=3, minute=30), distance=15.5)
    )
    travel_route_place_list.append(
        TravelRoutePlace(travel_route_id=1, place_id=1, priority=4, route_time=time(hour=2, minute=30), distance=13.5)
    )
    travel_route_place_list.append(
        TravelRoutePlace(travel_route_id=1, place_id=1, priority=3, route_time=time(hour=1, minute=30), distance=11.5)
    )
    travel_route_place_list.append(
        TravelRoutePlace(travel_route_id=1, place_id=1, priority=2, route_time=time(hour=5, minute=30), distance=14.5)
    )
    travel_route_place_list.append(
        TravelRoutePlace(travel_route_id=1, place_id=1, priority=1, route_time=time(hour=4, minute=30), distance=12.5)
    )
    await travel_route_place_repository.save_bulk(travel_route_place_list=travel_route_place_list)


@pytest.mark.asyncio
class TestTravelRouteRepository:

    async def test_save_travel_route_place_model(
        self,
        user_repository: UserRepository,
        place_repository: PlaceRepository,
        travel_route_repository: TravelRouteRepository,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        await travel_route_place_init(
            user_repository, place_repository, travel_route_repository, travel_route_place_repository
        )
        travel_route_place = TravelRoutePlace(
            travel_route_id=1, place_id=1, priority=5, route_time=time(hour=3, minute=30), distance=15.5
        )
        new_travel_route_place = await travel_route_place_repository.save(travel_route_place)
        assert new_travel_route_place.__dict__ == travel_route_place.__dict__ and new_travel_route_place.id

    async def test_get_travel_route_list(
        self,
        user_repository: UserRepository,
        place_repository: PlaceRepository,
        travel_route_repository: TravelRouteRepository,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        await travel_route_place_init(
            user_repository, place_repository, travel_route_repository, travel_route_place_repository
        )
        travel_route_place_list = await travel_route_place_repository.get_travel_route_list()
        assert len(travel_route_place_list) == 5

    async def test_get_travel_route_place_list_by_travel_route(
        self,
        user_repository: UserRepository,
        place_repository: PlaceRepository,
        travel_route_repository: TravelRouteRepository,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        await travel_route_place_init(
            user_repository, place_repository, travel_route_repository, travel_route_place_repository
        )
        travel_list = await travel_route_place_repository.get_travel_route_place_list_by_travel_route(travel_route_id=1)
        assert len(travel_list) == 5
        with pytest.raises(HTTPException):
            await travel_route_place_repository.get_travel_route_place_list_by_travel_route(travel_route_id=2)

    async def test_get_by_id(
        self,
        user_repository: UserRepository,
        place_repository: PlaceRepository,
        travel_route_repository: TravelRouteRepository,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        await travel_route_place_init(
            user_repository, place_repository, travel_route_repository, travel_route_place_repository
        )
        get_travel = await travel_route_place_repository.get_by_id(2)
        assert get_travel.id == 2

    async def test_delete_travel_route_model(
        self,
        user_repository: UserRepository,
        place_repository: PlaceRepository,
        travel_route_repository: TravelRouteRepository,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        await travel_route_place_init(
            user_repository, place_repository, travel_route_repository, travel_route_place_repository
        )
        await travel_route_place_repository.delete(1)
        with pytest.raises(HTTPException):
            await travel_route_place_repository.get_by_id(1)
        with pytest.raises(HTTPException):
            await travel_route_place_repository.delete(1)
