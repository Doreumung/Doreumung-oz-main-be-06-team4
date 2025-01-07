from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src import User
from src.travel.models.travel_route_place import TravelRoute
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.user.repo.repository import UserRepository


@pytest.mark.asyncio
class TestTravelRouteRepository:

    async def test_save_travel_route_model(
        self, travel_route_repository: TravelRouteRepository, user_save_init: tuple[User, User]
    ) -> None:
        user1, user2 = user_save_init
        travel_route = TravelRoute(
            id=6,
            title="ddd",
            user_id=user1.id,
            regions="제주시",
            themes="자연",
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
        new_travel_route = await travel_route_repository.save(travel_route)
        assert new_travel_route.__dict__ == travel_route.__dict__ and new_travel_route.id

    async def test_get_travel_route_list(
        self, travel_route_init: list[TravelRoute], travel_route_repository: TravelRouteRepository
    ) -> None:
        saved_travel_list = travel_route_init
        get_travel_list = await travel_route_repository.get_place_list()  # LIMIT 설정
        assert {t.id for t in saved_travel_list} == {d.id for d in get_travel_list}  # 길이보단 실제 데이터의 id 비교

    async def test_get_travel_route_list_by_user(
        self,
        user_save_init: tuple[User, User],
        travel_route_init: list[TravelRoute],
        user_repository: UserRepository,
        travel_route_repository: TravelRouteRepository,
    ) -> None:
        user1, user2 = user_save_init
        saved_travel_list = travel_route_init
        travel_list = await travel_route_repository.get_tarvel_route_list_by_user(user_id=user1.id)
        comp_list = [i for i in saved_travel_list if i.user_id == user1.id]
        assert len(travel_list) == len(comp_list)

    async def test_get_by_id(
        self, travel_route_init: list[TravelRoute], travel_route_repository: TravelRouteRepository
    ) -> None:
        comp_id = travel_route_init[0].id
        if comp_id is None:
            assert True
        get_place = await travel_route_repository.get_by_id(comp_id)  # type: ignore
        if not get_place:
            assert False
        assert get_place.id == comp_id

    async def test_delete_travel_route_model(
        self, travel_route_init: list[TravelRoute], travel_route_repository: TravelRouteRepository
    ) -> None:
        saved_travel_list = travel_route_init
        comp_id = saved_travel_list[0].id
        if comp_id is None:
            assert True
        await travel_route_repository.delete(comp_id)  # type: ignore
        try:
            await travel_route_repository.get_by_id(comp_id)  # type: ignore
        except (HTTPException, NoResultFound):
            assert True  # 두 예외 중 하나가 발생하면 테스트 성공
        else:
            pytest.fail("Neither HTTPException nor NoResultFound was raised")
