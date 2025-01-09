# import pytest
# from rich.theme import Theme
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src import Place  # type: ignore
# from src.travel.dtos.base_travel_route import Schedule
# from src.travel.models.enums import RegionEnum, ThemeEnum
# from src.travel.services.generate_place_list import (  # type: ignore
#     complete_place_list,
#     haversine,
#     random_eating_place_list,
#     random_place_list,
# )
#
#
# @pytest.mark.asyncio
# class TestGeneratePlaceListRepository:
#     async def test_random_place_list(self) -> list[Place]:
#         selected_themes = [ThemeEnum("자연"), ThemeEnum("액티비티")]
#         selected_regions = [RegionEnum("서귀포시"), RegionEnum("한림읍"), RegionEnum("안덕면")]
#         selected_morning_num = 1
#         selected_afternoon_num = 1
#         random_list = random_place_list(
#             themes=selected_themes,
#             regions=selected_regions,
#             morning=selected_morning_num,
#             afternoon=selected_afternoon_num,
#         )
#         assert len(random_list) == selected_morning_num + selected_afternoon_num
#         assert {i.theme for i in random_list} <= set(selected_themes)
#         assert {i.region for i in random_list} <= set(selected_regions)
#         return random_list
#
#     async def test_random_eating_place(self, place_list_for_service: list[Place]) -> None:
#         start_place = Place(name="군산오름", theme="자연", region="안덕면", latitude=33.253217, longitude=126.370693)
#         end_place = Place(
#             name="제주카트클럽", theme="액티비티", region="한림읍", latitude=33.347790, longitude=126.255974
#         )
#         random_eating_place = random_eating_place_list(
#             start_place=start_place, end_place=end_place, place_list=place_list_for_service
#         )
#         distance = haversine(
#             start_place.latitude, start_place.longitude, random_eating_place.latitude, random_eating_place.longitude
#         )
#         assert distance < 3
#
#     async def test_complete_place_list(self, async_session: AsyncSession, place_list_init: list[Place]) -> None:
#         selected_themes = [ThemeEnum("자연"), ThemeEnum("액티비티")]
#         selected_regions = [RegionEnum("서귀포시"), RegionEnum("한림읍"), RegionEnum("안덕면")]
#         selected_schedule = Schedule(breakfast=False, lunch=True, dinner=True, morning=1, afternoon=2)
#         place_list = complete_place_list(regions=selected_regions, themes=selected_themes, schedule=selected_schedule)
#         print(place_list)
#         place_list = (
#             [place_list.breakfast, place_list.lunch, place_list.dinner] + place_list.morning + place_list.afternoon  # type: ignore
#         )
#         place_list = [await async_session.get(Place, i.place_id) for i in place_list if i]  # type: ignore
#         print(place_list)
#         no_restaurant_list = [i for i in place_list if i.theme != "식당"]  # type: ignore
#         selected_themes = set(selected_themes)  # type: ignore
#         selected_themes.add(ThemeEnum("식당"))  # type: ignore
#         assert len(place_list) == 5  # type: ignore
#         assert {i.theme for i in place_list} <= selected_themes  # type: ignore
#         assert {RegionEnum(i.region) for i in no_restaurant_list} <= set(selected_regions)  # type: ignore
