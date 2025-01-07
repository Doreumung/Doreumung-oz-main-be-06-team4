import asyncio
from datetime import date, datetime, time
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src import Place, TravelRoute, TravelRoutePlace, User  # type: ignore
from src.config import settings
from src.config.orm import Base
from src.travel.repo.place_repo import PlaceRepository
from src.travel.repo.travel_route_place_repo import TravelRoutePlaceRepository
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.user.repo.repository import UserRepository

engine = create_async_engine(settings.TEST_ASYNC_DATABASE_URL, echo=True, future=True)

# 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    # 세션 범위의 이벤트 루프를 설정
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    # 테스트용 데이터베이스 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    # 테스트 후 데이터베이스 정리
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def travel_route_place_repository(async_session: AsyncSession) -> TravelRoutePlaceRepository:
    return TravelRoutePlaceRepository(async_session)


@pytest.fixture
def travel_route_repository(async_session: AsyncSession) -> TravelRouteRepository:
    return TravelRouteRepository(async_session)


@pytest.fixture
def place_repository(async_session: AsyncSession) -> PlaceRepository:
    return PlaceRepository(async_session)


@pytest.fixture
def user_repository(async_session: AsyncSession) -> UserRepository:
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def user_save_init(user_repository: UserRepository) -> tuple[User, User]:
    user1 = User(
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
    await user_repository.save(user1)
    user2 = User(
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
    await user_repository.save(user2)
    return user1, user2


@pytest.fixture
def place_list_for_service() -> list[Place]:
    place_list = []
    # 제주카트클럽 근처 식당(3km이내)
    place_list.append(
        Place(name="저지신토불이식당", theme="식당", region="한경면", latitude=33.342593, longitude=126.255824)
    )
    place_list.append(
        Place(name="더애월 저지점", theme="식당", region="한경면", latitude=33.337698, longitude=126.266830)
    )
    # 서귀포 자연휴양림 근처 식당(3km이내)
    place_list.append(
        Place(name="엘에이치큐프로", theme="식당", region="서귀포시", latitude=33.306827, longitude=126.432709)
    )
    # 군산오름 근처 식당(3km이내)
    place_list.append(Place(name="민영식당", theme="식당", region="서귀포시", latitude=33.246113, longitude=126.388198))
    place_list.append(
        Place(name="색달식당 중문본점", theme="식당", region="서귀포시 ", latitude=33.241829, longitude=126.386383)
    )
    return place_list


@pytest_asyncio.fixture
async def place_list_init(place_repository: PlaceRepository) -> list[Place]:
    place_list = []
    place_list.append(
        Place(id=1, name="군산오름", theme="자연", region="안덕면", latitude=33.253217, longitude=126.370693)
    )
    place_list.append(
        Place(id=2, name="서귀포 자연휴양림", theme="자연", region="서귀포시", latitude=33.311453, longitude=126.458861)
    )
    place_list.append(
        Place(id=3, name="제주카트클럽", theme="액티비티", region="한림읍", latitude=33.347790, longitude=126.255974)
    )
    place_list.append(
        Place(id=4, name="저지신토불이식당", theme="식당", region="한경면", latitude=33.342593, longitude=126.255824)
    )
    place_list.append(
        Place(id=5, name="더애월 저지점", theme="식당", region="한경면", latitude=33.337698, longitude=126.266830)
    )
    # 서귀포 자연휴양림 근처 식당(3km이내)
    place_list.append(
        Place(id=6, name="엘에이치큐프로", theme="식당", region="서귀포시", latitude=33.306827, longitude=126.432709)
    )
    place_list.append(
        Place(id=7, name="엘에이", theme="식당", region="서귀포시", latitude=33.307827, longitude=126.432709)
    )
    place_list.append(
        Place(id=8, name="큐프로", theme="식당", region="서귀포시", latitude=33.310827, longitude=126.432709)
    )
    # 군산오름 근처 식당(3km이내)
    place_list.append(
        Place(id=9, name="민영식당", theme="식당", region="서귀포시", latitude=33.246113, longitude=126.388198)
    )
    place_list.append(
        Place(id=10, name="식당", theme="식당", region="서귀포시", latitude=33.248113, longitude=126.388198)
    )
    place_list.append(
        Place(id=11, name="민영", theme="식당", region="서귀포시", latitude=33.247113, longitude=126.388198)
    )
    place_list.append(
        Place(
            id=12, name="색달식당 중문본점", theme="식당", region="서귀포시", latitude=33.241829, longitude=126.386383
        )
    )
    return await place_repository.save_bulk(place_list)


@pytest_asyncio.fixture
async def travel_route_init(
    user_save_init: tuple[TravelRoute, TravelRoute], travel_route_repository: TravelRouteRepository
) -> list[TravelRoute]:
    user1, user2 = user_save_init
    travel_route_list = []
    travel_route_list.append(
        TravelRoute(
            user_id=user1.id,
            title="awdaw",
            regions=["제주시"],
            themes=["자연"],
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            user_id=user2.id,
            title="awdaw",
            regions=["제주시"],
            themes=["자연"],
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            user_id=user2.id,
            title="awdaw",
            regions=["제주시"],
            themes=["자연"],
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            user_id=user2.id,
            title="awdaw",
            regions=["제주시"],
            themes=["자연"],
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_route_list.append(
        TravelRoute(
            user_id=user2.id,
            title="awdaw",
            regions=["제주시"],
            themes=["자연"],
            breakfast=True,
            morning=1,
            lunch=True,
            afternoon=1,
            dinner=True,
        )
    )
    travel_list_result = await travel_route_repository.save_bulk(travel_route_list=travel_route_list)
    return travel_list_result


@pytest_asyncio.fixture
async def travel_route_place_init(
    place_list_init: list[Place],
    travel_route_init: list[TravelRoute],
    travel_route_place_repository: TravelRoutePlaceRepository,
) -> list[TravelRoutePlace]:
    place_id = place_list_init[0].id
    travel_route_id = travel_route_init[0].id
    travel_route_place_list = []
    travel_route_place_list.append(
        TravelRoutePlace(
            travel_route_id=travel_route_id,
            place_id=place_id,
            priority=5,
        )
    )
    travel_route_place_list.append(
        TravelRoutePlace(
            travel_route_id=travel_route_id,
            place_id=place_id,
            priority=4,
        )
    )
    travel_route_place_list.append(
        TravelRoutePlace(
            travel_route_id=travel_route_id,
            place_id=place_id,
            priority=3,
        )
    )
    travel_route_place_list.append(
        TravelRoutePlace(
            travel_route_id=travel_route_id,
            place_id=place_id,
            priority=2,
        )
    )
    travel_route_place_list.append(
        TravelRoutePlace(
            travel_route_id=travel_route_id,
            place_id=place_id,
            priority=1,
        )
    )
    return await travel_route_place_repository.save_bulk(travel_route_place_list=travel_route_place_list)
