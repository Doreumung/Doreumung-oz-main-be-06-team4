from pydantic import BaseModel

from src.travel.models.enums import RegionEnum, ThemeEnum


class Schedule(BaseModel):
    breakfast: bool
    morning: int
    lunch: bool
    afternoon: int
    dinner: bool


class PlaceInfo(BaseModel):
    place_id: int
    name: str
    latitude: float
    longitude: float


class ScheduleInfo(BaseModel):
    breakfast: PlaceInfo | None = None
    morning: PlaceInfo | None = None
    lunch: PlaceInfo | None = None
    afternoon: PlaceInfo | None = None
    dinner: PlaceInfo | None = None


class TravelRouteConfig(BaseModel):
    regions: list[RegionEnum]
    themes: list[ThemeEnum]
    schedule: Schedule
