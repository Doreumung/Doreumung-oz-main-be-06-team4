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
    schedule: ScheduleInfo
    config: TravelRouteConfig


class SaveTravelRouteResponse(BaseModel):
    travel_route_id: int


class GetTravelRouteOneRequest(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class GetTravelRouteOneResponse(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class GetTravelRouteListRequest(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig


class GetTravelRouteListResponse(BaseModel):
    schedule: ScheduleInfo
    config: TravelRouteConfig
