# import pytest
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src.travel.models.place import Place
#
#
# #  save 테스트
# @pytest.mark.asyncio
# async def test_save_place_model(async_session: AsyncSession):
#     place = Place(name="한라산", theme="해변", address="제주시", latitude=123.21314214, longitude=123.21314214)
#     async_session.add(place)
#     await async_session.commit()
#     await async_session.refresh(place)
#     assert (
#         place.name == "한라산"
#         and place.theme == "해변"
#         and place.address == "제주시"
#         and place.latitude == 123.21314214
#         and place.longitude == 123.21314214
#     )
