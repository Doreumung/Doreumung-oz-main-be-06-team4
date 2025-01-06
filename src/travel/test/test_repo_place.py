import time

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.travel.models.place import Place, PlaceUpdate  # 테스트할 모델 import
from src.travel.repo.place_repo import PlaceRepository

# 오류가 발생했었는데 postgresql서버가 제대로 동작안하고 무한루프에 빠지는 오류
# 확인해보니 테스트엔 순서가 무작위 하는걸 간과하여 특정 오류가떳는데 그로인해 자원이 제대로 반환되지못해
# 발생한 오류였다 db서버를 껏다 키면 해결되는문제였다. 그런데 이상한점은 connection된 수가 4개밖에 안되었는데
# 왜 many_client 오류가 떳는지 알수가없다...
"""
오류 발생: 데이터베이스엔 datetime타입이였으나,datetime.now(kst)와같은 
         timezone datetime 타입으로 저장하여 타입불일치 오류발생
오류 해결: sa_column=Column(DateTime(timezone=True) timezone을 명시하여 해결
"""


@pytest.mark.asyncio
class TestPlaceRepository:

    async def test_save_place_model(self, async_session: AsyncSession) -> None:
        place_repository = PlaceRepository(async_session)
        place = Place(name="한라산", theme="해변", address="제주시", latitude=123.21314214, longitude=123.21314214)
        new_place = await place_repository.save(place)
        assert new_place.__dict__ == place.__dict__

    async def test_update_place_model(self, async_session: AsyncSession) -> None:
        place_repository = PlaceRepository(async_session)
        place = Place(
            id=1, name="한라산", theme="해변", address="제주시", latitude=123.21314214, longitude=123.21314214
        )
        new_place = await place_repository.save(place)
        place_repository = PlaceRepository(async_session)
        place_update = PlaceUpdate(name="한라산1")
        assert await place_repository.update(place_update, 1)

    async def test_delete_place_model(self, async_session: AsyncSession) -> None:
        place_repository = PlaceRepository(async_session)
        place = Place(name="한라산", theme="해변", address="제주시", latitude=123.21314214, longitude=123.21314214)
        new_place = await place_repository.save(place)
        assert await place_repository.delete(1)
        result = await async_session.get(Place, 1)
        assert not result

    async def test_get_by_theme_and_region(self, async_session: AsyncSession) -> None:
        place_repository = PlaceRepository(async_session)
        place = Place(name="한라산", theme="해변", address="제주시", latitude=123.21314214, longitude=123.21314214)
        new_place = await place_repository.save(place)
        get_place = place_repository.get_by_theme_and_region(theme="해변", region="제주시")
        assert get_place == get_place

    async def test_get_place_list(self, async_session: AsyncSession) -> None:
        place_repository = PlaceRepository(async_session)
        place_list = []
        place_list.append(
            Place(name="한라산1", theme="자연", address="서귀포시", latitude=123.21314214, longitude=123.21314214)
        )
        place_list.append(
            Place(name="한라산2", theme="해변", address="한경면", latitude=123.21314214, longitude=123.21314214)
        )
        place_list.append(
            Place(name="한라산3", theme="액티비티", address="한림읍", latitude=123.21314214, longitude=123.21314214)
        )
        place_list.append(
            Place(name="한라산4", theme="카페", address="애월읍", latitude=123.21314214, longitude=123.21314214)
        )
        place_list.append(
            Place(name="한라산5", theme="전시", address="조천읍", latitude=123.21314214, longitude=123.21314214)
        )
        new_place_list = await place_repository.save_bulk(place_list=place_list)
        place_list = await place_repository.get_place_list()
        assert len(new_place_list) == len(place_list)

    async def test_get_by_id(self, async_session: AsyncSession) -> None:
        place_repository = PlaceRepository(async_session)
        place = Place(name="한라산", theme="해변", address="제주시", latitude=123.21314214, longitude=123.21314214)
        new_place = await place_repository.save(place)
        if new_place.id is not None:
            get_place = await place_repository.get_by_id(new_place.id)
            assert get_place.id == new_place.id
        else:
            assert False
