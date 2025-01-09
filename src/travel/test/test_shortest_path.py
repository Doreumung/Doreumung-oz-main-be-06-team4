# import pytest
#
# from src import Place  # type: ignore
# from src.travel.dtos.base_travel_route import Schedule
# from src.travel.models.enums import RegionEnum, ThemeEnum
# from src.travel.services.generate_place_list import complete_place_list
# from src.travel.services.shortest_path_sort import (
#     create_distance_matrix,
#     solve_tsp_brute_force,
# )
#
#
# @pytest.mark.asyncio
# class TestShortestPath:
#     async def test_random_place_list(
#         self,
#     ) -> None:
#         selected_themes = [ThemeEnum("자연"), ThemeEnum("액티비티")]
#         selected_regions = [RegionEnum("서귀포시"), RegionEnum("한림읍"), RegionEnum("안덕면")]
#         selected_schedule = Schedule(breakfast=True, lunch=True, dinner=True, morning=1, afternoon=2)
#         place_list = complete_place_list(regions=selected_regions, themes=selected_themes, schedule=selected_schedule)
#         place_list = (
#             [place_list.breakfast, place_list.lunch, place_list.dinner] + place_list.morning + place_list.afternoon  # type: ignore
#         )
#         distance_matrix = create_distance_matrix(place_list)  # type: ignore
#         route, distance = solve_tsp_brute_force(distance_matrix)
#         print([i.name for i in place_list])  # type: ignore
#         print("Best Route:", route)
#         print("Best Distance:", distance)
