from fastapi import APIRouter, Depends, HTTPException

from src import TravelRoute, TravelRoutePlace  # type: ignore
from src.config.database.connection_async import get_async_session
from src.travel.dtos.base_travel_route import (
    PlaceInfo,
    Schedule,
    ScheduleInfo,
    TravelRouteConfig,
)
from src.travel.dtos.travel_route import (
    GenerateTravelRouteRequest,
    GenerateTravelRouteResponse,
    GetTravelRouteListPaginationResponse,
    GetTravelRouteListResponse,
    GetTravelRouteOneResponse,
    ReGenerateTravelRouteRequest,
    ReGenerateTravelRouteResponse,
    SaveTravelRouteRequest,
    SaveTravelRouteResponse,
)
from src.travel.models.place import Place
from src.travel.repo.place_repo import PlaceRepository
from src.travel.repo.travel_route_place_repo import TravelRoutePlaceRepository
from src.travel.repo.travel_route_repo import TravelRouteRepository
from src.travel.services.generate_place_list import (
    complete_place_list,
    re_complete_place_list,
)
from src.user.services.authentication import authenticate

router = APIRouter(prefix="/api/v1/travelroute", tags=["Travel"])


# @router.get("/init")
# async def save_init(place_repo: PlaceRepository = Depends()) -> dict[str, str]:
#     place_list = []
#     place_list.append(Place(name="군산오름", theme="자연", region="안덕면", latitude=33.253217, longitude=126.370693))
#     place_list.append(
#         Place(name="서귀포 자연휴양림", theme="자연", region="서귀포시", latitude=33.311453, longitude=126.458861)
#     )
#     place_list.append(
#         Place(name="제주카트클럽", theme="액티비티", region="한림읍", latitude=33.347790, longitude=126.255974)
#     )
#     # 제주카트클럽 근처 식당(3km이내)
#     place_list.append(
#         Place(name="저지신토불이식당", theme="식당", region="한경면", latitude=33.342593, longitude=126.255824)
#     )
#     place_list.append(
#         Place(name="더애월 저지점", theme="식당", region="한경면", latitude=33.337698, longitude=126.266830)
#     )
#     # 서귀포 자연휴양림 근처 식당(3km이내)
#     place_list.append(
#         Place(name="엘에이치큐프로", theme="식당", region="서귀포시", latitude=33.306827, longitude=126.432709)
#     )
#     place_list.append(Place(name="엘에이", theme="식당", region="서귀포시", latitude=33.308827, longitude=126.432709))
#     place_list.append(Place(name="큐프로", theme="식당", region="서귀포시", latitude=33.310827, longitude=126.432709))
#     # 군산오름 근처 식당(3km이내)
#     place_list.append(Place(name="민영식당", theme="식당", region="서귀포시", latitude=33.246113, longitude=126.388198))
#     place_list.append(
#         Place(name="색달식당 중문본점", theme="식당", region="서귀포시", latitude=33.241829, longitude=126.386383)
#     )
#     await place_repo.save_bulk(place_list)
#     return {"massage": "ddd"}


@router.post("", response_model=GenerateTravelRouteResponse)
async def generator_travel_route(data: GenerateTravelRouteRequest) -> GenerateTravelRouteResponse:
    # 전역변수로 미리 로드
    all_place_list = None
    async for session in get_async_session():
        place_repository_in = PlaceRepository(session)
        all_place_list = await place_repository_in.get_place_list()
    all_eating_place_list = []
    if all_place_list:
        for place in all_place_list:
            if place.theme == "식당":
                all_place_list.remove(place)
                all_eating_place_list.append(place)
    config = data.config
    schedule = complete_place_list(
        all_eating_place_list=all_eating_place_list,
        all_place_list=all_place_list,  # type: ignore
        regions=config.regions,
        themes=config.themes,
        schedule=config.schedule,
    )
    return GenerateTravelRouteResponse(config=config, schedule=schedule)


@router.patch("", response_model=ReGenerateTravelRouteResponse)
async def re_generator_travel_route(
    data: ReGenerateTravelRouteRequest, place_repo: PlaceRepository = Depends()
) -> ReGenerateTravelRouteResponse:
    # 전역변수로 미리 로드
    all_place_list = None
    async for session in get_async_session():
        place_repository_in = PlaceRepository(session)
        all_place_list = await place_repository_in.get_place_list()
    all_eating_place_list = []
    if all_place_list:
        for place in all_place_list:
            if place.theme == "식당":
                all_place_list.remove(place)
                all_eating_place_list.append(place)
    config = data.config
    schedule_info = data.schedule
    pined_place_list = []
    for i in ["breakfast", "morning", "lunch", "afternoon", "dinner"]:
        if i in ["breakfast", "lunch", "dinner"]:
            if getattr(schedule_info, i):
                pined_place_list.append(await place_repo.get_by_id(getattr(schedule_info, i).place_id))
        else:
            if getattr(schedule_info, i):
                for place_info in getattr(schedule_info, i):
                    pined_place_list.append(await place_repo.get_by_id(place_info.place_id))
    schedule = re_complete_place_list(
        all_eating_place_list=all_eating_place_list,
        all_place_list=all_place_list,  # type:ignore
        regions=config.regions,
        themes=config.themes,
        schedule=config.schedule,
        pined_place_list=pined_place_list,
    )
    return ReGenerateTravelRouteResponse(config=config, schedule=schedule)


