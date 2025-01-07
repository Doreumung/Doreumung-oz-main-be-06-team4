import random
from math import atan2, cos, radians, sin, sqrt

from src import Place  # type: ignore
from src.travel.dtos.base_travel_route import PlaceInfo, Schedule, ScheduleInfo
from src.travel.models.enums import RegionEnum, ThemeEnum
from src.travel.services.shortest_path_sort import (
    create_distance_matrix,
    haversine,
    solve_tsp_brute_force,
)


def loading_place_list() -> list[Place]:
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
    return place_list


def eating_place_list_to() -> list[Place]:
    place_list = []
    # 제주카트클럽 근처 식당(3km이내)
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
            id=12, name="색달식당 중문본점", theme="식당", region="서귀포시 ", latitude=33.241829, longitude=126.386383
        )
    )
    return place_list


# 전역변수로 미리 로드
all_place_list = loading_place_list()


# service 함수
def random_place_list(regions: list[RegionEnum], themes: list[ThemeEnum], morning: int, afternoon: int) -> list[Place]:
    global all_place_list
    filtered_list = [i for i in all_place_list if i.theme in themes and i.region in regions]
    selected_themes: set[ThemeEnum] = set()
    selected_regions: set[RegionEnum] = set()
    result_place = []
    for i in range(morning + afternoon):
        excluded_list: list[Place] = []
        temp_list = [i for i in filtered_list]
        choice_place = None
        while temp_list:
            choice_place = random.choice(temp_list)
            # 선택한 테마와 지역들이 이미 모두다 선택됐으면 조건 무시
            if selected_themes == set([i.value for i in themes]) and selected_regions == set(
                [i.value for i in regions]
            ):
                break
            # 테마와 지역들을 최대한 골고루 배정하기위해 이미 선택된것들 제외
            if choice_place.region not in selected_regions or choice_place.theme not in selected_themes:
                selected_regions.add(choice_place.region)
                selected_themes.add(choice_place.theme)
                break
            temp_list.remove(choice_place)
        # 정상적으로 break를 타고 나왔을때만 result에 추가
        if temp_list:
            filtered_list.remove(choice_place)  # type: ignore
            result_place.append(choice_place)
        # 이미 조건에맞는 장소가 남아있지않으므로 break후 무작위 선택
        else:
            break
    # 추가적으로 골라야할 장소의 갯수
    will_append_place_num = morning + afternoon - len(result_place)
    if will_append_place_num:
        # 이미선택된 장소 제외
        temp_list = [i for i in filtered_list if i not in result_place]
        # random.sample로 중복없이 부족한갯수 채우기
        result_place.append(random.sample(temp_list, will_append_place_num))  # type: ignore

    return result_place  # type: ignore


def point_to_line_distance(
    lat1: float, lon1: float, lat2: float, lon2: float, lat_rest: float, lon_rest: float
) -> float:
    # 직선 방정식 기반 거리 계산
    numerator = abs((lon2 - lon1) * (lat_rest - lat1) - (lat2 - lat1) * (lon_rest - lon1))
    denominator = sqrt((lon2 - lon1) ** 2 + (lat2 - lat1) ** 2)
    return numerator / denominator


# 필터링: 두 장소 사이 선분 근처에 있는 식당 찾기
def is_near_line(place1: Place, place2: Place, restaurant: Place, max_distance_km: int = 5) -> bool:
    distance = point_to_line_distance(
        place1.latitude, place1.longitude, place2.latitude, place2.longitude, restaurant.latitude, restaurant.longitude
    )
    return distance <= max_distance_km


def place_list_close_line(start_place: Place, end_place: Place, restaurants: list[Place]) -> list[Place]:
    filtered_restaurants = [
        restaurant for restaurant in restaurants if is_near_line(start_place, end_place, restaurant, 3)
    ]
    return filtered_restaurants


def place_list_in_radius(start_place: Place, radius: int, place_list: list[Place]) -> list[Place]:
    result_place = []
    for place in place_list:
        if haversine(start_place.latitude, start_place.longitude, place.latitude, place.longitude) <= radius:
            result_place.append(place)
    return result_place


# service 함수
def random_eating_place_list(start_place: Place, end_place: Place | None, place_list: list[Place]) -> Place:
    filtered_list = place_list_in_radius(start_place, 3, place_list)
    if end_place is not None:
        place_list_close_line(start_place, end_place, filtered_list)

    choice_place = random.choice(filtered_list)
    place_list.remove(choice_place)
    return choice_place


def complete_place_list(regions: list[RegionEnum], themes: list[ThemeEnum], schedule: Schedule) -> list[Place]:
    place_list = random_place_list(
        regions=regions, themes=themes, morning=schedule.morning, afternoon=schedule.afternoon
    )
    distance_matrix = create_distance_matrix(place_list)
    best_route, best_distance = solve_tsp_brute_force(distance_matrix)
    sorted_place_list = [place_list[i] for i in best_route]
    eating_list = eating_place_list_to()
    breakfast = None
    morning = [PlaceInfo.model_validate(sorted_place_list[i]) for i in range(schedule.morning)]
    lunch = None
    afternoon = [
        PlaceInfo.model_validate(sorted_place_list[i])
        for i in range(schedule.morning, schedule.morning + schedule.afternoon)
    ]
    dinner = None
    if schedule.morning > 0:
        if schedule.breakfast:
            breakfast = PlaceInfo.model_validate(
                random_eating_place_list(start_place=morning[0], end_place=None, place_list=eating_list)  # type: ignore
            )
        if schedule.lunch:
            lunch = PlaceInfo.model_validate(
                random_eating_place_list(start_place=morning[-1], end_place=afternoon[0], place_list=eating_list)  # type: ignore
            )
        if schedule.dinner:
            dinner = PlaceInfo.model_validate(
                random_eating_place_list(start_place=afternoon[-1], end_place=None, place_list=eating_list)  # type: ignore
            )
    schedule = ScheduleInfo(breakfast=breakfast, morning=morning, lunch=lunch, afternoon=afternoon, dinner=dinner)  # type: ignore
    return schedule  # type: ignore
