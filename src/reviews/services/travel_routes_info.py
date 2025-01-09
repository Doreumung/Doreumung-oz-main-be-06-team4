from src import TravelRoute  # type: ignore
from src.travel.dtos.base_travel_route import PlaceInfo, Schedule, ScheduleInfo


async def generate_schedule_info(travel_route: TravelRoute) -> ScheduleInfo:
    trps = travel_route.travel_route_places
    place_info_list = [(PlaceInfo.model_validate(trp.place), trp.priority) for trp in trps]
    place_info_list.sort(key=lambda x: x[1])
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

    return schedule_info
