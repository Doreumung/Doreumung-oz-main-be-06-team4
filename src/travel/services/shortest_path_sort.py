from math import atan2, cos, radians, sin, sqrt

from src import Place  # type: ignore


# 위도경도로 실제 지구상의 거리를 구하는 공식(지구는 둥글다!)
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371  # 지구 반지름 (km)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


# 거리 행렬 생성
def create_distance_matrix(place_list: list[Place]) -> list[list[float]]:
    n = len(place_list)
    distance_matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if place_list[i] != place_list[j]:
                distance_matrix[i][j] = haversine(  # type: ignore
                    place_list[i].latitude, place_list[i].longitude, place_list[j].latitude, place_list[j].longitude
                )

    return distance_matrix  # type: ignore


from itertools import permutations


def solve_tsp_brute_force(distance_matrix: list[list[float]]) -> tuple[list[int], float]:
    num_nodes = len(distance_matrix)
    nodes = list(range(num_nodes))  # 노드 인덱스 생성 (0, 1, 2, ..., n-1)

    # 최적 경로와 최소 거리 초기화
    best_route = None
    best_distance = float("inf")

    # 모든 가능한 순열 생성
    for perm in permutations(nodes):  # 모든 노드 순열을 생성
        route = list(perm)  # 현재 순열을 경로로 사용
        total_distance = 0

        # 현재 경로의 총 거리를 계산
        for i in range(len(route) - 1):
            total_distance += distance_matrix[route[i]][route[i + 1]]  # type: ignore

        # 최적 경로와 최소 거리 업데이트
        if total_distance < best_distance:
            best_distance = total_distance
            best_route = route

    return best_route, best_distance  # type: ignore


# # 예시 거리 행렬
# distance_matrix = [
#     [0, 10, 15, 20],
#     [10, 0, 35, 25],
#     [15, 35, 0, 30],
#     [20, 25, 30, 0]
# ]
#
# # 실행
# route, distance = solve_tsp_all_start_points(distance_matrix)
# print("Best Route:", route)
# print("Best Distance:", distance)


# 최적 경로 계산 및 출력
# route_indices = solve_tsp(distance_matrix)
# route_names = [selected_locations[i] for i in route_indices]
# print("최적 경로:", route_names)
