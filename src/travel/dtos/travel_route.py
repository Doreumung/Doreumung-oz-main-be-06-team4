from pydantic import BaseModel

from src.travel.dtos.base_travel_route import ScheduleInfo, TravelRouteConfig


class GenerateTravelRouteRequest(BaseModel):
    config: TravelRouteConfig


class GenerateTravelRouteResponse(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class ReGenerateTravelRouteRequest(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class ReGenerateTravelRouteResponse(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class SaveTravelRouteRequest(BaseModel):
    title: str
    schedule: ScheduleInfo
    config: TravelRouteConfig


class SaveTravelRouteResponse(BaseModel):
    travel_route_id: int


class GetTravelRouteOneResponse(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class GetTravelRouteListResponse(BaseModel):
    travelroute_id: int
    user_id: str
    title: str
    schedule: ScheduleInfo
    config: TravelRouteConfig
