from pydantic import BaseModel

from src.travel.models.place import Place


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
    regions: list[Place.RegionEnum]
    themes: list[Place.ThemeEnum]
    schedule: Schedule
