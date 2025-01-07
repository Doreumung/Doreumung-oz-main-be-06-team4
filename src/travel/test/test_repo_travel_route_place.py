from datetime import time

import pytest
from fastapi import HTTPException

from src import Place, User  # type: ignore
from src.travel.models.travel_route_place import TravelRoute, TravelRoutePlace
from src.travel.repo.place_repo import PlaceRepository
from src.travel.repo.travel_route_place_repo import TravelRoutePlaceRepository
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.user.repo.repository import UserRepository


@pytest.mark.asyncio
class TestTravelRouteRepository:

    async def test_save_travel_route_place_model(
        self,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        travel_route_place = TravelRoutePlace(
            travel_route_id=1, place_id=1, priority=5, route_time=time(hour=3, minute=30), distance=15.5
        )
        new_travel_route_place = await travel_route_place_repository.save(travel_route_place)
        assert new_travel_route_place.__dict__ == travel_route_place.__dict__ and new_travel_route_place.id

    async def test_get_travel_route_list(
        self,
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        travel_route_place_list = await travel_route_place_repository.get_travel_route_list()
        assert len(travel_route_place_list) == 5

    async def test_get_travel_route_place_list_by_travel_route(
        self,
        travel_route_init: list[TravelRoute],
        travel_route_place_init: list[TravelRoutePlace],
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        travel_id = travel_route_init[0].id
        if travel_id is None:
            assert True
        comp_list = [i for i in travel_route_place_init if i.travel_route_id == travel_id]
        travel_list = await travel_route_place_repository.get_travel_route_place_list_by_travel_route(
            travel_route_id=travel_id  # type: ignore
        )
        assert len(travel_list) == len(comp_list)
        with pytest.raises(HTTPException):
            await travel_route_place_repository.get_travel_route_place_list_by_travel_route(travel_route_id=-1)

    async def test_get_by_id(
        self,
        travel_route_place_init: list[TravelRoutePlace],
        travel_route_place_repository: TravelRoutePlaceRepository,
    ) -> None:
        trp_id = travel_route_place_init[0].id
        if trp_id is not None:
            get_travel = await travel_route_place_repository.get_by_id(trp_id)
            assert get_travel.id == trp_id
        assert False

    async def test_delete_travel_route_model(
        self, travel_route_place_init: list[TravelRoutePlace], travel_route_place_repository: TravelRoutePlaceRepository
    ) -> None:
        trp_id = travel_route_place_init[0].id
        if trp_id is None:
            assert True
        await travel_route_place_repository.delete(trp_id)  # type: ignore
        with pytest.raises(HTTPException):
            await travel_route_place_repository.get_by_id(trp_id)  # type: ignore
        with pytest.raises(HTTPException):
            await travel_route_place_repository.delete(trp_id)  # type: ignore
