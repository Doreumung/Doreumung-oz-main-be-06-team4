from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import User
from src.travel.models.travel_route_place import TravelRoute
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.user.repo.repository import UserRepository


async def travel_route_init(user_repository: UserRepository, travel_route_repository: TravelRouteRepository) -> None:
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
    user = User(
        id="2",
        email="<EMAILd>",
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
    travel_route_list = []
    travel_route_list.append(
        TravelRoute(
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
    )
    travel_route_list.append(
        TravelRoute(
            id=2,
            user_id="1",
            regions="제주시",
            themes="자연",
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            id=3,
            user_id="2",
            regions="제주시",
            themes="자연",
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            id=4,
            user_id="2",
            regions="제주시",
            themes="자연",
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            id=5,
            user_id="2",
            regions="제주시",
            themes="자연",
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    await travel_route_repository.save_bulk(travel_route_list=travel_route_list)


@pytest.mark.asyncio
class TestTravelRouteRepository:
    @pytest.fixture
    def travel_route_repository(self, async_session: AsyncSession) -> TravelRouteRepository:
        return TravelRouteRepository(async_session)

    @pytest.fixture
    def user_repository(self, async_session: AsyncSession) -> UserRepository:
        return UserRepository(async_session)

    async def test_save_travel_route_model(
        self, user_repository: UserRepository, travel_route_repository: TravelRouteRepository
    ) -> None:
        await travel_route_init(user_repository, travel_route_repository)
        travel_route = TravelRoute(
            id=6,
            user_id="1",
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
        self, user_repository: UserRepository, travel_route_repository: TravelRouteRepository
    ) -> None:
        await travel_route_init(user_repository, travel_route_repository)
        travel_route_list = await travel_route_repository.get_place_list()
        assert len(travel_route_list) == 5

    async def test_get_travel_route_list_by_user(
        self, user_repository: UserRepository, travel_route_repository: TravelRouteRepository
    ) -> None:
        await travel_route_init(user_repository, travel_route_repository)
        travel_list = await travel_route_repository.get_tarvel_route_list_by_user(user_id="2")
        assert len(travel_list) == 3

    async def test_get_by_id(
        self, user_repository: UserRepository, travel_route_repository: TravelRouteRepository
    ) -> None:
        await travel_route_init(user_repository, travel_route_repository)
        get_place = await travel_route_repository.get_by_id(2)
        assert get_place.id == 2

    async def test_delete_travel_route_model(
        self, user_repository: UserRepository, travel_route_repository: TravelRouteRepository
    ) -> None:
        await travel_route_init(user_repository, travel_route_repository)
        await travel_route_repository.delete(1)
        with pytest.raises(HTTPException):
            await travel_route_repository.get_by_id(1)
