from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from src.travel.models.enums import RegionEnum, ThemeEnum


class Schedule(BaseModel):
    breakfast: bool
    morning: int
    lunch: bool
    afternoon: int
    dinner: bool


class PlaceInfo(BaseModel):
    place_id: int = Field(validation_alias=AliasChoices("place_id", "id"))
    name: str
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)


class ScheduleInfo(BaseModel):
    breakfast: PlaceInfo | None = None
    morning: list[PlaceInfo] | None = None
    lunch: PlaceInfo | None = None
    afternoon: list[PlaceInfo] | None = None
    dinner: PlaceInfo | None = None


class TravelRouteConfig(BaseModel):
    regions: list[RegionEnum]
    themes: list[ThemeEnum]
    schedule: Schedule