@router.post("/save", response_model=SaveTravelRouteResponse)
async def save_travel_route(
    data: SaveTravelRouteRequest,
    user_id: str = Depends(authenticate),
    travel_route_repo: TravelRouteRepository = Depends(),
    travel_route_place_repo: TravelRoutePlaceRepository = Depends(),
) -> SaveTravelRouteResponse:
    travel_route = TravelRoute(
        user_id=user_id,
        title=data.title,
        regions=data.config.regions,
        themes=data.config.themes,
        breakfast=data.config.schedule.breakfast,
        morning=data.config.schedule.morning,
        lunch=data.config.schedule.lunch,
        afternoon=data.config.schedule.afternoon,
        dinner=data.config.schedule.dinner,
    )
    travel_route = await travel_route_repo.save(travel_route)
    index = 1
    for i in ["breakfast", "morning", "lunch", "afternoon", "dinner"]:
        if i in ["breakfast", "lunch", "dinner"]:
            place_info = getattr(data.schedule, i)
            if place_info:
                travel_route1 = TravelRoutePlace(
                    travel_route_id=travel_route.id, place_id=place_info.place_id, priority=index
                )
                await travel_route_place_repo.save(travel_route1)
                index += 1
        else:
            place_infos = getattr(data.schedule, i)
            if place_infos:
                for place_info in place_infos:
                    travel_route2 = TravelRoutePlace(
                        travel_route_id=travel_route.id, place_id=place_info.place_id, priority=index
                    )
                    await travel_route_place_repo.save(travel_route2)
                    index += 1

    return SaveTravelRouteResponse(travel_route_id=travel_route.id)  # type: ignore


async def generate_dto(travel_route: TravelRoute, user_id: str) -> GetTravelRouteListResponse:
    trps = travel_route.travel_route_places
    place_info_list = [(PlaceInfo.model_validate(trp.place), trp.priority) for trp in trps]
    place_info_list.sort(key=lambda x: x[1])
    route = []
    for i in place_info_list:
        route.append(i[0].name)
    breakfast = None
    morning = None
    lunch = None
    afternoon = None
    dinner = None
    index = 0

    if travel_route.breakfast:
        breakfast = place_info_list[index][0]
        index += 1
    if travel_route.morning:
        morning = [i[0] for i in place_info_list[index : index + travel_route.morning]]
        index += travel_route.morning
    if travel_route.lunch:
        lunch = place_info_list[index][0]
        index += 1
    if travel_route.afternoon:
        afternoon = [i[0] for i in place_info_list[index : index + travel_route.afternoon]]
        index += travel_route.afternoon
    if travel_route.dinner:
        dinner = place_info_list[index][0]
        index += 1

    schedule_info = ScheduleInfo(breakfast=breakfast, morning=morning, lunch=lunch, afternoon=afternoon, dinner=dinner)
    schedule = Schedule(
        breakfast=travel_route.breakfast,
        morning=travel_route.morning,
        lunch=travel_route.lunch,
        afternoon=travel_route.afternoon,
        dinner=travel_route.dinner,
    )
    config = TravelRouteConfig(regions=travel_route.regions, themes=travel_route.themes, schedule=schedule)
    review_id = [i.id for i in travel_route.reviews]
    return GetTravelRouteListResponse(
        travel_route=route, travel_route_id=travel_route.id, user_id=user_id, review_id=review_id, title=travel_route.title, schedule=schedule_info, config=config  # type: ignore
    )


@router.get("", response_model=GetTravelRouteListPaginationResponse)
async def get_travel_routes(
    page: int, size: int, user_id: str = Depends(authenticate), travel_route_repo: TravelRouteRepository = Depends()
) -> GetTravelRouteListPaginationResponse:
    travel_route_list = await travel_route_repo.get_tarvel_route_list_by_user(user_id)
    response_list = []
    for travel_route in travel_route_list:
        response_list.append(await generate_dto(travel_route=travel_route, user_id=user_id))
    total_travelroutes = len(response_list)
    total_pages = (total_travelroutes - 1) // size + 1
    response_list = response_list[size * (page - 1) : size * page]  # 나중에 query시 LIMIT 적용으로 바꾸기
    return GetTravelRouteListPaginationResponse(
        page=page, size=size, total_pages=total_pages, total_travel_routes=total_travelroutes, travel_list=response_list
    )


@router.get("/{id}", response_model=GetTravelRouteListResponse)
async def get_one_travel_route(
    id: int, user_id: str = Depends(authenticate), travel_route_repo: TravelRouteRepository = Depends()
) -> GetTravelRouteListResponse:
    travel_route = await travel_route_repo.get_by_id(id)
    return await generate_dto(travel_route=travel_route, user_id=travel_route.user_id)  # type: ignore


@router.delete("/{id}", status_code=204)
async def delete_one_travel_route(
    id: int, user_id: str = Depends(authenticate), travel_route_repo: TravelRouteRepository = Depends()
) -> None:
    if not await travel_route_repo.delete(id):
        raise HTTPException(status_code=404, detail="Item not found")
